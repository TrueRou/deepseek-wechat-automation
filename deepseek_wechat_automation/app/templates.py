from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI

from deepseek_wechat_automation.app import database
from deepseek_wechat_automation.app.logging import Ansi, log
from deepseek_wechat_automation.app.usecases import scheduler


@asynccontextmanager
async def init_lifespan(asgi_app: FastAPI):
    database.init_db()
    await scheduler.init_sched()
    log("Startup process complete.", Ansi.LGREEN)
    yield  # Above: Startup process Below: Shutdown process
    database.engine.dispose()


def init_api() -> FastAPI:
    """Create & initialize our app."""
    asgi_app = FastAPI(lifespan=init_lifespan)

    return asgi_app


asgi_app = init_api()
