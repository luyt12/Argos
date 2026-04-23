"""
Argos Translator - 全文翻译（每篇最多1000字）
"""
import os
import sys
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_CHARS_PER_ARTICLE = 1000  # 每篇文章最多翻译字数
_translator = None


def ensure_model():
    """确保 en→zh 模型已安装"""
    global _translator
    if _translator is not None:
        return _translator

    import argostranslate.package
    import argostranslate.translate

    try:
        _translator = argostranslate.translate.get_translation_from_codes("en", "zh")
        logging.info("Argos en→zh model ready")
        return _translator
    except Exception:
        pass

    logging.info("Installing Argos en→zh model (first run)...")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    pkg = next((p for p in available if p.from_code == "en" and p.to_code == "zh"), None)
    if not pkg:
        raise RuntimeError("Argos en→zh model not found")
    argostranslate.package.install_from_path(pkg.download())
    _translator = argostranslate.translate.get_translation_from_codes("en", "zh")
    logging.info("Argos model installed")
    return _translator


def translate_text(text: str) -> str:
    """翻译文本"""
    text = (text or "").strip()
    if not text:
        return text
    t = ensure_model()
    try:
        return t.translate(text)
    except Exception as e:
        logging.warning(f"Translation error: {e}")
        return text


def truncate_to_limit(text: str, limit: int = MAX_CHARS_PER_ARTICLE) -> str:
    """截取前 limit 个字符，按句子边界截断"""
    if len(text) <= limit:
        return text
    # 在 limit 附近找句子边界
    truncated = text[:limit]
    # 找最后一个句号、问号、感叹号
    for end in ['。', '！', '？', '.', '!', '?']:
        idx = truncated.rfind(end)
        if idx > limit * 0.7:  # 至少保留 70%
            return truncated[:idx + 1]
    # 没找到句子边界，按空格截断
    last_space = truncated.rfind(' ')
    if last_space > limit * 0.5:
        return truncated[:last_space] + '...'
    return truncated + '...'


def translate_article(article_md: str) -> str:
    """
    翻译单篇文章（Markdown格式）
    - 保留标题、链接、作者行
    - 只翻译正文，最多翻译前 MAX_CHARS_PER_ARTICLE 字符
    """
    lines = article_md.strip().split('\n')
    result = []
    body_lines = []
    header_done = False

    for line in lines:
        stripped = line.strip()
        # 标题行
        if stripped.startswith('## '):
            if body_lines:
                # 先处理之前积累的正文
                body_text = ' '.join(body_lines)
                translated_body = translate_text(truncate_to_limit(body_text))
                result.append(translated_body)
                body_lines = []
            # 翻译标题
            title_text = stripped[3:]
            result.append('## ' + translate_text(title_text))
            continue
        # 链接行、作者行、分隔线：直接保留
        if stripped.startswith('链接：') or stripped.startswith('作者：') or stripped == '---' or stripped.startswith('http'):
            if body_lines:
                body_text = ' '.join(body_lines)
                translated_body = translate_text(truncate_to_limit(body_text))
                result.append(translated_body)
                body_lines = []
            result.append(line)
            continue
        # 空行
        if not stripped:
            if body_lines:
                body_text = ' '.join(body_lines)
                translated_body = translate_text(truncate_to_limit(body_text))
                result.append(translated_body)
                body_lines = []
            result.append('')
            continue
        # 正文
        body_lines.append(stripped)

    # 处理剩余正文
    if body_lines:
        body_text = ' '.join(body_lines)
        translated_body = translate_text(truncate_to_limit(body_text))
        result.append(translated_body)

    return '\n'.join(result)


def translate_file(filepath: str) -> bool:
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return False

    os.makedirs("translate", exist_ok=True)
    outpath = os.path.join("translate", os.path.basename(filepath))

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    logging.info(f"Translating: {filepath} ({len(content)} chars)")

    # 按 --- 分割文章
    articles = re.split(r'\n---\n', content)
    translated_parts = []

    for i, article in enumerate(articles):
        article = article.strip()
        if not article:
            continue
        logging.info(f"  Article {i+1}/{len(articles)}...")
        translated_parts.append(translate_article(article))

    result = '\n\n---\n\n'.join(translated_parts)

    with open(outpath, "w", encoding="utf-8") as f:
        f.write(result)

    logging.info(f"Translation saved: {outpath}")
    return True


if __name__ == "__main__":
    import glob
    if len(sys.argv) > 1:
        translate_file(sys.argv[1])
    else:
        files = glob.glob("dailynews/*.md")
        if files:
            translate_file(max(files, key=os.path.getmtime))
        else:
            logging.error("No article files found")