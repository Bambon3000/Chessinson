import asyncio
from functools import partial
from Lights import Light


class AsyncLight:
    def __init__(self, light: Light, loop: asyncio.AbstractEventLoop):
        self.light = light
        self.loop = loop

    async def _run(self, fn, *args):
        await self.loop.run_in_executor(None, partial(fn, *args))

    async def off(self):
        await self._run(self.light.off)

    async def ready(self):
        await self._run(self.light.ready)

    async def move(self):
        await self._run(self.light.move)

    async def illegal(self):
        await self._run(self.light.illegal)

    async def unknown(self):
        await self._run(self.light.unknown)

    async def close(self):
        await self._run(self.light.close)

