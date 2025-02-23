import asyncio

from deepseek_wechat_automation.app.database import session_ctx
from deepseek_wechat_automation.app.logging import Ansi, log
from deepseek_wechat_automation.app.models import UploaderCredential, Uploaders
from deepseek_wechat_automation.app.uploader.offiaccount import OffiAccountUploader
from deepseek_wechat_automation.app.usecases.generator import generate_one


async def main():
    with session_ctx() as session:
        credential = session.get(UploaderCredential, (Uploaders.OFFIACCOUNT, "2762834470@qq.com"))
        log(f"Begin generation with credential: {credential.username}", Ansi.LGREEN)
        result = await generate_one(credential.override_prompt)
        log(f"Enter context with credential: {credential.username}", Ansi.LGREEN)
        uploader = OffiAccountUploader()
        uploader.enter_context(credential)
        session.commit()  # flush override username
        await uploader.insert_result(result, credential.override_author)
        input("Press any key to quit")
        uploader.leave_context(save=False)
        log(f"Finish context with credential: {credential.username}", Ansi.LYELLOW)


if __name__ == "__main__":
    asyncio.run(main())
