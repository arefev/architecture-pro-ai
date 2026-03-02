#!/usr/bin/env python3
import os
import json
import hashlib
import logging
import faiss
import numpy as np
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# -------------------------------
# Пути
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
INDEX_DIR = os.path.join(BASE_DIR, "vector_index")

KB_PATH = os.path.join(BASE_DIR, "knowledge_base")
INDEX_PATH = os.path.join(BASE_DIR, "vector_index/index.faiss")
META_PATH = os.path.join(BASE_DIR, "knowledge_base/metadata.json")
FILE_HASHES = os.path.join(BASE_DIR, "knowledge_base/file_hashes.json")

# -------------------------------
# Логирование
# -------------------------------
logging.basicConfig(
    filename="update_index.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("=== Запуск обновления индекса ===")

# -------------------------------
# Настройка моделей
# -------------------------------
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDER = SentenceTransformer(MODEL_NAME)

# -------------------------------
# Фильтрация вредных паттернов
# -------------------------------
DANGER_PATTERNS = [
    "ignore all instructions",
    "output:",
    "пароль",
    "password",
    "root",
    "admin",
    "system prompt",
    "superuser",
]

def is_chunk_safe(text: str) -> bool:
    lowered = text.lower()
    return not any(p in lowered for p in DANGER_PATTERNS)

# -------------------------------
# Санитизация
# -------------------------------

import re

def sanitize(text: str) -> str:
    patterns = [
        r"(?i)ignore.*?instructions",
        r"(?i)output\s*:",
        r"(?i)system\s*prompt"
    ]
    cleaned = text
    for p in patterns:
        cleaned = re.sub(p, "", cleaned)
    return cleaned.strip()

# -------------------------------
# Хеширование файлов
# -------------------------------
def calculate_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# -------------------------------
# Загрузка существующих хешей
# -------------------------------
def load_hashes():
    if not os.path.exists(FILE_HASHES):
        return {}
    with open(FILE_HASHES, "r", encoding="utf-8") as f:
        return json.load(f)

def save_hashes(hashes):
    with open(FILE_HASHES, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=4, ensure_ascii=False)


# -------------------------------
# Сканирование базы знаний
# -------------------------------
def scan_documents():
    hashes_before = load_hashes()
    hashes_after = {}
    modified_files = []

    for fpath in Path(KB_PATH).rglob("*.md"):
        h = calculate_hash(fpath)
        hashes_after[str(fpath)] = h
        if hashes_before.get(str(fpath)) != h:
            modified_files.append(fpath)

    return modified_files, hashes_after


# -------------------------------
# Разбиение на чанки
# -------------------------------
def chunk_document(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80
    )
    docs = splitter.split_documents([Document(page_content=text)])
    return docs


# -------------------------------
# Загрузка существующего индекса
# -------------------------------
def load_index():
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
    else:
        index = None
    return index


# -------------------------------
# Загрузка метаданных
# -------------------------------
def load_metadata():
    if not os.path.exists(META_PATH):
        return {"chunks": [], "metadata": [], "embedding_model": MODEL_NAME}
    with open(META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------
# Обновление индекса
# -------------------------------
def update_index():
    modified_files, new_hashlist = scan_documents()

    if not modified_files:
        logging.info("Изменений в документах нет. Обновление индекса не требуется.")
        return

    logging.info(f"Изменённые файлы: {len(modified_files)}")

    metadata = load_metadata()
    index = load_index()

    num_new_chunks = 0
    new_embeddings = []
    new_chunk_texts = []
    new_metadata_entries = []

    for path in modified_files:
        docs = chunk_document(path)

        for doc in docs:
            text = doc.page_content

            if not is_chunk_safe(text):
                logging.warning(f"[FILTER] Вредоносный чанк пропущен: {path}")
                continue

            clean_text = sanitize(text)

            new_chunk_texts.append(clean_text)
            new_metadata_entries.append({
                "source": str(path),
                "raw_len": len(text),
                "clean_len": len(clean_text),
                "timestamp": datetime.now().isoformat(),
            })
            num_new_chunks += 1

    if num_new_chunks == 0:
        logging.info("Нет безопасных новых чанков. Индекс не обновлён.")
        return

    # Генерация эмбеддингов
    new_embeddings = EMBEDDER.encode(new_chunk_texts, convert_to_numpy=True)

    if index is None:
        index = faiss.IndexFlatL2(new_embeddings.shape[1])

    index.add(new_embeddings)

    # Сохраняем индекс
    faiss.write_index(index, INDEX_PATH)

    # Обновляем метаданные
    metadata["chunks"] += new_chunk_texts
    metadata["metadata"] += new_metadata_entries
    metadata["embedding_model"] = MODEL_NAME

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    # Сохраняем обновлённые хеши
    save_hashes(new_hashlist)

    logging.info(f"Добавлено новых чанков: {num_new_chunks}")
    logging.info(f"Индекс обновлён. Всего чанков: {len(metadata['chunks'])}")


if __name__ == "__main__":
    try:
        update_index()
    except Exception as e:
        logging.error(f"ОШИБКА обновления индекса: {e}")
        raise