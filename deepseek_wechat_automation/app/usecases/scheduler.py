import asyncio
from deepseek_wechat_automation.app.logging import log
from deepseek_wechat_automation.app.models import UploaderCredential
from deepseek_wechat_automation.app.sessions import scheduler
from deepseek_wechat_automation.app.settings import scheduler_cron
from apscheduler.triggers.cron import CronTrigger

from deepseek_wechat_automation.app.uploader.offiaccount import OffiAccountUploader
from deepseek_wechat_automation.app.usecases.generator import generate_one


async def init_sched():
    scheduler.add_job(func=new_post_sched, trigger=CronTrigger.from_crontab(scheduler_cron))


def new_post_sched():
    pass


def new_post(credential: UploaderCredential):
    result = asyncio.run(generate_one())
    uploader = OffiAccountUploader()
    log(f"Enter context with credential: {credential.username}")
    uploader.enter_context(credential)
    uploader.insert_text(result.text)
    while True:
        pass
