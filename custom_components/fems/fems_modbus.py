"""Modbus client for FEMS."""

from __future__ import annotations

import struct

from pymodbus.client import AsyncModbusTcpClient


class FemsModbusApi:
    """Simple async Modbus TCP client for FEMS."""

    def __init__(self, host: str, port: int, slave: int) -> None:
        self._host = host
        self._port = port
        self._slave = slave
        self._client: AsyncModbusTcpClient | None = None

    async def async_connect(self) -> None:
        if self._client is None:
            self._client = AsyncModbusTcpClient(host=self._host, port=self._port)
        await self._client.connect()

    async def async_close(self) -> None:
        if self._client:
            self._client.close()

    async def async_read_uint16_input(self, address: int) -> int | None:
        if self._client is None:
            await self.async_connect()

        assert self._client is not None
        result = await self._client.read_input_registers(
            address=address,
            count=1,
            device_id=self._slave,
        )
        if result.isError() or len(result.registers) != 1:
            return None
        return result.registers[0]

    async def async_read_float32_holding(self, address: int) -> float | None:
        if self._client is None:
            await self.async_connect()

        assert self._client is not None
        result = await self._client.read_holding_registers(
            address=address,
            count=2,
            device_id=self._slave,
        )
        if result.isError() or len(result.registers) != 2:
            return None

        raw = struct.pack(">HH", result.registers[0], result.registers[1])
        return struct.unpack(">f", raw)[0]

    async def async_read_float64_holding(self, address: int) -> float | None:
        if self._client is None:
            await self.async_connect()

        assert self._client is not None
        result = await self._client.read_holding_registers(
            address=address,
            count=4,
            device_id=self._slave,
        )
        if result.isError() or len(result.registers) != 4:
            return None

        raw = struct.pack(
            ">HHHH",
            result.registers[0],
            result.registers[1],
            result.registers[2],
            result.registers[3],
        )
        return struct.unpack(">d", raw)[0]

    async def async_read_many_uint16_input(self, registers: dict[str, int]) -> dict[str, int | None]:
        return {key: await self.async_read_uint16_input(address) for key, address in registers.items()}

    async def async_read_many_float32(self, registers: dict[str, int]) -> dict[str, float | None]:
        return {key: await self.async_read_float32_holding(address) for key, address in registers.items()}

    async def async_read_many_float64(self, registers: dict[str, int]) -> dict[str, float | None]:
        return {key: await self.async_read_float64_holding(address) for key, address in registers.items()}
