def chunk_text(text, chunk_size=1000, overlap=150):
    """
    Split text into overlapping chunks so that important
    context is not lost at chunk boundaries.
    """

    if not text:
        return []

    text = " ".join(text.split())

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            boundary = text.rfind(" ", start, end)

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(end - overlap, start + 1)

    return chunks