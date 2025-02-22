import asyncio
from datetime import datetime
from sqlmodel import Session, select
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
    log(f"Scheduler initialized: {scheduler_cron}", Ansi.LBLUE)
    scheduler.start()


def create_new_article_sched():
    with session_ctx() as session:
        stmt = select(UploaderCredential).order_by(UploaderCredential.updated_at).where(UploaderCredential.is_expired == False)
        credentials = session.exec(stmt).all()  # 获取所有未过期的凭证
        
        if not credentials:
            log("No accounts available now. Skipping...", Ansi.LYELLOW)
            return
            
        log(f"Found {len(credentials)} accounts to process", Ansi.LBLUE)
        current_time = datetime.utcnow()
        
        for credential in credentials:
            try:
                log(f"Processing account: {credential.username}", Ansi.LGREEN)
                credential.updated_at = current_time  # 更新时间戳
                create_new_article(credential, session)
            except Exception as e:
                log(f"Error processing account {credential.username}: {str(e)}", Ansi.LRED)
                continue  # 继续处理下一个账号
        
        session.commit()  # 统一提交所有更改



def create_new_article(credential: UploaderCredential, session: Session, save: bool = True):
    log(f"Begin generation with credential: {credential.username}", Ansi.LGREEN)
    try:
        result = asyncio.run(generate_one(credential.override_prompt))
    except Exception as e:
        log(f"Failed to generate article. Skipping...", Ansi.LRED)
        return
    log(f"Enter context with credential: {credential.username}", Ansi.LGREEN)
    uploader = OffiAccountUploader()
    if uploader.enter_context(credential):
        asyncio.run(uploader.insert_result(result, credential.override_author))
        log(f"Finish context with credential: {credential.username}", Ansi.LYELLOW)
        uploader.leave_context(save=save)
    else:
        log(f"Failed to enter context with credential, expired it: {credential.username}", Ansi.LYELLOW)
        credential.is_expired = True
        uploader.leave_context(save=False)
    session.commit()
