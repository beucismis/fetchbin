from sqlmodel import Session, select
from ansi2html import Ansi2HTMLConverter
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

from . import models, database


api = APIRouter()
settings = models.Settings()
templates = Jinja2Templates(directory="src/fetchbin/api/templates")
ansi_converter = Ansi2HTMLConverter()


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

        return {"url": f"http://127.0.0.1:8000/c/{db_output.public_id}"}


@api.get("/c/{public_id}", response_class=HTMLResponse)
def view_output(request: Request, public_id: str):
    with Session(database.engine) as session:
        statement = select(database.FetchOutput).where(database.FetchOutput.public_id == public_id)
        db_output = session.exec(statement).first()

        if not db_output:
            raise HTTPException(status_code=404, detail="Çıktı bulunamadı")

        raw_ansi_text = db_output.content
        html_content = ansi_converter.convert(raw_ansi_text)

        return templates.TemplateResponse(
            "view.html",
            {"request": request, "html_content": html_content, "public_id": public_id},
        )


@api.get("/", response_class=HTMLResponse)
def view_all_outputs(request: Request):
    with Session(database.engine) as session:
        statement = select(database.FetchOutput).order_by(database.FetchOutput.id.desc()).limit(50)
        outputs = session.exec(statement).all()

        return templates.TemplateResponse("index.html", {"request": request, "outputs": outputs})
