"""
Document Ingestion Script
Ingests PDF documents into Milvus vector store for RAG retrieval
"""
import os
# Disable hf_transfer before any other imports
os.environ.pop('HF_HUB_ENABLE_HF_TRANSFER', None)

import argparse
import logging
from pathlib import Path
from typing import List
import sys

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
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


def get_pdf_files(directory: str) -> List[Path]:
    """Get list of PDF files in directory"""
    try:
        logger.info(f"Scanning for PDF files in {directory}...")

        # Check if directory exists
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory}")
            sys.exit(1)

        # Get PDF files
        pdf_files = list(dir_path.glob("**/*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files")
        return pdf_files

    except Exception as e:
        logger.error(f"Failed to scan directory: {e}")
        sys.exit(1)


def load_single_pdf(pdf_path: Path) -> List:
    """Load a single PDF file"""
    try:
        reader = SimpleDirectoryReader(
            input_files=[str(pdf_path)]
        )
        documents = reader.load_data()
        return documents
    except Exception as e:
        logger.warning(f"Failed to load {pdf_path.name}: {e}")
        return []


def setup_embedding_model():
    """Setup embedding model using sentence-transformers (GPU-accelerated)"""
    try:
        logger.info("Configuring embeddings via sentence-transformers (GPU-accelerated)")
        embed_model = HuggingFaceEmbedding(
            model_name="all-MiniLM-L6-v2",  # Fast, lightweight embedding model
            device="cuda"  # Use GPU for fast embeddings
        )
        logger.info("✓ Embedding model configured (sentence-transformers on GPU)")
        return embed_model
    except Exception as e:
        logger.error(f"Failed to configure embedding model: {e}")
        import traceback
        traceback.print_exc()
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


def ingest_pdf_file(pdf_path: Path, vector_store, embed_model, node_parser, index):
    """Ingest a single PDF file"""
    try:
        logger.info(f"Processing: {pdf_path.name}")

        # Load this PDF
        documents = load_single_pdf(pdf_path)
        if not documents:
            logger.warning(f"  Skipping {pdf_path.name} (no documents loaded)")
            return 0

        logger.info(f"  Loaded {len(documents)} pages")

        # Parse into chunks
        nodes = node_parser.get_nodes_from_documents(documents)
        logger.info(f"  Created {len(nodes)} chunks")

        # Insert nodes (with progress tracking)
        for i, node in enumerate(nodes, 1):
            if i % 50 == 0:
                logger.info(f"  Progress: {i}/{len(nodes)} chunks")
            index.insert_nodes([node])

        logger.info(f"  ✓ Completed {pdf_path.name}: {len(nodes)} chunks ingested")
        return len(nodes)

    except Exception as e:
        logger.error(f"  Failed to ingest {pdf_path.name}: {e}")
        return 0


def ingest_documents_incremental(pdf_files: List[Path], vector_store, embed_model):
    """Ingest documents one PDF at a time to conserve memory"""
    try:
        logger.info("Starting incremental document ingestion...")
        logger.info(f"Chunk size: {settings.chunk_size}, Overlap: {settings.chunk_overlap}")
        logger.info(f"Total PDFs to process: {len(pdf_files)}")

        # Configure Settings
        Settings.embed_model = embed_model
        Settings.chunk_size = settings.chunk_size
        Settings.chunk_overlap = settings.chunk_overlap

        # Create node parser (reused for all PDFs)
        node_parser = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

        # Create index
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

        # Process each PDF one at a time
        total_chunks = 0
        successful_pdfs = 0

        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"\n[{i}/{len(pdf_files)}] Processing PDF...")
            chunks = ingest_pdf_file(pdf_path, vector_store, embed_model, node_parser, index)

            if chunks > 0:
                total_chunks += chunks
                successful_pdfs += 1

        logger.info("\n" + "=" * 60)
        logger.info("✓ Document ingestion complete!")
        logger.info(f"Successful PDFs: {successful_pdfs}/{len(pdf_files)}")
        logger.info(f"Total chunks: {total_chunks}")
        logger.info(f"Collection: {settings.chroma_collection_name}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to ingest documents: {e}")
        import traceback
        traceback.print_exc()
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
    logger.info("AI Mentor - Document Ingestion (Memory-Efficient)")
    logger.info("=" * 60)

    # Step 1: Prepare ChromaDB
    prepare_chromadb()

    # Step 2: Get list of PDF files
    pdf_files = get_pdf_files(args.directory)
    if not pdf_files:
        logger.warning("No PDF files to ingest")
        sys.exit(0)

    # Step 3: Setup embedding model
    embed_model = setup_embedding_model()

    # Step 4: Create vector store
    vector_store = create_vector_store(overwrite=args.overwrite)

    # Step 5: Ingest documents incrementally (one PDF at a time)
    ingest_documents_incremental(pdf_files, vector_store, embed_model)

    logger.info("\nIngestion complete! You can now start the backend server.")


if __name__ == "__main__":
    main()
