import asyncio
from http import HTTPStatus

from src.logger import log


async def handle_request(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    await reader.readline()
    response = (
        f"HTTP/1.1 {HTTPStatus.OK} OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 2\r\n"
        "\r\n"
        "OK"
    )
    writer.write(response.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def start_server(port: int = 8080) -> None:
    server = await asyncio.start_server(handle_request, "0.0.0.0", port)
    log("info", f"Health server running on port {port}")
    async with server:
        await server.serve_forever()
