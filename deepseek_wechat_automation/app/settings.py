import os
from dotenv import load_dotenv

from deepseek_wechat_automation.app.logging import Ansi, log

if not load_dotenv():
    log("Failed to load .env file, using default settings.", Ansi.LRED)
    log("Please make sure you have a .env file in the root directory.", Ansi.LRED)
    log("You can copy .env.example to .env and modify the settings.", Ansi.LRED)
    log("Default settings may not work properly because of missing api keys.", Ansi.LYELLOW)

# Basic
db_url = os.environ.get("DATABASE_URL", "sqlite:///./db.sqlite3")
proxy_url = os.environ.get("PROXY_URL", None)
web_port = int(os.environ.get("WEB_PORT", 8000))
web_host = os.environ.get("WEB_HOST", "127.0.0.1")
article_author = os.environ.get("ARTICLE_AUTHOR", "小编")

# OpenAI API
llm_url = os.environ.get("LLM_API_URL", "https://ark.cn-beijing.volces.com/api/v3/bots/")
llm_key = os.environ.get("LLM_API_KEY", "")
llm_model = os.environ.get("LLM_MODEL", "bot-20250215153018-mj9m7")

# Siliconflow API
t2i_url = os.environ.get("T2I_API_URL", "https://api.siliconflow.cn/v1/")
t2i_key = os.environ.get("T2I_API_KEY", "")
t2i_model = os.environ.get("T2I_MODEL", "deepseek-ai/Janus-Pro-7B")

# Scheduler
scheduler_cron = os.environ.get("SCHEDULER_CRON", "*/10 * * * *")
