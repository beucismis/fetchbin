import re
from datetime import datetime

from sqlmodel import Session, select
from ansi2html import Ansi2HTMLConverter
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse

from . import models, database


api = APIRouter()
settings = models.Settings()
templates = Jinja2Templates(directory="src/fetchbin/api/templates")
ansi_converter = Ansi2HTMLConverter(inline=False)


@api.on_event("startup")
def on_startup():
    database.create_db_and_tables()


@api.post("/api/share", response_class=JSONResponse)
def share_output(request: models.ShareRequest):
    with Session(database.engine) as session:
        db_output = database.FetchOutput(content=request.content)
        session.add(db_output)
        session.commit()
        session.refresh(db_output)

        return {
            "url": f"http://127.0.0.1:8000/c/{db_output.public_id}",
            "delete_url": f"http://127.0.0.1:8000/delete/{db_output.delete_token}",
        }


@api.get("/c/{public_id}", response_class=HTMLResponse)
def view_output(request: Request, public_id: str):
    with Session(database.engine) as session:
        statement = select(database.FetchOutput).where(database.FetchOutput.public_id == public_id)
        db_output = session.exec(statement).first()

        if not db_output:
            raise HTTPException(status_code=404, detail="Çıktı bulunamadı")

        raw_ansi_text = db_output.content
        ansi_escape_pattern = re.compile(r"\x1b\[[0-9;]*[A-HJKST]")
        processed_ansi_text = ansi_escape_pattern.sub("", raw_ansi_text)
        html_content = ansi_converter.convert(processed_ansi_text, full=False)

        return templates.TemplateResponse(
            "view.html",
            {
                "request": request,
                "html_content": html_content,
                "public_id": public_id,
                "delete_token": db_output.delete_token,
                "created_at": db_output.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
        )


@api.get("/raw/{public_id}", response_class=PlainTextResponse)
def view_raw_output(public_id: str):
    with Session(database.engine) as session:
        statement = select(database.FetchOutput).where(database.FetchOutput.public_id == public_id)
        db_output = session.exec(statement).first()

        if not db_output:
            raise HTTPException(status_code=404, detail="Output not found")

        return PlainTextResponse(content=db_output.content)


@api.get("/", response_class=HTMLResponse)
def view_all_outputs(request: Request):
    with Session(database.engine) as session:
        statement = select(database.FetchOutput).order_by(database.FetchOutput.id.desc()).limit(50)
        outputs = session.exec(statement).all()

        return templates.TemplateResponse("index.html", {"request": request, "outputs": outputs})


@api.get("/delete/{delete_token}", response_class=HTMLResponse)
def delete_page(request: Request, delete_token: str):
    with Session(database.engine) as session:
        statement = select(database.FetchOutput).where(database.FetchOutput.delete_token == delete_token)
        db_output = session.exec(statement).first()

        if not db_output:
            raise HTTPException(status_code=404, detail="Share not found")

        return templates.TemplateResponse(
            "delete.html",
            {"request": request, "public_id": db_output.public_id},
        )


@api.post("/delete/{delete_token}", response_class=HTMLResponse)
def delete_output(request: Request, delete_token: str):
    with Session(database.engine) as session:
        statement = select(database.FetchOutput).where(database.FetchOutput.delete_token == delete_token)
        db_output = session.exec(statement).first()

        if not db_output:
            raise HTTPException(status_code=404, detail="Share not found")

        session.delete(db_output)
        session.commit()

        return templates.TemplateResponse("deleted.html", {"request": request})
