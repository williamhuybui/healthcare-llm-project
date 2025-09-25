import os
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jService:
    def __init__(self, uri: str = None):
        self.uri = uri or os.getenv('NEO4j_URI')
        self.username = os.getenv('NEO4j_USERNAME')
        self.password = os.getenv('NEO4j_PASSWORD')
        self.driver = None
        
    def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"Failed to connect to Neo4j: {str(e)}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get comprehensive metadata about the Neo4j database"""
        if not self.driver:
            if not self.connect():
                return {"error": "Could not connect to database"}
        
        metadata = {}
        
        try:
            with self.driver.session() as session:
                # Database info
                metadata['database_info'] = self._get_database_info(session)
                
                # Node labels and counts
                metadata['node_labels'] = self._get_node_labels(session)
                
                # Relationship types and counts  
                metadata['relationship_types'] = self._get_relationship_types(session)
                
                # Indexes
                metadata['indexes'] = self._get_indexes(session)
                
                # Constraints
                metadata['constraints'] = self._get_constraints(session)
                
                # Database statistics
                metadata['statistics'] = self._get_statistics(session)
                
        except Exception as e:
            metadata['error'] = f"Error fetching metadata: {str(e)}"
        
        return metadata
    
    def _get_database_info(self, session) -> Dict[str, Any]:
        """Get basic database information"""
        try:
            result = session.run("CALL dbms.components()")
            components = []
            for record in result:
                components.append({
                    'name': record['name'],
                    'version': record['version'],
                    'edition': record['edition']
                })
            return {'components': components}
        except Exception:
            return {'components': []}
    
    def _get_node_labels(self, session) -> List[Dict[str, Any]]:
        """Get all node labels with counts"""
        labels = []
        try:
            # Get all labels
            result = session.run("CALL db.labels()")
            label_names = [record['label'] for record in result]
            
            # Get count for each label
            for label in label_names:
                count_result = session.run(f"MATCH (n:`{label}`) RETURN count(n) as count")
                count = count_result.single()['count']
                labels.append({
                    'label': label,
                    'count': count
                })
        except Exception as e:
            labels.append({'error': f"Error getting node labels: {str(e)}"})
        
        return labels
    
    def _get_relationship_types(self, session) -> List[Dict[str, Any]]:
        """Get all relationship types with counts"""
        relationships = []
        try:
            # Get all relationship types
            result = session.run("CALL db.relationshipTypes()")
            rel_types = [record['relationshipType'] for record in result]
            
            # Get count for each type
            for rel_type in rel_types:
                count_result = session.run(f"MATCH ()-[r:`{rel_type}`]-() RETURN count(r) as count")
                count = count_result.single()['count']
                relationships.append({
                    'type': rel_type,
                    'count': count
                })
        except Exception as e:
            relationships.append({'error': f"Error getting relationship types: {str(e)}"})
        
        return relationships
    
    def _get_indexes(self, session) -> List[Dict[str, Any]]:
        """Get all database indexes"""
        indexes = []
        try:
            result = session.run("SHOW INDEXES")
            for record in result:
                indexes.append({
                    'name': record.get('name'),
                    'labels': record.get('labelsOrTypes', []),
                    'properties': record.get('properties', []),
                    'type': record.get('type'),
                    'state': record.get('state')
                })
        except Exception as e:
            # Fallback for older Neo4j versions
            try:
                result = session.run("CALL db.indexes()")
                for record in result:
                    indexes.append({
                        'description': record.get('description'),
                        'state': record.get('state'),
                        'type': record.get('type')
                    })
            except Exception:
                indexes.append({'error': f"Error getting indexes: {str(e)}"})
        
        return indexes
    
    def _get_constraints(self, session) -> List[Dict[str, Any]]:
        """Get all database constraints"""
        constraints = []
        try:
            result = session.run("SHOW CONSTRAINTS")
            for record in result:
                constraints.append({
                    'name': record.get('name'),
                    'type': record.get('type'),
                    'labels': record.get('labelsOrTypes', []),
                    'properties': record.get('properties', [])
                })
        except Exception as e:
            # Fallback for older Neo4j versions
            try:
                result = session.run("CALL db.constraints()")
                for record in result:
                    constraints.append({
                        'description': record.get('description'),
                        'type': record.get('type')
                    })
            except Exception:
                constraints.append({'error': f"Error getting constraints: {str(e)}"})
        
        return constraints
    
    def _get_statistics(self, session) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        try:
            # Total nodes
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            stats['total_nodes'] = result.single()['total_nodes']
            
            # Total relationships
            result = session.run("MATCH ()-[r]-() RETURN count(r) as total_relationships")
            stats['total_relationships'] = result.single()['total_relationships']
            
            # Database size (if available)
            try:
                result = session.run("CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store file sizes') YIELD attributes RETURN attributes")
                store_info = result.single()
                if store_info:
                    stats['store_info'] = store_info['attributes']
            except Exception:
                pass
                
        except Exception as e:
            stats['error'] = f"Error getting statistics: {str(e)}"
        
        return stats

# Usage example
if __name__ == "__main__":
    service = Neo4jService()
    
    if service.connect():
        print("Connected to Neo4j successfully!")
        metadata = service.get_metadata()
        print("\nDatabase Metadata:")
        print("-" * 50)
        
        for key, value in metadata.items():
            print(f"\n{key.upper()}:")
            if isinstance(value, list):
                for item in value:
                    print(f"  {item}")
            elif isinstance(value, dict):
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"  {value}")
        
        service.close()
    else:
        print("Failed to connect to Neo4j database")