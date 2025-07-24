from nltk.tokenize import sent_tokenize

def split_text_into_chunks(text, chunk_size=500):
    sentences = sent_tokenize(text)
    chunks = []
    chunk = ""
    for sent in sentences:
        if len(chunk) + len(sent) < chunk_size:
            chunk += sent + " "
        else:
            chunks.append(chunk.strip())
            chunk = sent + " "
    if chunk:
        chunks.append(chunk.strip())
    return chunks
