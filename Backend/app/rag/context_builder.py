from typing import List, Dict


def build_rag_context(
    retrieved_chunks: List[Dict]
) -> str:
    """
    Convert retrieved chunks into a clean context
    for the LLM.
    """

    if not retrieved_chunks:
        return "No relevant evidence was retrieved from the paper."

    context_parts = []

    for index, item in enumerate(
        retrieved_chunks,
        start=1
    ):
        text = item.get("text", "").strip()

        if not text:
            continue

        context_parts.append(
            f"[Evidence {index}]\n{text}"
        )

    if not context_parts:
        return "No relevant evidence was retrieved from the paper."

    return "\n\n".join(context_parts)