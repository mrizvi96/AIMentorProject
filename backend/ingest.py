"""
Document Ingestion Script
Ingests PDF documents into Milvus vector store for RAG retrieval
"""
import argparse
import logging
from pathlib import Path
from typing import List
import sys

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
import chromadb

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global ChromaDB client instance
chroma_client = None

def prepare_chromadb():
    """Prepare ChromaDB client (file-based, no server needed)"""
    global chroma_client
    try:
        logger.info(f"Using ChromaDB with database at {settings.chroma_db_path}")
        chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
        logger.info("✓ ChromaDB client prepared")
    except Exception as e:
        logger.error(f"Failed to prepare ChromaDB client: {e}")
        sys.exit(1)


def load_documents(directory: str) -> List:
    """Load documents from directory"""
    try:
        logger.info(f"Loading documents from {directory}...")

        # Check if directory exists
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory}")
            sys.exit(1)

        # Count PDF files
        pdf_files = list(dir_path.glob("**/*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files")

        # Load documents
        reader = SimpleDirectoryReader(
            input_dir=directory,
            required_exts=[".pdf"],
            recursive=True
        )
        documents = reader.load_data()

        logger.info(f"✓ Loaded {len(documents)} documents")
        return documents

    except Exception as e:
        logger.error(f"Failed to load documents: {e}")
        sys.exit(1)


def setup_embedding_model():
    """Setup embedding model"""
    try:
        logger.info(f"Loading embedding model: {settings.embedding_model_name}")
        embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model_name
        )
        logger.info("✓ Embedding model loaded")
        return embed_model
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        sys.exit(1)


def create_vector_store(overwrite: bool = False):
    """Create or connect to ChromaDB vector store"""
    global chroma_client
    if chroma_client is None:
        logger.error("ChromaDB client not initialized. Call prepare_chromadb() first.")
        sys.exit(1)

    try:
        collection_name = settings.chroma_collection_name

        if overwrite:
            logger.warning(f"Overwrite mode: will delete existing collection '{collection_name}' if it exists.")
            try:
                chroma_client.delete_collection(name=collection_name)
                logger.info(f"Existing collection '{collection_name}' deleted.")
            except Exception as e:
                logger.warning(f"Could not delete collection '{collection_name}' (might not exist): {e}")

        logger.info(f"Creating/connecting to ChromaDB collection '{collection_name}'...")
        collection = chroma_client.get_or_create_collection(name=collection_name)

        vector_store = ChromaVectorStore(chroma_collection=collection)
        logger.info("✓ Vector store ready")
        return vector_store

    except Exception as e:
        logger.error(f"Failed to create vector store: {e}")
        sys.exit(1)


def ingest_documents(documents: List, vector_store, embed_model):
    """Ingest documents into vector store"""
    try:
        logger.info("Starting document ingestion...")
        logger.info(f"Chunk size: {settings.chunk_size}, Overlap: {settings.chunk_overlap}")

        # Configure Settings
        Settings.embed_model = embed_model
        Settings.chunk_size = settings.chunk_size
        Settings.chunk_overlap = settings.chunk_overlap

        # Create node parser
        node_parser = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

        # Parse documents into nodes
        logger.info("Parsing documents into chunks...")
        nodes = node_parser.get_nodes_from_documents(documents)
        logger.info(f"Created {len(nodes)} chunks from {len(documents)} documents")

        # Create index and ingest
        logger.info("Generating embeddings and storing in ChromaDB...")
        logger.info("This may take several minutes depending on document size...")

        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store
        )

        # Insert nodes
        for i, node in enumerate(nodes, 1):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(nodes)} chunks processed")
            index.insert_nodes([node])

        logger.info("✓ Document ingestion complete!")
        logger.info(f"Total documents: {len(documents)}")
        logger.info(f"Total chunks: {len(nodes)}")
        logger.info(f"Collection: {settings.chroma_collection_name}")

    except Exception as e:
        logger.error(f"Failed to ingest documents: {e}")
        sys.exit(1)


def main():
    """Main ingestion function"""
    parser = argparse.ArgumentParser(
        description="Ingest PDF documents into ChromaDB vector store"
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=settings.course_materials_dir,
        help=f"Directory containing PDF files (default: {settings.course_materials_dir})"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing collection (deletes all existing data)"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("AI Mentor - Document Ingestion")
    logger.info("=" * 60)

    # Step 1: Prepare ChromaDB
    prepare_chromadb()

    # Step 2: Load documents
    documents = load_documents(args.directory)
    if not documents:
        logger.warning("No documents to ingest")
        sys.exit(0)

    # Step 3: Setup embedding model
    embed_model = setup_embedding_model()

    # Step 4: Create vector store
    vector_store = create_vector_store(overwrite=args.overwrite)

    # Step 5: Ingest documents
    ingest_documents(documents, vector_store, embed_model)

    logger.info("=" * 60)
    logger.info("Ingestion complete! You can now start the backend server.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
