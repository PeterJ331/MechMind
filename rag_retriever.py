# rag_retriever.py（动态重建索引版本）

import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.extractor import extract_text

UPLOAD_FOLDER = './uploads'
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
EMBED_MODEL = 'all-MiniLM-L6-v2'

model = SentenceTransformer(EMBED_MODEL)

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks

def build_index_from_uploads(upload_dir=UPLOAD_FOLDER):
    all_chunks = []
    metadata = []

    for root, _, files in os.walk(upload_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                text = extract_text(file_path)
                chunks = chunk_text(text)
                all_chunks.extend(chunks)
                metadata.extend([file_path] * len(chunks))
            except Exception as e:
                print(f"❌ 跳过文件: {file_path} 错误: {e}")
                continue

    if not all_chunks:
        return None, [], []

    embeddings = model.encode(all_chunks, convert_to_numpy=True, show_progress_bar=False)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return index, all_chunks, metadata

def retrieve_top_k(question, k=10):
    index, all_chunks, metadata = build_index_from_uploads()
    if index is None:
        return ["❌ 当前库为空，未检索到任何内容"]

    question_embedding = model.encode([question])
    distances, indices = index.search(question_embedding, k)

    top_chunks = []
    for i, dist in zip(indices[0], distances[0]):
        if i < len(all_chunks):
            content = all_chunks[i]
            source = metadata[i]
            similarity_score = 1 / (1 + dist)
            formatted = f"[{source}] 相似度: {similarity_score:.4f}\n{content}"
            top_chunks.append(formatted)

    return top_chunks
