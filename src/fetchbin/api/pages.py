import re
from datetime import datetime, timedelta, timezone

from ansi2html import Ansi2HTMLConverter
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, func, select

from .. import __about__
from . import database, models
from .database import get_db_session

router = APIRouter()
router.mount("/static", StaticFiles(directory="src/fetchbin/api/static"), name="static")

settings = models.Settings()
templates = Jinja2Templates(directory="src/fetchbin/api/templates")
ansi_converter = Ansi2HTMLConverter(inline=False)
ansi_escape_pattern = re.compile(r"\x1b\[[0-9;]*[A-HJKST]")


def get_fetch_output_by_public_id(public_id: str, session: Session = Depends(get_db_session)) -> database.FetchOutput:
    statement = select(database.FetchOutput).where(database.FetchOutput.public_id == public_id)
    db_output = session.exec(statement).first()

    if not db_output:
        raise HTTPException(status_code=404, detail="Output not found")

    return db_output


def get_fetch_output_by_delete_token(
    delete_token: str, session: Session = Depends(get_db_session)
) -> database.FetchOutput:
    statement = select(database.FetchOutput).where(database.FetchOutput.delete_token == delete_token)
    db_output = session.exec(statement).first()

    if not db_output:
        raise HTTPException(status_code=404, detail="Share not found")

    return db_output


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_db_session)):
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    statement = select(func.count(database.FetchOutput.id)).where(database.FetchOutput.created_at > one_hour_ago)
    shares_last_hour = session.exec(statement).one()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "shares_last_hour": shares_last_hour,
        },
    )


@router.get("/outputs", response_class=HTMLResponse)
def view_outputs_list(request: Request, sort_by: str = "newest", session: Session = Depends(get_db_session)):
    statement = select(database.FetchOutput).where(database.FetchOutput.is_hidden == False)

    if sort_by == "upvotes":
        statement = statement.order_by(database.FetchOutput.upvotes.desc())
    elif sort_by == "downvotes":
        statement = statement.order_by(database.FetchOutput.downvotes.desc())
    elif sort_by == "score":
        statement = statement.order_by((database.FetchOutput.upvotes - database.FetchOutput.downvotes).desc())
    else:
        statement = statement.order_by(database.FetchOutput.id.desc())

    outputs_from_db = session.exec(statement.limit(100)).all()
    processed_outputs = []

    for output in outputs_from_db:
        processed_outputs.append(
            {
                "public_id": output.public_id,
                "command": output.command,
                "html_content": ansi_converter.convert(output.content, full=False),
                "created_at": output.created_at.replace(tzinfo=timezone.utc).isoformat(),
                "upvotes": output.upvotes,
                "downvotes": output.downvotes,
            }
        )

    return templates.TemplateResponse(
        "outputs.html",
        {"request": request, "outputs": processed_outputs, "sort_by": sort_by},
    )


@router.get("/raw/{public_id}", response_class=PlainTextResponse)
def view_raw_output(
    db_output: database.FetchOutput = Depends(get_fetch_output_by_public_id),
):
    return PlainTextResponse(content=db_output.content)


@router.get("/output/{public_id}", response_class=HTMLResponse)
def view_output(request: Request, db_output: database.FetchOutput = Depends(get_fetch_output_by_public_id)):
    raw_ansi_text = db_output.content
    processed_ansi_text = ansi_escape_pattern.sub("", raw_ansi_text)
    html_content = ansi_converter.convert(processed_ansi_text, full=False)

    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "html_content": html_content,
            "public_id": db_output.public_id,
            "delete_token": db_output.delete_token,
            "created_at": db_output.created_at.replace(tzinfo=timezone.utc).isoformat(),
            "command": db_output.command,
            "upvotes": db_output.upvotes,
            "downvotes": db_output.downvotes,
        },
    )


@router.get("/delete/{delete_token}", response_class=HTMLResponse)
def delete_page(request: Request, db_output: database.FetchOutput = Depends(get_fetch_output_by_delete_token)):
    return templates.TemplateResponse(
        "delete.html",
        {"request": request, "public_id": db_output.public_id},
    )


@router.post("/delete/{delete_token}", response_class=HTMLResponse)
def delete_output(
    request: Request,
    db_output: database.FetchOutput = Depends(get_fetch_output_by_delete_token),
    session: Session = Depends(get_db_session),
):
    session.delete(db_output)
    session.commit()

    return templates.TemplateResponse("deleted.html", {"request": request})


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/po-tos", response_class=HTMLResponse)
async def po_tos(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("po-tos.html", {"request": request})


@router.get("/healthcheck", response_class=JSONResponse)
async def healthcheck() -> models.HealthCheck:
    return models.HealthCheck(
        status="healthy",
        version=__about__.__version__,
        timestamp=datetime.now(timezone.utc),
    )
