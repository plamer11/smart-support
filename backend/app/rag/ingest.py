
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..config import settings

KB_DIR = Path(settings.chroma_dir).parent / "kb"

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "，", " "],
)


def load_and_split():
    loader = DirectoryLoader(
        str(KB_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"autodetect_encoding": True},
    )
    docs = loader.load()

    chunks = []
    for doc in docs:
        source = Path(doc.metadata.get("source", "faq.md")).stem

        sections = doc.page_content.split("\n## ")
        for i, sec in enumerate(sections):
            if not sec.strip():
                continue
            first_line = sec.splitlines()[0].strip()
            section_name = first_line.lstrip("#").strip() or source
            body = sec if i == 0 else "## " + sec
            for c in splitter.create_documents([body]):
                c.metadata = {"source": source, "section": section_name}
                chunks.append(c)
    return chunks


def ingest():
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings

    chunks = load_and_split()
    print(f"共切分出 {len(chunks)} 个知识片段，开始向量化入库……")

    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=settings.chroma_dir,
        collection_name="smartsupport_kb",
    )
    print(f"入库完成，向量库目录：{settings.chroma_dir}")


if __name__ == "__main__":
    ingest()
