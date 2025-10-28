from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from . import routers, models


app = FastAPI()
settings = models.Settings()
app.mount("/static", StaticFiles(directory="src/fetchbin/api/static"), name="static")
app.include_router(routers.api)
templates = Jinja2Templates(directory="src/fetchbin/api/templates")


@app.get("/", response_class=HTMLResponse)
async def home_sweet_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/po-tos", response_class=HTMLResponse)
async def po_tos(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("po-tos.html", {"request": request})


@app.get("/healthcheck", response_class=JSONResponse)
async def healthcheck() -> models.HealthCheck:
    return models.HealthCheck(
        status="healthy",
        timestamp=datetime.now(UTC),
    )
