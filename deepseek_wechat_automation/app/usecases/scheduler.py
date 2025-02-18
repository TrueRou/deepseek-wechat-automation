import asyncio
from datetime import datetime
from sqlmodel import select
from apscheduler.triggers.cron import CronTrigger

from deepseek_wechat_automation.app.database import session_ctx
from deepseek_wechat_automation.app.logging import Ansi, log
from deepseek_wechat_automation.app.models import UploaderCredential
from deepseek_wechat_automation.app.sessions import scheduler
from deepseek_wechat_automation.app.settings import scheduler_cron
from deepseek_wechat_automation.app.uploader.offiaccount import OffiAccountUploader
from deepseek_wechat_automation.app.usecases.generator import generate_one


async def init_sched():
    scheduler.add_job(func=create_new_article_sched, trigger=CronTrigger.from_crontab(scheduler_cron))


def create_new_article_sched():
    with session_ctx() as session:
        stmt = select(UploaderCredential).order_by(UploaderCredential.updated_at).where(UploaderCredential.is_expired == False)
        if credentials := session.exec(stmt).one_or_none():
            credentials.updated_at = datetime.utcnow()
            create_new_article(credentials)
            session.commit()
        else:
            log("No account available now. Skipping...", Ansi.LYELLOW)


def create_new_article(credential: UploaderCredential):
    log(f"Begin generation with credential: {credential.username}", Ansi.LGREEN)
    result = asyncio.run(generate_one(credential.override_prompt))
    log(f"Enter context with credential: {credential.username}", Ansi.LGREEN)
    uploader = OffiAccountUploader()
    if uploader.enter_context(credential):
        asyncio.run(uploader.insert_result(result))
        log(f"Finish context with credential: {credential.username}", Ansi.LYELLOW)
        uploader.leave_context(credential, save=True)
    else:
        log(f"Failed to enter context with credential, expired it: {credential.username}", Ansi.LYELLOW)
        credential.is_expired = True
        uploader.leave_context(credential, save=False)
