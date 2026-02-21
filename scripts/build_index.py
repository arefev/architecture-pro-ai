import os
import json
import time
from typing import List
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer

# ----------------------------------------------
# 1. Настроим пути
# ----------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
INDEX_DIR = os.path.join(BASE_DIR, "vector_index")

t0 = time.time()

# ----------------------------------------------
# 2. Инициализация модели эмбеддингов
# ----------------------------------------------

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Обёртка для совместимости с FAISS LangChain
class LocalEmbeddingWrapper:
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text):
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()

    # ВАЖНО: FAISS вызывает объект как функцию
    def __call__(self, text):
        return self.embed_query(text)

emb = LocalEmbeddingWrapper(embedding_model)

# ----------------------------------------------
# 3. Функция чтения файлов
# ----------------------------------------------

def load_documents(base_path: str):
    docs = []
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith((".md", ".txt")):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                docs.append({"path": path, "text": text})
    return docs

documents = load_documents(KB_DIR)

# ----------------------------------------------
# 4. Чанкирование текста
# ----------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", "!", "?", " "]
)

chunked_docs = []

for doc in documents:
    chunks = splitter.split_text(doc["text"])
    for i, chunk in enumerate(chunks):
        chunked_docs.append({
            "id": str(uuid4()),
            "content": chunk,
            "source": doc["path"],
            "chunk_index": i
        })

# ----------------------------------------------
# 5. Подготовка данных для FAISS
# ----------------------------------------------

texts = [c["content"] for c in chunked_docs]
metadatas = [{"source": c["source"], "chunk_id": c["id"], "index": c["chunk_index"]} 
             for c in chunked_docs]

# ----------------------------------------------
# 6. Создание FAISS-индекса
# ----------------------------------------------

vector_store = FAISS.from_texts(
    texts=texts,
    embedding=emb,
    metadatas=metadatas
)

# Сохраняем индекс
vector_store.save_local(INDEX_DIR)

print("Готово! Индекс создан и сохранён в:", INDEX_DIR)

# ----------------------------------------------
# 7. Пример поиска
# ----------------------------------------------

query = "Кто такой Xarn Velgor?"
results = vector_store.similarity_search(query, k=3)

for r in results:
    print("----")
    print("Источник:", r.metadata["source"])
    print("Чанк:", r.metadata["index"])
    print(r.page_content)


total_time = time.time() - t0
print ("Создано чанков:", len(chunked_docs))
print (f"  Время генерации: {total_time:.2f} сек")
