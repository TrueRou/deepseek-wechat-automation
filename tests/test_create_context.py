from deepseek_wechat_automation.app.uploader.offiaccount import OffiAccountUploader


uploader = OffiAccountUploader()
uploader.create_driver()
uploader.create_context("2762834470@qq.com", "qwer2022")
input("Press any key to quit")
uploader.drop_driver()
