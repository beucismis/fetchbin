from ansi2html import Ansi2HTMLConverter
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session, select

from . import database, models
from .database import get_db_session

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
ansi_converter = Ansi2HTMLConverter(inline=False)


def get_fetch_output_by_public_id(public_id: str, session: Session = Depends(get_db_session)) -> database.FetchOutput:
    statement = select(database.FetchOutput).where(database.FetchOutput.public_id == public_id)
    db_output = session.exec(statement).first()
    if not db_output:
        raise HTTPException(status_code=404, detail="Output not found")
    return db_output


def _handle_vote(
    db_share: database.FetchOutput,
    request: Request,
    session: Session,
    vote_type: str,
):
    ip_address = request.headers.get("X-Forwarded-For")
    if ip_address:
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.client.host
    vote_statement = select(database.Vote).where(
        database.Vote.share_id == db_share.id,
        database.Vote.ip_address == ip_address,
    )
    existing_vote = session.exec(vote_statement).first()
    if existing_vote:
        raise HTTPException(status_code=409, detail="Already voted")

    if vote_type == "upvote":
        db_share.upvotes += 1
    elif vote_type == "downvote":
        db_share.downvotes += 1

    new_vote = database.Vote(share_id=db_share.id, ip_address=ip_address)
    session.add(new_vote)

    try:
        session.commit()
        session.refresh(db_share)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to record vote")

    return {"upvotes": db_share.upvotes, "downvotes": db_share.downvotes}


@router.post("/share", response_class=JSONResponse)
@limiter.limit("10/minute")
def share_output(request: Request, share_request: models.ShareRequest, session: Session = Depends(get_db_session)):
    if len(share_request.content) > 1024 * 1024:
        raise HTTPException(status_code=413, detail="Content too large")

    db_output = database.FetchOutput(
        content=share_request.content,
        command=share_request.command,
        is_hidden=share_request.is_hidden,
    )
    session.add(db_output)

    try:
        session.commit()
        session.refresh(db_output)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create share")

    base_url = f"{request.url.scheme}://{request.url.netloc}"
    return {
        "url": f"{base_url}/output/{db_output.public_id}",
        "delete_url": f"{base_url}/delete/{db_output.delete_token}",
    }


@router.post("/output/{public_id}/upvote", response_class=JSONResponse)
@limiter.limit("10/minute")
def upvote_output(
    request: Request,
    db_share: database.FetchOutput = Depends(get_fetch_output_by_public_id),
    session: Session = Depends(get_db_session),
):
    return _handle_vote(db_share, request, session, "upvote")


@router.post("/output/{public_id}/downvote", response_class=JSONResponse)
@limiter.limit("10/minute")
def downvote_output(
    request: Request,
    db_share: database.FetchOutput = Depends(get_fetch_output_by_public_id),
    session: Session = Depends(get_db_session),
):
    return _handle_vote(db_share, request, session, "downvote")


@router.get("/output/{public_id}", response_class=JSONResponse)
def get_output(
    db_share: database.FetchOutput = Depends(get_fetch_output_by_public_id),
):
    """Returns the details of a specific output, including raw and HTML content."""
    return {
        "public_id": db_share.public_id,
        "command": db_share.command,
        "created_at": db_share.created_at,
        "upvotes": db_share.upvotes,
        "downvotes": db_share.downvotes,
        "content_raw": db_share.content,
        "content_html": ansi_converter.convert(db_share.content, full=False),
    }


@router.get("/outputs", response_class=JSONResponse)
def get_outputs_list(session: Session = Depends(get_db_session)):
    statement = select(database.FetchOutput).where(database.FetchOutput.is_hidden == False)
    statement = statement.order_by(database.FetchOutput.id.desc())

    outputs_from_db = session.exec(statement).all()
    processed_outputs = [
        {
            "public_id": output.public_id,
            "command": output.command,
            "created_at": output.created_at,
            "upvotes": output.upvotes,
            "downvotes": output.downvotes,
            "content_raw": output.content,
            "content_html": ansi_converter.convert(output.content, full=False),
        }
        for output in outputs_from_db
    ]

    return processed_outputs


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def api_docs():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head><title>FetchBin API</title></head>
        <body>
            <h2>Documentation</h2>
            <h3>Create a Share</h3>
            <p><code>POST /api/share</code></p>
            <p>Creates a new share. Accepts a JSON body with a required "content" field and optional "command" and "is_hidden" fields.</p>
        <p><b>Example Body:</b></p>
        <pre><code>{
  "content": "your text output here",
  "command": "your_command (optional)",
  "is_hidden": false (optional)
}</code></pre>
            <h3>Get All Outputs</h3>
                    <p><code>GET /api/outputs</code></p>
                    <p>Returns a JSON list of all non-hidden shares with their full content.</p>            <h3>Get a Single Output</h3>
            <p><code>GET /api/output/{public_id}</code></p>
            <p>Returns all details for a single share, including raw and HTML content.</p>
            <h3>Vote on an Output</h3>
            <p><code>POST /api/output/{public_id}/upvote</code></p>
            <p><code>POST /api/output/{public_id}/downvote</code></p>
            <p>Upvotes or downvotes a share. No request body is needed.</p>
            </body>
    </html>
    """

    return HTMLResponse(content=html_content)
