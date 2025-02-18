from abc import ABC, abstractmethod
from selenium import webdriver

from deepseek_wechat_automation.app.models import UploaderCredential


class IUploader(ABC):
    driver: webdriver.Chrome

    def create_driver(self) -> None:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("disable-infobars")
        options.add_argument("--incognito")
        options.add_argument("log-level=3")
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)

    def drop_driver(self) -> None:
        self.driver.quit()

    @abstractmethod
    def create_context(self) -> UploaderCredential:
        pass

    @abstractmethod
    def enter_context(self, credential: UploaderCredential) -> None:
        pass

    @abstractmethod
    def leave_context(self, save: bool = True) -> None:
        pass

    @abstractmethod
    def set_title(self, title: str) -> None:
        pass

    @abstractmethod
    def set_author(self, author: str) -> None:
        pass

    @abstractmethod
    def set_head_image(self, image_url: str) -> None:
        pass

    @abstractmethod
    def insert_text(self, text: str) -> None:
        pass

    @abstractmethod
    def insert_image(self, image_url: str) -> None:
        pass
