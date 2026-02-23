import json
import os
from rag_chain import rag_answer

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
GOLDEN_FILE = os.path.join(BASE_DIR, "bot/golden_questions.txt")

def read_golden_questions():
    questions = []
    with open(GOLDEN_FILE) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                questions.append(line.strip())
    return questions

def evaluate():
    questions = read_golden_questions()

    results = []

    for q in questions:
        result = rag_answer(q)

        chunks = result["chunks"]
        answer = result["answer"]
        sources = result["sources"]

        results.append({
            "query": q,
            "chunks": len(chunks),
            "answer_length": len(answer),
            "success": len(answer) > 30
        })

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    evaluate()