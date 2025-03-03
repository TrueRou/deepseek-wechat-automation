import os
import json
import tempfile
import time
import emoji
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from deepseek_wechat_automation.app import database, settings
from deepseek_wechat_automation.app.database import session_ctx
from deepseek_wechat_automation.app.logging import Ansi, log
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
            account = session.get(UploaderCredential, (Uploaders.OFFIACCOUNT, username))
            if not account:
                account = UploaderCredential(
                    uploader=Uploaders.OFFIACCOUNT,
                    username=username,
                    password=password,
                    credential=json.dumps(credential),
                )
                database.add_model(session, account)
            else:
                account.credential = json.dumps(credential)
                account.is_expired = False
            session.commit()
        self.leave_context(save=False)
        return account

    def enter_context(self, credential: UploaderCredential, view_only: bool = False) -> bool:
        self.create_driver()
        # 设置 cookies 和 token
        self.driver.get(f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN")
        credential_dict = json.loads(credential.credential)
        for cookie in credential_dict["cookies"]:
            self.driver.add_cookie(cookie)
        token = credential_dict["token"]
        # 进入公众号主页并进入新的创作 - 文章
        self.driver.get(f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={token}")
        try:
            WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='app']/div[2]/div[3]/div[2]/div/div[2]")))
            button = self.driver.find_element(By.XPATH, "//*[@id='app']/div[2]/div[3]/div[2]/div/div[2]")
            username = self.driver.find_element(By.XPATH, "//*[@id='app']/div[2]/div[1]/div[1]/div/div[1]/div")
            credential.override_username = username.text
            if not view_only:
                button.click()
                # 切换至最新句柄
                handles = self.driver.window_handles
                self.driver.switch_to.window(handles[-1])
            return True
        except Exception as e:
            return False

    def leave_context(self, save: bool = True) -> None:
        if self.driver:
            if save:
                # 点击发表按钮
                self.driver.find_element(By.XPATH, "//*[@id='js_send']/button").click()

                try:
                    dialog_path = "//*[@id='wxDialog_1']/div[3]/a[1]"
                    WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, dialog_path)))
                    self.driver.find_element(By.XPATH, dialog_path).click()
                except:
                    pass  # 本次不是第一次群发，不用关闭弹窗

                # 等待发表按钮出现
                btn_path = "//*[@id='vue_app']/div[2]/div[1]/div[1]/div/div[3]/div/div/div[1]/button"
                btn_next_path = "//*[@id='vue_app']/div[2]/div[2]/div[1]/div/div[3]/div/div[1]/button"
                WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, btn_path)))
                self.driver.find_element(By.XPATH, btn_path).click()
                try:
                    WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, btn_next_path)))
                    self.driver.find_element(By.XPATH, btn_next_path).click()
                except:
                    pass  # 本次不是群发，不用寻找下一步按钮
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

    def set_header(self, header: str | None = None) -> None:
        if header is not None:
            raise NotImplementedError("OffiAccountUploader does not support setting custom header")

        def scroll_to_bottom():
            try:
                # 等待页面初始加载
                WebDriverWait(self.driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

                last_height = self.driver.execute_script("return document.body.scrollHeight")
                while True:
                    # 渐进式滚动
                    self.driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(1.5)  # 等待内容加载

                    # 检查高度变化
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # 最后确认是否真的到底
                        time.sleep(2)
                        final_height = self.driver.execute_script("return document.body.scrollHeight")
                        if final_height == new_height:
                            break
                    last_height = new_height

                # 滚动到封面区域
                cover = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="js_cover_area"]/div[1]/span')))
                self.driver.execute_script(
                    """
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                    window.scrollBy(0, -100);
                """,
                    cover,
                )

                # 确保元素可交互
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="js_cover_area"]/div[1]')))

            except Exception as e:
                log(f"滚动过程中出错: {str(e)}", Ansi.LRED)
                raise

        try:
            # 执行滚动
            scroll_to_bottom()
            time.sleep(2)

            # 悬停在封面区域
            cover_area = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="js_cover_area"]/div[1]')))
            ActionChains(self.driver).move_to_element(cover_area).pause(1).perform()

            # 点击"从正文选择"
            self.driver.find_element(By.XPATH, '//*[@id="js_cover_null"]/ul/li[1]/a').click()

            # 选择第一张图片
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="vue_app"]/div[2]/div[1]/div/div[2]/div[1]/div/ul/li/div'))
            ).click()
            time.sleep(2)

            # 点击下一步
            self.driver.find_element(By.XPATH, '//*[@id="vue_app"]/div[2]/div[1]/div/div[3]/div[1]/button').click()
            time.sleep(2)

            # 最后确认
            self.driver.find_element(By.XPATH, '//*[@id="vue_app"]/div[2]/div[1]/div/div[3]/div[2]/button').click()
            time.sleep(2)

        except Exception as e:
            log(f"执行封面选择操作失败: {str(e)}", Ansi.LRED)
            self.leave_context(save=False)
            raise

    def insert_text(self, text: str) -> None:
        # 进入iframe
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, '//*[@id="ueditor_0"]'))
        # 输入文章内容
        copy_text_to_clipboard(text)
        self.driver.find_element(By.XPATH, "/html/body/p").send_keys(Keys.CONTROL, "v")
        # 退出iframe
        self.driver.switch_to.default_content()

    async def insert_image(self, image_url: str) -> None:
        if image_url.startswith("http"):
            async with async_httpx_ctx() as session:
                response = await session.get(image_url)
                image_filename = os.path.basename(image_url.split("?")[0] if "?" in image_url else image_url)
                image_path = os.path.join(tempfile.gettempdir(), image_filename)
                with open(image_path, "wb") as f:
                    f.write(response.content)
                copy_image_to_clipboard(image_path)
        elif os.path.exists(image_url):
            copy_image_to_clipboard(image_url)
        # 进入iframe
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, '//*[@id="ueditor_0"]'))
        # 输入文章内容
        self.driver.find_element(By.XPATH, "/html/body/p").send_keys(Keys.CONTROL, "v")
        # 退出iframe
        self.driver.switch_to.default_content()

    async def insert_result(self, result: AIGCResult, author: str | None = None) -> None:
        # 将文本分割为标题和正文
        lines = [line.strip() for line in result.text.split("\n") if line.strip()]
        title = lines[0]
        body = "\n".join(lines[1:])

        self.set_title(title)
        self.set_author(author or settings.article_author)

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

        # 设置封面
        self.set_header()
