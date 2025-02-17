import os
from dotenv import load_dotenv

load_dotenv()

# Basic
db_url = os.environ.get("DATABASE_URL", "sqlite:///./db.sqlite3")
proxy_url = os.environ.get("PROXY_URL", None)
web_port = int(os.environ.get("WEB_PORT", 8000))

# OpenAI API
llm_url = os.environ.get("LLM_API_URL", "https://ark.cn-beijing.volces.com/api/v3/bots/")
llm_key = os.environ.get("LLM_API_KEY", "")
llm_model = os.environ.get("LLM_MODEL", "bot-20250215153018-mj9m7")

# Siliconflow API
t2i_url = os.environ.get("T2I_API_URL", "https://api.siliconflow.cn/v1/")
t2i_key = os.environ.get("T2I_API_KEY", "")
t2i_model = os.environ.get("T2I_MODEL", "deepseek-ai/Janus-Pro-7B")
