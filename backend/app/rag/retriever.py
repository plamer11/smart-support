
from ..config import settings


def get_retriever(k: int = 4):
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    vectorstore = Chroma(
        persist_directory=settings.chroma_dir,
        embedding_function=embeddings,
        collection_name="smartsupport_kb",
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})
