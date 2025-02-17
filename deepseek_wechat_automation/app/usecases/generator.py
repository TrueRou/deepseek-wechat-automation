import re
import json

from deepseek_wechat_automation.app import database
from deepseek_wechat_automation.app.database import session_ctx
from deepseek_wechat_automation.app.models import AIGCContent, AIGCResult
from deepseek_wechat_automation.app.sessions import async_httpx_ctx, openai_client
from deepseek_wechat_automation.app import settings

text_prompt = """
你的任务是根据当天获取到的热点事件或者用户给定的具体领域生成一篇微信公众号推文，并在合适的地方插入图片，同时文章要搭配适当的emoji。
在撰写推文时，请遵循以下指南:
1. 推文开头要有一个吸引人的标题，标题中可适当使用emoji。
2. 正文部分要详细阐述热点事件，逻辑清晰，语言流畅。
3. 在合适的地方插入提供的图片，使用<img+数字>作为占位符
4. 可适当表达自己对热点事件的观点和看法，使用emoji增强情感表达。
5. 推文结尾要有一个总结或引导互动的话语，搭配emoji。
6. 确保推文没有任何拼写或语法错误。
7. 图片不需要你获取，只需要将你描述出图片的大致要求即可。
8. 文章长度尽量不要过短。
请在<wechat_article>标签内写下你的推文。
请在<image_requirements>标签内写下图片的要求，格式为 <img+数字>: 内容。
"""


async def _new_text(retry: int = 0) -> tuple[str, dict[str, str], int]:
    resp = await openai_client.chat.completions.create(
        model="bot-20250215153018",
        messages=[{"role": "system", "content": text_prompt}],
        stream=False,
    )
    content = resp.choices[0].message.content

    article_match: re.Match[str] = re.search(r"<wechat_article>(.*?)</wechat_article>", content, re.DOTALL)
    images_match: re.Match[str] = re.search(r"<image_requirements>(.*?)</image_requirements>", content, re.DOTALL)
    if not article_match or not images_match:
        return await _new_text(retry + 1)

    image_requirements = {f"img{img[0]}": img[1] for img in re.findall(r"<img(\d+)>: (.*?)\n", images_match.group(1))}
    return article_match.group(1), image_requirements, retry


async def _new_image(prompt: str) -> str:
    async with async_httpx_ctx() as session:
        resp = await session.post(
            f"{settings.t2i_url}images/generations",
            headers={"Authorization": f"Bearer {settings.t2i_key}"},
            content={"model": settings.t2i_model, "prompt": prompt},
        )
        return resp.json()["images"][0]["url"]


async def generate_one() -> AIGCResult:
    with session_ctx() as session:
        text_content, image_requirements, retry = await _new_text()
        aigc_content = AIGCContent(text_content=text_content, image_content=json.dumps(image_requirements, ensure_ascii=False), retry=retry)
        database.add_model(session, aigc_content)
        images = {img_id: await _new_image(prompt) for img_id, prompt in image_requirements.items()}
        return AIGCResult(text=text_content, images=images)
