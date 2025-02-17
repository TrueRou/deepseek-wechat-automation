import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from deepseek_wechat_automation.app import database
from deepseek_wechat_automation.app.database import session_ctx
from deepseek_wechat_automation.app.models import UploaderCredential, Uploaders
from deepseek_wechat_automation.app.uploader.base import IUploader


class OffiAccountUploader(IUploader):
    def create_context(self, username: str, password: str) -> UploaderCredential:
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
        return model

    def enter_context(self, credential: UploaderCredential) -> None:
        # 设置 cookies 和 token
        credential = json.loads(credential.credential)
        for cookie in credential.credential["cookies"]:
            self.driver.add_cookie(cookie)
        token = credential.credential["token"]
        # 进入公众号主页并进入新的创作 - 文章
        self.driver.get(f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={token}")
        self.driver.find_element(By.XPATH, "//*[@id='app']/div[2]/div[3]/div[2]/div/div[2]").click()

    def leave_context(self, credential: UploaderCredential, save: bool = True) -> None:
        if save:
            # 点击发表按钮
            self.driver.find_element(By.XPATH, "//*[@id='js_send']/button").click()
            # 等待发表成功
            WebDriverWait(self.driver, 30).until(EC.url_changes(self.driver.current_url))
        # 点击登出账号
        credential = json.loads(credential.credential)
        token = credential.credential["token"]
        self.driver.get(f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={token}")
        self.driver.find_element(By.XPATH, "//*[@id='js_mp_sidemenu']/div/div[3]/div[2]/div[2]/ul/li[4]/a").click()

    def set_title(self, title: str) -> None:
        # 输入文章标题
        element = self.driver.find_element(By.XPATH, "//*[@id='title']")
        element.clear()
        element.send_keys(title)

    def set_author(self, author: str) -> None:
        # 输入作者
        element = self.driver.find_element(By.XPATH, "//*[@id='author']")
        element.clear()
        element.send_keys(author)

    def set_head_image(self, image_url: str) -> None:
        pass

    def insert_text(self, text: str) -> None:
        # 进入iframe
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, '//*[@id="ueditor_0"]'))
        # 输入文章内容
        self.driver.find_element(By.XPATH, "/html/body/p").send_keys(text)
        # 退出iframe
        self.driver.switch_to.default_content()

    def insert_image(self, image_url: str) -> None:
        pass
