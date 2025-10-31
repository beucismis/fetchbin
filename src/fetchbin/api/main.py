import asyncio
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from . import api, database, models, pages, tcp_server

tcp_server_task = None


async def startup():
    print("[SYSTEM] Initializing database...")
    database.create_db_and_tables()
    print("[SYSTEM] Database initialized.")
    print("[SYSTEM] Starting TCP server...")
    loop = asyncio.get_event_loop()
    global tcp_server_task
    tcp_server_task = loop.create_task(tcp_server.serve_tcp())
    print("[SYSTEM] TCP server started.")


async def shutdown():
    print("[SYSTEM] Stopping TCP server...")

    if tcp_server_task:
        tcp_server_task.cancel()
        try:
            await tcp_server_task
        except asyncio.CancelledError:
            print("[SYSTEM] TCP server task cancelled.")

    print("[SYSTEM] TCP server stopped.")


app = FastAPI(on_startup=[startup], on_shutdown=[shutdown])
settings = models.Settings()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
app.mount("/static", StaticFiles(directory="src/fetchbin/api/static"), name="static")
