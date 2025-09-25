import sqlite3
import pandas as pd
from typing import Dict, List, Any
from pathlib import Path

class SQLTool:
    """Tool for executing SQL queries against the healthcare database."""
    
    def __init__(self, db_path: str = "healthcare.db"):
        """Initialize with database path."""
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def execute_query(self, query: str, description: str = "") -> Dict[str, Any]:
        """
        Execute SQL query and return structured results.
        
        Args:
            query: SQL query string
            description: Human readable description of query purpose
            
        Returns:
            Dictionary with results, metadata, and reference information
        """
        if not self.connection:
            if not self.connect():
                return {
                    "results": [],
                    "columns": [],
                    "row_count": 0,
                    "reference": "Database connection failed",
                    "error": "Could not connect to database"
                }
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            # Create reference string
            reference = f"SQL Query: {description if description else 'Database query'} ({len(results)} rows)"
            
            return {
                "results": results,
                "columns": columns,
                "row_count": len(results),
                "reference": reference,
                "query": query
            }
            
        except Exception as e:
            return {
                "results": [],
                "columns": [],
                "row_count": 0,
                "reference": f"SQL Error: {str(e)}",
                "error": str(e),
                "query": query
            }
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a specific table."""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query, f"Table schema for {table_name}")
    
    def list_tables(self) -> Dict[str, Any]:
        """List all tables in the database."""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        return self.execute_query(query, "List database tables")
    
    def search_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user profile data for a specific user."""
        query = f"""
        SELECT u.*, p.plan_name, p.plan_type, d.doctor_name 
        FROM user u
        LEFT JOIN plan p ON u.plan_id = p.plan_id  
        LEFT JOIN doctor d ON u.primary_doctor_id = d.doctor_id
        WHERE u.user_id = '{user_id}'
        """
        return self.execute_query(query, f"User profile for {user_id}")
    
    def search_plans(self, plan_id: str = None, plan_type: str = None) -> Dict[str, Any]:
        """Search insurance plans with optional filters."""
        query = "SELECT * FROM plan WHERE 1=1"
        conditions = []
        
        if plan_id:
            conditions.append(f"plan_id = {plan_id}")
        if plan_type:
            conditions.append(f"plan_type LIKE '%{plan_type}%'")
            
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        return self.execute_query(query, "Insurance plan search")
    
    def search_doctors(self, specialty: str = None, city: str = None, accepts_new: bool = None) -> Dict[str, Any]:
        """Search doctors with optional filters."""
        query = """
        SELECT d.*, f.facility_name, f.city, f.state 
        FROM doctor d
        LEFT JOIN facility f ON d.facility_id = f.facility_id
        WHERE 1=1
        """
        conditions = []
        
        if specialty:
            conditions.append(f"d.specialty LIKE '%{specialty}%'")
        if city:
            conditions.append(f"f.city LIKE '%{city}%'")
        if accepts_new is not None:
            conditions.append(f"d.accepts_new_patients = {accepts_new}")
            
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        return self.execute_query(query, f"Doctor search - specialty: {specialty}, city: {city}")
    
    def get_coverage_details(self, plan_id: str = None, service_category: str = None) -> Dict[str, Any]:
        """Get coverage details with optional filters."""
        query = "SELECT * FROM coverage WHERE 1=1"
        conditions = []
        
        if plan_id:
            conditions.append(f"plan_id = '{plan_id}'")
        if service_category:
            conditions.append(f"service_category LIKE '%{service_category}%'")
            
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        return self.execute_query(query, f"Coverage details - plan: {plan_id}, service: {service_category}")
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

# Tool function for LangChain integration
def sql_query_tool(query: str, description: str = "") -> Dict[str, Any]:
    """
    LangChain tool function for SQL queries.
    
    Args:
        query: SQL query to execute
        description: Description of what the query does
        
    Returns:
        Query results with metadata
    """
    tool = SQLTool()
    try:
        result = tool.execute_query(query, description)
        return result
    finally:
        tool.close()

if __name__ == "__main__":
    # Test the SQL tool
    tool = SQLTool()
    
    # Test connection and basic queries
    if tool.connect():
        print("✓ Database connected successfully")
        
        # List tables
        tables = tool.list_tables()
        print(f"Tables: {[result['name'] for result in tables['results']]}")
        
        # Test user search
        user_data = tool.search_user_data("101")
        print(f"User 101: {user_data}")
        
        tool.close()
    else:
        print("✗ Database connection failed")