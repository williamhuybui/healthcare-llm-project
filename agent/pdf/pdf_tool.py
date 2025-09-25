import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any
import re

class PDFTool:
    """Tool for searching PDF documents and extracted content."""
    
    def __init__(self, pdf_db_path: str = "comprehensive_healthcare.db"):
        """Initialize with PDF database path."""
        self.pdf_db_path = pdf_db_path
        self.connection = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.pdf_db_path)
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"PDF database connection failed: {e}")
            return False
    
    def search_documents(self, keywords: str, document_type: str = "all", max_results: int = 5) -> Dict[str, Any]:
        """
        Search PDF content for keywords.
        
        Args:
            keywords: Keywords to search for
            document_type: Type of document to search (plan_summary, coverage, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results and references
        """
        if not self.connection:
            if not self.connect():
                return {
                    "snippets": [],
                    "sources": [],
                    "page_numbers": [],
                    "reference": "PDF database connection failed",
                    "error": "Could not connect to PDF database"
                }
        
        try:
            # Search in document content
            content_results = self._search_document_content(keywords, max_results)
            
            # Search in plan data
            plan_results = self._search_plan_data(keywords)
            
            # Search in coverage details  
            coverage_results = self._search_coverage_details(keywords, max_results)
            
            # Combine results
            all_snippets = []
            all_sources = []
            all_pages = []
            
            # Add content results
            for result in content_results:
                all_snippets.append(result.get('content', '')[:500] + "...")
                all_sources.append(f"Document Page {result.get('page_number', 'Unknown')}")
                all_pages.append(result.get('page_number', 0))
            
            # Add plan data results
            for result in plan_results:
                snippet = f"Plan: {result.get('plan_name', 'Unknown')} - Type: {result.get('plan_type', 'N/A')}"
                if result.get('premium_monthly'):
                    snippet += f" - Premium: ${result.get('premium_monthly')}/month"
                if result.get('deductible_individual'):
                    snippet += f" - Deductible: ${result.get('deductible_individual')}"
                all_snippets.append(snippet)
                all_sources.append("Plan Database")
                all_pages.append(0)
            
            # Add coverage results
            for result in coverage_results:
                snippet = f"Service: {result.get('service_category', 'Unknown')}"
                if result.get('copay'):
                    snippet += f" - Copay: ${result.get('copay')}"
                if result.get('coinsurance_pct'):
                    snippet += f" - Coinsurance: {result.get('coinsurance_pct')}%"
                if result.get('notes'):
                    snippet += f" - {result.get('notes')[:100]}"
                all_snippets.append(snippet)
                all_sources.append("Coverage Database")
                all_pages.append(result.get('page_reference', 0))
            
            # Limit results
            all_snippets = all_snippets[:max_results]
            all_sources = all_sources[:max_results]  
            all_pages = all_pages[:max_results]
            
            reference = f"PDF Search: '{keywords}' ({len(all_snippets)} results found)"
            
            return {
                "snippets": all_snippets,
                "sources": all_sources,
                "page_numbers": all_pages,
                "reference": reference,
                "keywords": keywords
            }
            
        except Exception as e:
            return {
                "snippets": [],
                "sources": [],
                "page_numbers": [],
                "reference": f"PDF Search Error: {str(e)}",
                "error": str(e),
                "keywords": keywords
            }
    
    def _search_document_content(self, keywords: str, max_results: int) -> List[Dict]:
        """Search in document content table."""
        cursor = self.connection.cursor()
        
        # Build search query with LIKE for each keyword
        keywords_list = keywords.split()
        where_conditions = []
        for keyword in keywords_list:
            where_conditions.append(f"raw_text LIKE '%{keyword}%'")
        where_clause = " OR ".join(where_conditions)
        
        query = f"""
        SELECT page_number, raw_text as content, document_id
        FROM document_content 
        WHERE {where_clause}
        ORDER BY page_number
        LIMIT {max_results}
        """
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def _search_plan_data(self, keywords: str) -> List[Dict]:
        """Search in plan data."""
        cursor = self.connection.cursor()
        
        keywords_list = keywords.split()
        where_conditions = []
        for keyword in keywords_list:
            where_conditions.extend([
                f"plan_name LIKE '%{keyword}%'",
                f"plan_type LIKE '%{keyword}%'",
                f"network_type LIKE '%{keyword}%'"
            ])
        where_clause = " OR ".join(where_conditions)
        
        query = f"""
        SELECT plan_name, plan_type, premium_monthly, deductible_individual, 
               oop_max_individual, network_type, coverage_period
        FROM plan_details 
        WHERE {where_clause}
        LIMIT 3
        """
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def _search_coverage_details(self, keywords: str, max_results: int) -> List[Dict]:
        """Search in coverage details."""
        cursor = self.connection.cursor()
        
        keywords_list = keywords.split()
        where_conditions = []
        for keyword in keywords_list:
            where_conditions.extend([
                f"service_category LIKE '%{keyword}%'",
                f"service_subcategory LIKE '%{keyword}%'",
                f"notes LIKE '%{keyword}%'"
            ])
        where_clause = " OR ".join(where_conditions)
        
        query = f"""
        SELECT service_category, service_subcategory, copay, coinsurance_pct, 
               notes, page_reference
        FROM coverage_details 
        WHERE {where_clause}
        ORDER BY service_category
        LIMIT {max_results}
        """
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_document_summary(self, document_id: int = None) -> Dict[str, Any]:
        """Get summary of document content."""
        if not self.connection:
            if not self.connect():
                return {"error": "Database connection failed"}
        
        try:
            cursor = self.connection.cursor()
            
            if document_id:
                query = """
                SELECT d.file_name, d.num_pages, d.extraction_date,
                       COUNT(dc.id) as content_pages,
                       COUNT(et.id) as tables_count
                FROM documents d
                LEFT JOIN document_content dc ON d.id = dc.document_id
                LEFT JOIN extracted_tables et ON d.id = et.document_id
                WHERE d.id = ?
                GROUP BY d.id
                """
                cursor.execute(query, (document_id,))
            else:
                query = """
                SELECT d.file_name, d.num_pages, d.extraction_date,
                       COUNT(dc.id) as content_pages,
                       COUNT(et.id) as tables_count
                FROM documents d
                LEFT JOIN document_content dc ON d.id = dc.document_id
                LEFT JOIN extracted_tables et ON d.id = et.document_id
                GROUP BY d.id
                LIMIT 5
                """
                cursor.execute(query)
            
            results = [dict(row) for row in cursor.fetchall()]
            
            return {
                "documents": results,
                "reference": f"Document summary ({len(results)} documents)"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "reference": f"Document summary error: {str(e)}"
            }
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

# Tool function for LangChain integration
def pdf_search_tool(keywords: str, document_type: str = "all", max_results: int = 5) -> Dict[str, Any]:
    """
    LangChain tool function for PDF search.
    
    Args:
        keywords: Keywords to search for
        document_type: Type of document to search
        max_results: Maximum results to return
        
    Returns:
        Search results with snippets and references
    """
    tool = PDFTool()
    try:
        result = tool.search_documents(keywords, document_type, max_results)
        return result
    finally:
        tool.close()

if __name__ == "__main__":
    # Test the PDF tool
    tool = PDFTool()
    
    if tool.connect():
        print("✓ PDF database connected successfully")
        
        # Test document summary
        summary = tool.get_document_summary()
        print(f"Documents: {summary}")
        
        # Test search
        search_results = tool.search_documents("premium deductible", max_results=3)
        print(f"Search results: {len(search_results.get('snippets', []))} found")
        for i, snippet in enumerate(search_results.get('snippets', [])):
            print(f"{i+1}. {snippet[:100]}...")
        
        tool.close()
    else:
        print("✗ PDF database connection failed")