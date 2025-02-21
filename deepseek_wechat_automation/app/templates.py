from __future__ import annotations
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from fastapi import Depends, FastAPI, Form, Request
from fastapi.templating import Jinja2Templates

from deepseek_wechat_automation.app import database
from deepseek_wechat_automation.app.logging import Ansi, log
from deepseek_wechat_automation.app.models import UploaderCredential, Uploaders
from deepseek_wechat_automation.app.uploader.offiaccount import OffiAccountUploader
from deepseek_wechat_automation.app.usecases import scheduler
from deepseek_wechat_automation.app.database import require_session, session_ctx


@asynccontextmanager
async def init_lifespan(asgi_app: FastAPI):
    database.init_db()
    await scheduler.init_sched()
    log("Startup process complete.", Ansi.LGREEN)
    yield  # Above: Startup process Below: Shutdown process
    database.engine.dispose()


templates = Jinja2Templates(directory="templates")
asgi_app = FastAPI(lifespan=init_lifespan)
executor = ThreadPoolExecutor(10)
database.register_middleware(asgi_app)


def require_credential(
    uploader: Uploaders = Form(...),
    username: str = Form(...),
    session: Session = Depends(require_session),
) -> UploaderCredential:
    return session.get(UploaderCredential, (uploader, username))


@asgi_app.get("/")
async def index(request: Request):
    with session_ctx() as session:
        accounts = list(session.exec(select(UploaderCredential)).all())
    return templates.TemplateResponse("index.html", {"request": request, "accounts": accounts})


@asgi_app.post("/accounts/new")
async def new_account(username: str = Form(...), password: str = Form(...)):
    def create_account():
        try:
            OffiAccountUploader().create_context(username, password)
        except Exception as e:
            log(f"Failed to create account: {str(e)[:64]}", Ansi.LRED)

    asyncio.get_event_loop().run_in_executor(executor, create_account)
    return RedirectResponse(url="/", status_code=303)


@asgi_app.post("/accounts/delete")
async def delete_account(credential: UploaderCredential = Depends(require_credential), session: Session = Depends(require_session)):
    session.delete(credential)
    session.commit()
    return RedirectResponse(url="/", status_code=303)


@asgi_app.post("/accounts/renew")
async def renew_account(credential: UploaderCredential = Depends(require_credential)):
    def renew_account():
        try:
            OffiAccountUploader().create_context(credential.username, credential.password)
        except Exception as e:
            log(f"Failed to renew account: {repr(e)[:64]}", Ansi.LRED)

    asyncio.get_event_loop().run_in_executor(executor, renew_account)
    return RedirectResponse(url="/", status_code=303)


@asgi_app.post("/accounts/view")
async def view_account(credential: UploaderCredential = Depends(require_credential)):
    def view_account():
        with session_ctx() as session:
            cred_ctx = session.get(UploaderCredential, (credential.uploader, credential.username))
            if not OffiAccountUploader().enter_context(cred_ctx, view_only=True):
                cred_ctx.is_expired = True
                session.commit()
                log(f"Failed to view account, expired it: {credential.username}", Ansi.LRED)

    asyncio.get_event_loop().run_in_executor(executor, view_account)
    return RedirectResponse(url="/", status_code=303)


@asgi_app.post("/accounts/test")
async def trigger_post(credential: UploaderCredential = Depends(require_credential)):
    def test_account():
        with session_ctx() as session:
            cred_ctx = session.get(UploaderCredential, (credential.uploader, credential.username))
            scheduler.create_new_article(cred_ctx, session, save=False)

    asyncio.get_event_loop().run_in_executor(executor, test_account)
    return RedirectResponse(url="/", status_code=303)
