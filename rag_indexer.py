# rag_indexer.py
import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from utils.extractor import extract_text
from utils.splitter import split_text_into_chunks

UPLOAD_FOLDER = './uploads'
INDEX_PATH = 'rag_index.index'
META_PATH = 'rag_meta.pkl'
EMBED_MODEL = 'all-MiniLM-L6-v2'  # 小巧高效

model = SentenceTransformer(EMBED_MODEL)

def build_rag_index():
    docs, metadata = [], []

    for folder in os.listdir(UPLOAD_FOLDER):
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                path = os.path.join(folder_path, filename)
                text = extract_text(path)
                chunks = split_text_into_chunks(text)
                for chunk in chunks:
                    docs.append(chunk)
                    metadata.append({'folder': folder, 'file': filename})

    embeddings = model.encode(docs, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    # 保存索引和元数据
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, 'wb') as f:
        pickle.dump((docs, metadata), f)

    print(f"✅ 构建完成：共索引 {len(docs)} 个片段")
