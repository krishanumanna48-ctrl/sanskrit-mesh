from sanskrit_mesh.core.compiler import SanskritMeshCompiler, HyperCompiler
from sanskrit_mesh.core import tables


class AsyncStreamingDecoder:
    """Async streaming decoder that buffers incoming compiled chunks at token boundaries."""

    _PIPE = "|"

    def __init__(self, compiler=None, level=None, huffman="fixed", entropy_prune=False):
        if compiler is not None:
            self.compiler = compiler
        elif level is None or level == tables.LEVEL_V1:
            self.compiler = SanskritMeshCompiler()
        else:
            self.compiler = HyperCompiler(level=level, huffman=huffman, entropy_prune=entropy_prune)
        self.level = level
        self._buffer = ""
        self._open_pipes = 0

    async def decode_chunk(self, chunk: str):
        if not chunk:
            return ""
        self._buffer += chunk
        self._open_pipes = self._buffer.count(self._PIPE)
        if self._open_pipes % 2 != 0:
            return ""
        complete = self._buffer
        self._buffer = ""
        if not isinstance(self.compiler, HyperCompiler):
            return self.compiler.decompile_text(complete)
        return self.compiler.decompile_text(complete)

    async def decode_stream(self, async_iterable):
        async for chunk in async_iterable:
            partial = await self.decode_chunk(chunk)
            if partial:
                yield partial
        if self._buffer:
            remaining = await self._flush()
            if remaining:
                yield remaining

    async def _flush(self):
        partial = self._buffer
        self._buffer = ""
        if not partial:
            return ""
        if not isinstance(self.compiler, HyperCompiler):
            return self.compiler.decompile_text(partial)
        return self.compiler.decompile_text(partial)
