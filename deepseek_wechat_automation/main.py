import logging

import uvicorn

from deepseek_wechat_automation.app.logging import Ansi, log
from deepseek_wechat_automation.app.templates import asgi_app
from deepseek_wechat_automation.app.settings import web_port, web_host


def app():
    log(f"Uvicorn running on http://{web_host}:{str(web_port)} (Press CTRL+C to quit)", Ansi.YELLOW)
    uvicorn.run(asgi_app, log_level=logging.WARNING, port=web_port, host=web_host)


if __name__ == "__main__":
    app()
