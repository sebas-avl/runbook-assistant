def chunk_text(text:str, chunk_size: int = 800, overlap: int=100) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    step = chunk_size - overlap
    chunks: list[str] = []
    for start in range (0, len(text), step):
        end = start + chunk_size
        chunks.append(text[start:end])
        # stop once a chunk reaches the end, otherwise the last chunk would be redundant
        if end >= len(text):
            break                   
    return chunks