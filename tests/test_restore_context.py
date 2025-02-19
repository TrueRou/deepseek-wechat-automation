import asyncio

from deepseek_wechat_automation.app.database import session_ctx
from deepseek_wechat_automation.app.logging import Ansi, log
from deepseek_wechat_automation.app.models import AIGCResult, UploaderCredential, Uploaders
from deepseek_wechat_automation.app.uploader.offiaccount import OffiAccountUploader
from deepseek_wechat_automation.app.usecases.generator import generate_one


async def main():
    with session_ctx() as session:
        credential = session.get(UploaderCredential, (Uploaders.OFFIACCOUNT, "2762834470@qq.com"))
        result = AIGCResult(
            text="你好Context\n<img1>\n这里是正文内容第一行\n第二行\n第三行",
            images={"img1": "https://s2.loli.net/2024/01/26/oxiQPIpVeEm9JGb.webp"},
        )
        log(f"Enter context with credential: {credential.username}", Ansi.LGREEN)
        uploader = OffiAccountUploader()
        uploader.enter_context(credential)
        await uploader.insert_result(result, credential.override_author)
        input("Press any key to quit")
        uploader.leave_context(save=False)
        log(f"Finish context with credential: {credential.username}", Ansi.LYELLOW)


if __name__ == "__main__":
    asyncio.run(main())
