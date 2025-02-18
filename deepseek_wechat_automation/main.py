import logging

import uvicorn

from app.logging import Ansi, log
from app.templates import asgi_app
from app.settings import web_port, web_host


if __name__ == "__main__":
    log(f"Uvicorn running on http://{web_host}:{str(web_port)} (Press CTRL+C to quit)", Ansi.YELLOW)
    uvicorn.run(asgi_app, log_level=logging.WARNING, port=web_port, host=web_host)
