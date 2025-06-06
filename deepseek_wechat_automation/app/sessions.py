import contextlib
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from openai import AsyncOpenAI

from deepseek_wechat_automation.app import settings

scheduler = BackgroundScheduler()
openai_client = AsyncOpenAI(api_key=settings.llm_key, base_url=settings.llm_url)


@contextlib.asynccontextmanager
async def async_httpx_ctx():
    async with httpx.AsyncClient(proxy=settings.proxy_url or None, timeout=120) as session:
        yield session
