# architecture-pro-ai
Яндекс практикум 7 спринт. Создание AI бота.

Запуск зависимостей

**Используется sentence_transformers и ollama, большой вес скачиваемых файлов!**

```bash
pip install -r requirements.txt
```

Замена терминов:

```bash
python ./scripts/replace_terms.py
```

Создание индекса:

```bash
python ./scripts/build_index.py
```

Обновление индекса:

```bash
python ./scripts/update_index.py
```

Обновление индекса:

```bash
python ./scripts/update_index.py
```

Запуск cli бота:

```bash
python ./bot/rag_chain.py
```

Запуск тестов:

```bash
python ./bot/evaluate.py
```

Вопросы для тестов `./bot/golden_questions.txt`

Запуск телеграмм бота:

```bash
python ./bot/bot.py
```