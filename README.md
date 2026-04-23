# Argos - Foreign Policy Blogs 全文翻译

抓取 [Foreign Policy Blogs](https://foreignpolicyblogs.com/) 每日文章，使用 [ArgosTranslate](https://github.com/argosopentech/argos-translate) 离线翻译引擎将英文全文翻译为简体中文，通过邮件发送。

## 工作流

每天北京时间 20:00 自动运行：
1. 抓取 `https://foreignpolicyblogs.com/feed/` 当日全部文章全文
2. 使用 ArgosTranslate（en→zh）逐段翻译 Markdown 正文
3. 生成 HTML 邮件发送

## 本地测试

```bash
pip install -r requirements.txt
python daily_task.py
```

## 依赖

- `argostranslate >= 1.9.6` — 离线翻译引擎（首次运行自动下载 en→zh 模型）
- `feedparser` — RSS 解析
- `html2text` — HTML 转 Markdown
- `markdown` — Markdown 转 HTML（邮件格式）