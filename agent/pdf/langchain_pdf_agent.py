import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from langchain_community.document_loaders import UnstructuredPDFLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import chromadb

class LangChainPDFAgent:
    def __init__(self, storage_dir="pdf_data_storage", db_path="healthcare_pdf.db"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.setup_database()
        
        # Initialize embeddings and vector store
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Initialize vector stores
        self.vector_store_path = self.storage_dir / "vector_store"
        self.chroma_path = self.storage_dir / "chroma_db"
        
        self.processed_files = {}
        
    def setup_database(self):
        """Create database tables for storing PDF data"""
        cursor = self.conn.cursor()
        
        # Main documents table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER,
            num_pages INTEGER,
            extraction_date TIMESTAMP,
            document_type TEXT,
            metadata TEXT
        )
        ''')
        
        # Text chunks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS text_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            chunk_index INTEGER,
            content TEXT NOT NULL,
            chunk_metadata TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
        ''')
        
        # Extracted entities table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS extracted_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            entity_type TEXT,
            entity_value TEXT,
            confidence REAL,
            context TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
        ''')
        
        # Healthcare plan data
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            plan_name TEXT,
            plan_type TEXT,
            premium_monthly REAL,
            deductible REAL,
            oop_maximum REAL,
            coverage_period TEXT,
            network_type TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
        ''')
        
        # Coverage benefits
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS coverage_benefits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            service_category TEXT,
            copay REAL,
            coinsurance_pct REAL,
            deductible_applies BOOLEAN,
            prior_auth_required BOOLEAN,
            coverage_limit TEXT,
            notes TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
        ''')
        
        self.conn.commit()
        
    def extract_pdf_comprehensive(self, pdf_path: str) -> Dict[str, Any]:
        """Comprehensive PDF extraction using multiple LangChain loaders"""
        pdf_path = str(Path(pdf_path).resolve())
        
        print(f"Processing PDF: {pdf_path}")
        
        # Try multiple extraction methods
        documents = []
        extraction_methods = []
        
        # Method 1: UnstructuredPDFLoader (best for complex layouts)
        try:
            loader = UnstructuredPDFLoader(pdf_path, mode="elements")
            docs = loader.load()
            documents.extend(docs)
            extraction_methods.append("UnstructuredPDF")
            print(f"✓ UnstructuredPDFLoader: {len(docs)} elements")
        except Exception as e:
            print(f"✗ UnstructuredPDFLoader failed: {e}")
        
        # Method 2: PyPDFLoader (fallback)
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            if not documents:  # Only use if unstructured failed
                documents.extend(docs)
                extraction_methods.append("PyPDF")
            print(f"✓ PyPDFLoader: {len(docs)} pages")
        except Exception as e:
            print(f"✗ PyPDFLoader failed: {e}")
        
        if not documents:
            raise ValueError("All PDF extraction methods failed")
        
        # Get file metadata
        file_stat = os.stat(pdf_path)
        file_metadata = {
            'file_path': pdf_path,
            'file_name': Path(pdf_path).name,
            'file_size': file_stat.st_size,
            'extraction_methods': extraction_methods,
            'extraction_date': datetime.now().isoformat(),
            'num_documents': len(documents)
        }
        
        return {
            'documents': documents,
            'metadata': file_metadata,
            'raw_content': self._combine_document_content(documents)
        }
    
    def _combine_document_content(self, documents: List[Document]) -> str:
        """Combine all document content into a single string"""
        return "\n\n".join([doc.page_content for doc in documents])
    
    def process_and_store_pdf(self, pdf_path: str) -> int:
        """Complete processing pipeline for PDF"""
        
        # Extract PDF content
        extraction_result = self.extract_pdf_comprehensive(pdf_path)
        documents = extraction_result['documents']
        metadata = extraction_result['metadata']
        raw_content = extraction_result['raw_content']
        
        # Store document metadata in database
        document_id = self._store_document_metadata(metadata, len(documents))
        
        # Create text chunks
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} text chunks")
        
        # Store chunks in database
        self._store_text_chunks(document_id, chunks)
        
        # Extract healthcare-specific data
        healthcare_data = self._extract_healthcare_data(raw_content)
        self._store_healthcare_data(document_id, healthcare_data)
        
        # Create and store vector embeddings
        self._create_vector_store(document_id, chunks, metadata['file_name'])
        
        # Store processing results
        self.processed_files[pdf_path] = {
            'document_id': document_id,
            'chunks': len(chunks),
            'healthcare_data': healthcare_data,
            'metadata': metadata
        }
        
        print(f"✓ Successfully processed and stored PDF (Document ID: {document_id})")
        return document_id
    
    def _store_document_metadata(self, metadata: Dict, num_pages: int) -> int:
        """Store document metadata in database"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO documents 
        (file_path, file_name, file_size, num_pages, extraction_date, document_type, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata['file_path'],
            metadata['file_name'],
            metadata['file_size'],
            num_pages,
            metadata['extraction_date'],
            'healthcare_plan',
            json.dumps(metadata)
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def _store_text_chunks(self, document_id: int, chunks: List[Document]):
        """Store text chunks in database"""
        cursor = self.conn.cursor()
        for i, chunk in enumerate(chunks):
            cursor.execute('''
            INSERT INTO text_chunks (document_id, chunk_index, content, chunk_metadata)
            VALUES (?, ?, ?, ?)
            ''', (
                document_id,
                i,
                chunk.page_content,
                json.dumps(chunk.metadata)
            ))
        self.conn.commit()
    
    def _extract_healthcare_data(self, content: str) -> Dict[str, Any]:
        """Extract healthcare-specific information from content"""
        import re
        
        healthcare_data = {
            'plan_info': {},
            'benefits': [],
            'costs': {},
            'network_info': {}
        }
        
        # Extract plan information
        plan_patterns = {
            'plan_name': [
                r'Plan Name[:\s]*([^\n]+)',
                r'Coverage[:\s]*([^\n]+)',
                r'Blue\s+\w+.*?(?:HMO|PPO|EPO)',
            ],
            'plan_type': [
                r'\b(HMO|PPO|EPO|POS)\b',
            ],
            'coverage_period': [
                r'Coverage Period[:\s]*([^\n]+)',
                r'(\d{1,2}/\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{1,2}/\d{4})',
            ],
            'network': [
                r'Network[:\s]*([^\n]+)',
            ]
        }
        
        for key, patterns in plan_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    healthcare_data['plan_info'][key] = match.group(1).strip()
                    break
        
        # Extract cost information
        cost_patterns = {
            'premium': [
                r'Premium[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*per month',
            ],
            'deductible': [
                r'Deductible[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'Annual Deductible[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            ],
            'oop_maximum': [
                r'Out.of.pocket maximum[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'Maximum out.of.pocket[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            ]
        }
        
        for key, patterns in cost_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value_str = match.group(1).replace(',', '')
                    try:
                        healthcare_data['costs'][key] = float(value_str)
                    except ValueError:
                        healthcare_data['costs'][key] = value_str
                    break
        
        # Extract benefits using more comprehensive patterns
        benefit_patterns = [
            r'(Primary Care|Specialist|Emergency|Urgent Care|Hospital|Prescription|Mental Health|Vision|Dental)[^$]*?\$(\d+)',
            r'([A-Za-z\s]+(?:Visit|Care|Service|Treatment))[^$]*?\$(\d+)',
        ]
        
        for pattern in benefit_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for service, cost in matches:
                healthcare_data['benefits'].append({
                    'service': service.strip(),
                    'cost': f"${cost}",
                    'type': 'copay'
                })
        
        return healthcare_data
    
    def _store_healthcare_data(self, document_id: int, healthcare_data: Dict[str, Any]):
        """Store extracted healthcare data"""
        cursor = self.conn.cursor()
        
        # Store plan data
        plan_info = healthcare_data.get('plan_info', {})
        costs = healthcare_data.get('costs', {})
        
        cursor.execute('''
        INSERT INTO plan_data 
        (document_id, plan_name, plan_type, premium_monthly, deductible, oop_maximum, coverage_period, network_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            document_id,
            plan_info.get('plan_name'),
            plan_info.get('plan_type'),
            costs.get('premium'),
            costs.get('deductible'),
            costs.get('oop_maximum'),
            plan_info.get('coverage_period'),
            plan_info.get('network')
        ))
        
        # Store benefits
        for benefit in healthcare_data.get('benefits', []):
            cursor.execute('''
            INSERT INTO coverage_benefits 
            (document_id, service_category, notes)
            VALUES (?, ?, ?)
            ''', (
                document_id,
                benefit.get('service'),
                f"{benefit.get('type', '')}: {benefit.get('cost', '')}"
            ))
        
        self.conn.commit()
    
    def _create_vector_store(self, document_id: int, chunks: List[Document], file_name: str):
        """Create and store vector embeddings"""
        if not chunks:
            return
        
        try:
            # Create FAISS vector store
            texts = [chunk.page_content for chunk in chunks]
            metadatas = [{'document_id': document_id, 'chunk_id': i, 'source': file_name} 
                        for i, chunk in enumerate(chunks)]
            
            vector_store = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            
            # Save FAISS index
            faiss_path = self.storage_dir / f"faiss_{document_id}"
            vector_store.save_local(str(faiss_path))
            
            print(f"✓ Created FAISS vector store: {faiss_path}")
            
        except Exception as e:
            print(f"✗ Error creating vector store: {e}")
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search across all processed documents"""
        results = []
        
        # Search in all FAISS indexes
        for faiss_dir in self.storage_dir.glob("faiss_*"):
            try:
                vector_store = FAISS.load_local(
                    str(faiss_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                docs = vector_store.similarity_search(query, k=top_k)
                
                for doc in docs:
                    results.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'source': faiss_dir.name
                    })
            except Exception as e:
                print(f"Error searching {faiss_dir}: {e}")
        
        return results[:top_k]
    
    def get_document_summary(self, document_id: int) -> Dict[str, Any]:
        """Get comprehensive summary of a processed document"""
        cursor = self.conn.cursor()
        
        # Get document metadata
        cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
        doc_info = cursor.fetchone()
        
        if not doc_info:
            return {}
        
        # Get plan data
        cursor.execute('SELECT * FROM plan_data WHERE document_id = ?', (document_id,))
        plan_data = cursor.fetchone()
        
        # Get benefits
        cursor.execute('SELECT * FROM coverage_benefits WHERE document_id = ?', (document_id,))
        benefits = cursor.fetchall()
        
        # Get chunks count
        cursor.execute('SELECT COUNT(*) FROM text_chunks WHERE document_id = ?', (document_id,))
        chunks_count = cursor.fetchone()[0]
        
        return {
            'document_info': dict(zip([col[0] for col in cursor.description], doc_info)) if doc_info else None,
            'plan_data': dict(zip([col[0] for col in cursor.description], plan_data)) if plan_data else None,
            'benefits': [dict(zip([col[0] for col in cursor.description], benefit)) for benefit in benefits],
            'chunks_count': chunks_count
        }
    
    def export_all_data(self, output_dir: str = "exported_data"):
        """Export all processed data to CSV files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        tables = ['documents', 'plan_data', 'coverage_benefits', 'text_chunks']
        
        for table in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
            csv_path = output_path / f"{table}.csv"
            df.to_csv(csv_path, index=False)
            print(f"Exported {len(df)} records to {csv_path}")
    
    def close(self):
        """Clean up resources"""
        self.conn.close()

if __name__ == "__main__":
    agent = LangChainPDFAgent()
    
    try:
        # Process the healthcare PDF
        pdf_path = "data/plans_pdf/blue_advantage_gold_hmo_standard.pdf"
        
        if Path(pdf_path).exists():
            document_id = agent.process_and_store_pdf(pdf_path)
            
            # Get and display summary
            summary = agent.get_document_summary(document_id)
            print("\n=== DOCUMENT SUMMARY ===")
            print(json.dumps(summary, indent=2, default=str))
            
            # Export data
            agent.export_all_data()
            
            # Test search functionality
            print("\n=== SEARCH TEST ===")
            search_results = agent.search_documents("premium deductible", top_k=3)
            for i, result in enumerate(search_results, 1):
                print(f"\nResult {i}:")
                print(f"Content: {result['content'][:200]}...")
                print(f"Source: {result['source']}")
                
        else:
            print(f"PDF not found: {pdf_path}")
            
    finally:
        agent.close()