import os
import glob
from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions
from rich.console import Console

console = Console()

class JarvisRAG:
    def __init__(self, data_dir: str = "data", db_dir: str = "chroma_db"):
        self.data_dir = data_dir
        self.db_dir = db_dir
        
        # Initialize local persistent vector database
        self.client = chromadb.PersistentClient(path=self.db_dir)
        
        # Use local lightweight sentence-transformers embedding model
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="jarvis_knowledge",
            embedding_function=self.embedding_fn
        )

    def _chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
        """Splits large text into overlapping chunks to preserve semantic context."""
        words = text.split()
        if not words:
            return []
        
        chunks = []
        step = chunk_size - overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    def ingest_documents(self):
        """Scans the data/ folder and indexes all TXT, MD, and PDF files."""
        console.print("[cyan]Ingesting personal documents into vector store...[/cyan]")
        
        # Clear existing collection for clean rebuild
        self.client.delete_collection("jarvis_knowledge")
        self.collection = self.client.get_or_create_collection(
            name="jarvis_knowledge",
            embedding_function=self.embedding_fn
        )

        all_files = glob.glob(f"{self.data_dir}/**/*.*", recursive=True)
        total_chunks = 0

        for file_path in all_files:
            ext = os.path.splitext(file_path)[1].lower()
            text = ""

            try:
                if ext in [".txt", ".md", ".py", ".cpp", ".c", ".json"]:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                elif ext == ".pdf":
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
            except Exception as e:
                console.print(f"[yellow]Skipping {file_path}: {e}[/yellow]")
                continue

            if not text.strip():
                continue

            chunks = self._chunk_text(text)
            for idx, chunk in enumerate(chunks):
                doc_id = f"{os.path.basename(file_path)}_{idx}"
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{"source": os.path.basename(file_path)}],
                    ids=[doc_id]
                )
                total_chunks += 1

        console.print(f"[green]✓ Ingested {len(all_files)} files into {total_chunks} vector chunks.[/green]")

    def search(self, query: str, top_k: int = 2) -> str:
        """Retrieves the top-k most semantically relevant text chunks for a query."""
        if self.collection.count() == 0:
            return ""

        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count())
        )

        if not results or not results.get("documents") or not results["documents"][0]:
            return ""

        retrieved_docs = results["documents"][0]
        context = "\n---\n".join(retrieved_docs)
        return context

if __name__ == "__main__":
    rag = JarvisRAG()
    rag.ingest_documents()
    res = rag.search("What is Project Titan?")
    console.print(f"[bold green]Retrieved Context:[/bold green]\n{res}")