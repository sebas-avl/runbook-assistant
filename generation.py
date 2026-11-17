import os

from embeddings import get_client


def build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[{number}] ({chunk['source']})\n{chunk['text']}"
        for number, chunk in enumerate(chunks, start=1)
    )
    return (
        "Answer the question using ONLY the context below. "
        "If the context does not contain the answer, say you don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )

def generate_answer(prompt: str) -> str:
    response = get_client().converse(
        modelId=os.environ["TEXT_MODEL_ID"],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 500, "temperature": 0.0},
    )
    return response["output"]["message"]["content"][0]["text"]