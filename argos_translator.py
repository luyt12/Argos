"""
Argos Translator
使用 argostranslate 离线翻译引擎将英文文章全文翻译为简体中文。
"""
import os
import sys
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_translator = None


def ensure_model():
    """确保 en→zh 翻译模型已安装（首次运行自动下载）"""
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

    logging.info("Installing Argos en→zh model (first run, downloading)...")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    pkg = next((p for p in available if p.from_code == "en" and p.to_code == "zh"), None)
    if not pkg:
        raise RuntimeError("Argos en→zh model not found in package index")
    argostranslate.package.install_from_path(pkg.download())
    _translator = argostranslate.translate.get_translation_from_codes("en", "zh")
    logging.info("Argos model installed successfully")
    return _translator


def translate_text(text: str) -> str:
    """翻译单段文本，空文本直接返回"""
    text = (text or "").strip()
    if not text:
        return text
    t = ensure_model()
    try:
        return t.translate(text)
    except Exception as e:
        logging.warning(f"Translation error: {e}")
        return text


def translate_markdown(content: str) -> str:
    """
    逐段翻译 Markdown 文档。
    - 保留 ## 标题结构、链接行、分隔线
    - 对正文段落逐段翻译
    """
    lines = content.split("\n")
    result = []
    buffer = []

    def flush_buffer():
        if buffer:
            para = " ".join(buffer).strip()
            if para:
                result.append(translate_text(para))
            buffer.clear()

    for line in lines:
        stripped = line.strip()

        # 空行：刷新缓冲
        if not stripped:
            flush_buffer()
            result.append("")
            continue

        # 标题行：翻译标题文字
        if stripped.startswith("#"):
            flush_buffer()
            # 提取 # 前缀和标题文字
            m = re.match(r"(#+\s*)(.*)", stripped)
            if m:
                prefix, title_text = m.group(1), m.group(2)
                result.append(prefix + translate_text(title_text))
            else:
                result.append(line)
            continue

        # 链接行（以"链接："开头）或分隔线：直接保留
        if stripped.startswith("链接：") or stripped == "---" or stripped.startswith("作者："):
            flush_buffer()
            result.append(line)
            continue

        # Markdown 链接行（纯链接）
        if re.match(r"^\[.*\]\(.*\)$", stripped) or re.match(r"^https?://", stripped):
            flush_buffer()
            result.append(line)
            continue

        # 普通段落：加入缓冲
        buffer.append(stripped)

    flush_buffer()
    return "\n".join(result)


def translate_file(filepath: str) -> bool:
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return False

    os.makedirs("translate", exist_ok=True)
    outpath = os.path.join("translate", os.path.basename(filepath))

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    logging.info(f"Translating: {filepath} ({len(content)} chars)")

    # 按文章分割（以 --- 分隔）
    articles = content.split("\n---\n")
    translated_parts = []

    for i, article in enumerate(articles):
        article = article.strip()
        if not article:
            continue
        logging.info(f"  Article {i+1}/{len(articles)} ({len(article)} chars)...")
        translated_parts.append(translate_markdown(article))

    result = "\n\n---\n\n".join(translated_parts)

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
