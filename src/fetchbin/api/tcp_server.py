import asyncio
import os

from sqlmodel import Session

from .database import FetchOutput, engine

TCP_HOST = os.environ.get("FETCHBIN_TCP_HOST", "0.0.0.0")
TCP_PORT = int(os.environ.get("FETCHBIN_TCP_PORT", 9999))
BASE_URL = os.environ.get("FETCHBIN_PUBLIC_URL", "http://localhost:8000")


async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    print(f"[TCP] Connection from {addr}")

    try:
        data = await reader.read(1024 * 1024)
        content = data.decode().strip()

        if not content:
            print(f"[TCP] No content received from {addr}. Closing connection.")
            writer.write(b"Error: Content cannot be empty.\n")
            await writer.drain()

            return

        http_methods = ["GET ", "POST ", "PUT ", "DELETE ", "HEAD ", "OPTIONS ", "PATCH "]

        if any(content.startswith(method) for method in http_methods):
            print(f"[TCP] HTTP request from {addr} rejected.")
            error_response = (
                b"HTTP/1.1 400 Bad Request\r\n"
                b"Content-Type: text/plain\r\n"
                b"Connection: close\r\n"
                b"\r\n"
                b"Error: This port is for raw text submissions only (e.g., via netcat).\n"
                b"It does not speak HTTP."
            )
            writer.write(error_response)
            await writer.drain()

            return

        with Session(engine) as session:
            fetch_output = FetchOutput(content=content)
            session.add(fetch_output)
            session.commit()
            session.refresh(fetch_output)
            public_id = fetch_output.public_id
            delete_token = fetch_output.delete_token

        view_url = f"{BASE_URL}/view/{public_id}"
        delete_url = f"{BASE_URL}/delete/{delete_token}"
        response_text = f"Success! Your output has been shared.\nURL: {view_url}\nDelete URL: {delete_url}\n"
        print(f"[TCP] Saved paste from {addr}. URL: {view_url}")
        writer.write(response_text.encode())
        await writer.drain()

    except Exception as e:
        print(f"[TCP] Error handling connection from {addr}: {e}")
        error_message = f"An internal error occurred: {e}\n"
        writer.write(error_message.encode())
        await writer.drain()
    finally:
        print(f"[TCP] Closing connection for {addr}")
        writer.close()
        await writer.wait_closed()


async def serve_tcp():
    server = await asyncio.start_server(handle_connection, TCP_HOST, TCP_PORT)
    addr = server.sockets[0].getsockname()
    print(f"[TCP] Server listening on {addr}")

    async with server:
        await server.serve_forever()
