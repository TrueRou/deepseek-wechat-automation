# deepseek-wechat-automation

自动生成微信公众号文章的封面图、摘要、正文内容，通过 Selenium 自动化操作浏览器实现。

## 使用方式

### 安装环境

- Python 3.12 以上版本, Chrome 浏览器
- 执行 `pip install poetry` 全局安装 Poetry
- 执行 `poetry install` 安装项目依赖
- 执行 `poetry run app` 运行项目

> 更新项目: `git pull && poetry install && poetry run app`

### 配置文件

- 在 项目根目录 目录下创建 `.env` 文件, 可以根据 `.env.example` 文件进行配置
- ARTICLE_AUTHOR 为微信公众号要求填写的作者名称
- SCHEDULER_CRON 是定时任务的 cron 表达式, 默认为每10分钟执行一次

### 数据库和前端

默认使用 SQLite 数据库, 在根目录会自动创建 `db.sqlite3` 文件

默认会启动一个 FastAPI (后端) 服务, 可以通过 http://127.0.0.1:8000/ 访问网页, 主要用来添加账号使用

如果要为单独账号设置独立的 Prompt 参数, 请自行打开 `db.sqlite3` 进行修改

## 一些说明

### 关于过期检测

- 支持检测账号是否过期, 如果过期了, 在定时任务的时候会自动跳过
- 如果已过期可以点击前端的 `Renew` 按钮进行更新，会重新走一遍第一次创建账号的流程

### 关于测试

- 项目中有一些测试用例, 可以进入 `tests` 目录进行逐项的测试
- 前端有一个 `Trigger Test` 按钮, 可以手动触发定时任务，但是执行到最后阶段的时候不会点击发布按钮

### 关于定时任务的逻辑

- 每隔十分钟从数据库中获取一个账号进行操作, 条件为 `WHERE is_expired=False ORDER BY updated_at ASC LIMIT 1`
- 如果登录失败, 无法创建上下文, 则会将账号标记为过期, 并且跳过这个账号
- 如果发布成功, 更新数据库中的 `updated_at` 为当前时间

