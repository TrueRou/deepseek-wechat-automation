import os
import json
import tempfile
import emoji
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from deepseek_wechat_automation.app import database, settings
from deepseek_wechat_automation.app.database import session_ctx
from deepseek_wechat_automation.app.models import AIGCResult, UploaderCredential, Uploaders
from deepseek_wechat_automation.app.sessions import async_httpx_ctx
from deepseek_wechat_automation.app.uploader.base import IUploader
from deepseek_wechat_automation.app.usecases.clipboard import copy_image_to_clipboard, copy_text_to_clipboard


class OffiAccountUploader(IUploader):
    def create_context(self, username: str, password: str) -> UploaderCredential:
        self.create_driver()
        self.driver.get("https://mp.weixin.qq.com/cgi-bin/loginpage")
        # 点击使用账号密码登录
        self.driver.find_element(By.XPATH, "//a[@class='login__type__container__select-type']").click()
        # 输入账号和密码
        self.driver.find_element(By.CSS_SELECTOR, "input[name='account']").send_keys(username)
        self.driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(password)
        # 点击登录并等待登录成功
        self.driver.find_element(By.CLASS_NAME, "btn_login").click()
        WebDriverWait(self.driver, 600).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='app']/div[2]/div[3]/div[2]/div/div[2]")))
        # 获取当前 token 和 cookies
        credential = {"token": self.driver.current_url.split("&token=")[1], "cookies": self.driver.get_cookies()}
        with session_ctx() as session:
            model = UploaderCredential(
                uploader=Uploaders.OFFIACCOUNT,
                username=username,
                password=password,
                credential=json.dumps(credential),
            )
            database.merge_model(session, model)
        self.leave_context(save=False)
        return model

    def enter_context(self, credential: UploaderCredential) -> bool:
        self.create_driver()
        # 设置 cookies 和 token
        self.driver.get(f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN")
        credential = json.loads(credential.credential)
        for cookie in credential["cookies"]:
            self.driver.add_cookie(cookie)
        token = credential["token"]
        # 进入公众号主页并进入新的创作 - 文章
        self.driver.get(f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={token}")
        try:
            self.driver.find_element(By.XPATH, "//*[@id='app']/div[2]/div[3]/div[2]/div/div[2]").click()
            # 切换至最新句柄
            handles = self.driver.window_handles
            self.driver.switch_to.window(handles[-1])
            return True
        except:
            return False

    def leave_context(self, save: bool = True) -> None:
        if save:
            # 点击发表按钮
            self.driver.find_element(By.XPATH, "//*[@id='js_send']/button").click()
            # 等待发表成功
            WebDriverWait(self.driver, 30).until(EC.url_changes(self.driver.current_url))
        self.drop_driver()

    def set_title(self, title: str) -> None:
        # 输入文章标题
        title = emoji.replace_emoji(title, "")
        element = self.driver.find_element(By.XPATH, "//*[@id='title']")
        element.clear()
        copy_text_to_clipboard(title)
        element.send_keys(Keys.CONTROL, "v")

    def set_author(self, author: str) -> None:
        # 输入作者
        element = self.driver.find_element(By.XPATH, "//*[@id='author']")
        element.clear()
        copy_text_to_clipboard(author)
        element.send_keys(Keys.CONTROL, "v")

    def insert_text(self, text: str) -> None:
        # 进入iframe
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, '//*[@id="ueditor_0"]'))
        # 输入文章内容
        copy_text_to_clipboard(text)
        self.driver.find_element(By.XPATH, "/html/body/p").send_keys(Keys.CONTROL, "v")
        # 退出iframe
        self.driver.switch_to.default_content()

    async def insert_image(self, image_url: str) -> None:
        async with async_httpx_ctx() as session:
            response = await session.get(image_url)
            image_filename = os.path.basename(image_url.split("?")[0] if "?" in image_url else image_url)
            image_path = os.path.join(tempfile.gettempdir(), image_filename)
            with open(image_path, "wb") as f:
                f.write(response.content)
            copy_image_to_clipboard(image_path)
        # 进入iframe
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, '//*[@id="ueditor_0"]'))
        # 输入文章内容
        self.driver.find_element(By.XPATH, "/html/body/p").send_keys(Keys.CONTROL, "v")
        # 退出iframe
        self.driver.switch_to.default_content()

    async def insert_result(self, result: AIGCResult) -> None:
        # 将文本分割为标题和正文
        lines = [line.strip() for line in result.text.split("\n") if line.strip()]
        title = lines[0]
        body = "\n".join(lines[1:])

        self.set_title(title)
        self.set_author(settings.article_author)

        cur_index = 1
        cur_pos = 0
        last_pos = 0

        while True:
            cur_pos = body.find(f"<img{cur_index}>", last_pos)
            if cur_pos == -1:
                break

            # 插入当前 <img+编号> 标签之前的内容
            self.insert_text(body[last_pos:cur_pos])

            # 提取图片编号并获取相应的图片 URL
            if url := result.images.get(f"img{str(cur_index)}"):
                await self.insert_image(url)

            # 跳过当前 <img+编号> 标签
            last_pos = cur_pos + len(f"<img{cur_index}>")
            cur_index += 1

        # 插入最后一个 <img+编号> 标签之后的剩余内容
        self.insert_text(body[last_pos:])
