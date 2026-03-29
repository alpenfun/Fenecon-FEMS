"""Modbus client for fems-diagnostics"""

from __future__ import annotations

import asyncio
import logging
import struct
from typing import Any

from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)


class FemsModbusApi:
    """Async Modbus TCP client for FEMS."""

    def __init__(self, host: str, port: int, slave: int) -> None:
        self._host = host
        self._port = port
        self._slave = slave
        self._client: AsyncModbusTcpClient | None = None

    async def async_connect(self) -> None:
        """Ensure connection to Modbus device."""
        if self._client is None:
            self._client = AsyncModbusTcpClient(host=self._host, port=self._port)

        if not self._client.connected:
            await self._client.connect()

    async def async_close(self) -> None:
        """Close Modbus connection."""
        if self._client and self._client.connected:
            self._client.close()

    async def _async_safe_read(self, coro) -> Any | None:
        """Execute Modbus read safely."""
        try:
            return await coro
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Modbus read failed: %s", err)
            return None

    async def async_read_uint16_input(self, address: int) -> int | None:
        """Read single uint16 input register."""
        await self.async_connect()

        if self._client is None:
            return None

        result = await self._async_safe_read(
            self._client.read_input_registers(
                address=address,
                count=1,
                device_id=self._slave,
            )
        )

        if not result or result.isError() or len(result.registers) != 1:
            return None

        return result.registers[0]

    async def async_read_float32_holding(self, address: int) -> float | None:
        """Read float32 holding register."""
        await self.async_connect()

        if self._client is None:
            return None

        result = await self._async_safe_read(
            self._client.read_holding_registers(
                address=address,
                count=2,
                device_id=self._slave,
            )
        )

        if not result or result.isError() or len(result.registers) != 2:
            return None

        raw = struct.pack(">HH", result.registers[0], result.registers[1])
        return struct.unpack(">f", raw)[0]

    async def async_read_float64_holding(self, address: int) -> float | None:
        """Read float64 holding register."""
        await self.async_connect()

        if self._client is None:
            return None

        result = await self._async_safe_read(
            self._client.read_holding_registers(
                address=address,
                count=4,
                device_id=self._slave,
            )
        )

        if not result or result.isError() or len(result.registers) != 4:
            return None

        raw = struct.pack(
            ">HHHH",
            result.registers[0],
            result.registers[1],
            result.registers[2],
            result.registers[3],
        )
        return struct.unpack(">d", raw)[0]

    async def async_read_many_uint16_input(
        self, registers: dict[str, int]
    ) -> dict[str, int | None]:
        """Read multiple uint16 input registers in parallel."""
        tasks = [
            self.async_read_uint16_input(address)
            for address in registers.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            key: (None if isinstance(value, Exception) else value)
            for key, value in zip(registers.keys(), results)
        }

    async def async_read_many_float32(
        self, registers: dict[str, int]
    ) -> dict[str, float | None]:
        """Read multiple float32 registers in parallel."""
        tasks = [
            self.async_read_float32_holding(address)
            for address in registers.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            key: (None if isinstance(value, Exception) else value)
            for key, value in zip(registers.keys(), results)
        }

    async def async_read_many_float64(
        self, registers: dict[str, int]
    ) -> dict[str, float | None]:
        """Read multiple float64 registers in parallel."""
        tasks = [
            self.async_read_float64_holding(address)
            for address in registers.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            key: (None if isinstance(value, Exception) else value)
            for key, value in zip(registers.keys(), results)
        }
