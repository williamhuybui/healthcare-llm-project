import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional

class SQLQueryAgent:
    def __init__(self, db_path="healthcare.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dictionaries"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            
            # Convert rows to dictionaries
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
                
            return results
            
        except Exception as e:
            print(f"Error executing query: {e}")
            return []
            
    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Get schema information for a table"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
        
    def list_tables(self) -> List[str]:
        """List all tables in the database"""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = self.execute_query(query)
        return [row['name'] for row in results]
        
    def describe_database(self) -> Dict[str, Any]:
        """Get comprehensive database information"""
        tables = self.list_tables()
        db_info = {}
        
        for table in tables:
            schema = self.get_table_schema(table)
            count_query = f"SELECT COUNT(*) as count FROM {table}"
            count_result = self.execute_query(count_query)
            record_count = count_result[0]['count'] if count_result else 0
            
            db_info[table] = {
                'columns': schema,
                'record_count': record_count
            }
            
        return db_info
        
    def find_doctors_by_specialty(self, specialty: str) -> List[Dict[str, Any]]:
        """Find doctors by specialty"""
        query = """
        SELECT doctor_id, doctor_name, specialty, facility_id, languages, 
               accepts_new_patients, phone, email
        FROM doctor 
        WHERE specialty LIKE ?
        """
        return self.execute_query(query.replace('?', f"'%{specialty}%'"))
        
    def find_users_by_location(self, city: str = None, state: str = None) -> List[Dict[str, Any]]:
        """Find users by location"""
        conditions = []
        if city:
            conditions.append(f"city LIKE '%{city}%'")
        if state:
            conditions.append(f"state = '{state}'")
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
        SELECT u.user_id, u.first_name, u.last_name, u.city, u.state, u.zip,
               p.plan_name, d.doctor_name
        FROM user u
        LEFT JOIN plan p ON u.plan_id = p.plan_id
        LEFT JOIN doctor d ON u.primary_doctor_id = d.doctor_id
        WHERE {where_clause}
        """
        return self.execute_query(query)
        
    def find_coverage_for_service(self, service_category: str, plan_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find coverage information for a specific service"""
        base_query = """
        SELECT c.coverage_id, c.plan_id, p.plan_name, c.service_category,
               c.copay, c.coinsurance_pct, c.prior_auth_required, 
               c.coverage_limit, c.notes
        FROM coverage c
        LEFT JOIN plan p ON c.plan_id = p.plan_id
        WHERE c.service_category LIKE ?
        """
        
        conditions = [f"'%{service_category}%'"]
        if plan_id:
            base_query += " AND c.plan_id = ?"
            conditions.append(str(plan_id))
            
        query = base_query.replace('?', conditions[0])
        if len(conditions) > 1:
            query = query.replace('?', conditions[1])
            
        return self.execute_query(query)
        
    def get_facilities_by_plan(self, plan_id: int) -> List[Dict[str, Any]]:
        """Get facilities that accept a specific plan"""
        query = f"""
        SELECT facility_id, facility_name, npi, address_line, city, state, zip, phone
        FROM facility
        WHERE accepts_plan_ids LIKE '%{plan_id}%'
        """
        return self.execute_query(query)
        
    def interactive_query(self):
        """Interactive query interface"""
        print("SQL Query Agent - Interactive Mode")
        print("Available commands:")
        print("  'tables' - List all tables")
        print("  'describe' - Show database schema")
        print("  'quit' - Exit")
        print("  Or enter any SQL query")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\nEnter command or SQL query: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'tables':
                    tables = self.list_tables()
                    print(f"Tables: {', '.join(tables)}")
                elif user_input.lower() == 'describe':
                    db_info = self.describe_database()
                    for table, info in db_info.items():
                        print(f"\nTable: {table} ({info['record_count']} records)")
                        for col in info['columns']:
                            print(f"  - {col['name']}: {col['type']}")
                else:
                    results = self.execute_query(user_input)
                    if results:
                        df = pd.DataFrame(results)
                        print(f"\nResults ({len(results)} rows):")
                        print(df.to_string(index=False))
                    else:
                        print("No results found or query error.")
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    agent = SQLQueryAgent()
    try:
        agent.interactive_query()
    finally:
        agent.close()