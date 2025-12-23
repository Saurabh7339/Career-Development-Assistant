"""
RAG Pipeline for Skill Gap Identification System
Handles document processing, embeddings, and retrieval
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter


class RAGPipeline:
    """RAG pipeline for processing and retrieving user profiles and skill documents"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize RAG pipeline with vector store and embeddings"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model (free, runs locally)
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded!")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )
        
        # Get or create collections
        self.profile_collection = self.client.get_or_create_collection(
            name="user_profiles",
            metadata={"description": "User profile documents"}
        )
        
        self.skill_framework_collection = self.client.get_or_create_collection(
            name="skill_frameworks",
            metadata={"description": "Skill framework and role requirement documents"}
        )
    
    def add_profile(self, profile_id: str, profile_text: str, metadata: Optional[Dict] = None):
        """Add a user profile to the vector store"""
        # Split text into chunks
        chunks = self.text_splitter.split_text(profile_text)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add to collection
        ids = [f"{profile_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
        
        self.profile_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        return len(chunks)
    
    def add_skill_framework(self, framework_id: str, framework_text: str, metadata: Optional[Dict] = None):
        """Add a skill framework document to the vector store"""
        chunks = self.text_splitter.split_text(framework_text)
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        if metadata is None:
            metadata = {}
        
        ids = [f"{framework_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
        
        self.skill_framework_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        return len(chunks)
    
    def retrieve_relevant_context(
        self, 
        query: str, 
        collection_name: str = "user_profiles",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query"""
        collection = self.profile_collection if collection_name == "user_profiles" else self.skill_framework_collection
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Search in collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        contexts = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i, doc in enumerate(results['documents'][0]):
                contexts.append({
                    "text": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        return contexts
    
    def get_profile_context(self, profile_id: str, query: str, top_k: int = 3) -> str:
        """Get relevant context from a specific profile"""
        # Use semantic search with profile_id filter
        try:
            # Try to get chunks with profile_id in metadata
            results = self.profile_collection.get(
                where={"profile_id": profile_id} if profile_id else None
            )
            
            if results and results.get('documents') and len(results['documents']) > 0:
                # Filter chunks by profile_id
                profile_chunks = [
                    (doc, meta) for doc, meta in zip(results['documents'], results.get('metadatas', []))
                    if meta and meta.get('profile_id') == profile_id
                ]
                
                if profile_chunks:
                    # Use semantic search within profile chunks
                    query_embedding = self.embedding_model.encode([query])[0].tolist()
                    chunk_embeddings = self.embedding_model.encode([doc for doc, _ in profile_chunks])
                    similarities = np.dot(chunk_embeddings, query_embedding)
                    top_indices = np.argsort(similarities)[-top_k:][::-1]
                    
                    return "\n\n".join([profile_chunks[i][0] for i in top_indices])
        except Exception as e:
            print(f"Error retrieving profile context: {e}")
        
        # Fallback to semantic search
        contexts = self.retrieve_relevant_context(query, "user_profiles", top_k)
        return "\n\n".join([ctx["text"] for ctx in contexts])
    
    def search_skill_frameworks(self, query: str, top_k: int = 5) -> str:
        """Search skill frameworks for relevant requirements"""
        contexts = self.retrieve_relevant_context(query, "skill_frameworks", top_k)
        return "\n\n".join([ctx["text"] for ctx in contexts])

