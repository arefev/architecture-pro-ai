"""
Задание 2: Замена терминов Star Wars → QuantumForge.
"""

import json
import re
import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
TERMS_MAP_PATH = os.path.join(KB_DIR, "terms_map.json")
RAW_TEXT_PATH = os.path.join(BASE_DIR, "raw_texts")

with open(TERMS_MAP_PATH, "r", encoding="utf-8") as f:
    terms = json.load(f)

input_dir = Path(RAW_TEXT_PATH)
output_dir = Path(KB_DIR)
output_dir.mkdir(exist_ok=True)

def replace_terms(text, mapping):
    for src, dst in sorted(mapping.items(), key=lambda x: -len(x[0])):
        # безопасная подмена с учётом регистра
        text = re.sub(rf"\b{re.escape(src)}\b", dst, text)
    return text

for file in input_dir.glob("*.txt"):
    content = file.read_text(encoding="utf-8")
    replaced = replace_terms(content, terms)
    (output_dir / file.name.replace(".txt", ".md")).write_text(replaced, encoding="utf-8")
