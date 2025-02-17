import asyncio

from deepseek_wechat_automation.app.usecases.generator import generate_one


async def test_generate():
    result = await generate_one()
    print(result)


asyncio.run(test_generate())
