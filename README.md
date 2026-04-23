# Argos - Foreign Policy Blogs 全文翻译

每日抓取 [Foreign Policy Blogs](https://foreignpolicyblogs.com/) 最新文章，使用 ArgosTranslate 离线翻译为中文，通过邮件发送。

## 特点

- **离线翻译**：ArgosTranslate 不调用任何 API，首次运行自动下载 en→zh 模型
- **限流控制**：每次最多抓取 3 篇新文章，每篇最多翻译前 1000 字
- **去重机制**：processed_urls.json 记录已处理链接，确保不重复

## 工作流

北京时间每天 20:00 自动运行。

## 本地测试

```bash
pip install -r requirements.txt
python daily_task.py
```

## 配置

GitHub Secrets:
- `EMAIL_TO`: 收件邮箱
- `EMAIL_FROM`: 发件邮箱
- `SMTP_HOST`: smtp.agentmail.to
- `SMTP_PORT`: 465
- `SMTP_USER`: 发件邮箱
- `SMTP_PASS`: AgentMail 密码