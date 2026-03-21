"""Modbus client for FEMS."""

from __future__ import annotations

import struct
from typing import Any

from pymodbus.client import AsyncModbusTcpClient


class FemsModbusApi:
    """Simple async Modbus TCP client for FEMS."""

    def __init__(self, host: str, port: int, slave: int) -> None:
        self._host = host
        self._port = port
        self._slave = slave
        self._client: AsyncModbusTcpClient | None = None

    async def async_connect(self) -> None:
        """Connect to Modbus device."""
        if self._client is None:
            self._client = AsyncModbusTcpClient(host=self._host, port=self._port)
        await self._client.connect()

    async def async_close(self) -> None:
        """Close Modbus connection."""
        if self._client:
            self._client.close()

    async def async_read_float32_holding(self, address: int) -> float | None:
        """Read a float32 holding register."""
        if self._client is None:
            await self.async_connect()

        assert self._client is not None
        result = await self._client.read_holding_registers(
            address=address,
            count=2,
            device_id=self._slave,
        )
        if result.isError():
            return None

        registers = result.registers
        if len(registers) != 2:
            return None

        raw = struct.pack(">HH", registers[0], registers[1])
        return struct.unpack(">f", raw)[0]

    async def async_read_many_float32(self, registers: dict[str, int]) -> dict[str, float | None]:
        """Read multiple float32 values."""
        data: dict[str, float | None] = {}
        for key, address in registers.items():
            data[key] = await self.async_read_float32_holding(address)
        return data