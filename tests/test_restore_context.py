from deepseek_wechat_automation.app.database import session_ctx
from deepseek_wechat_automation.app.models import UploaderCredential, Uploaders
from deepseek_wechat_automation.app.uploader.offiaccount import OffiAccountUploader


uploader = OffiAccountUploader()
with session_ctx() as session:
    model = session.get(UploaderCredential, (Uploaders.OFFIACCOUNT, "2762834470@qq.com"))
    uploader.enter_context(model)
    uploader.set_title("Hello, world!")
    uploader.set_author("Author")
    uploader.insert_text("This is a test.")
    while True:
        pass
