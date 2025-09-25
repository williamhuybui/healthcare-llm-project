import os
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from dotenv import load_dotenv
from service import Neo4jService

load_dotenv()

class HealthcareGraphRAG:
    def __init__(self):
        self.neo4j_service = Neo4jService()
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.graph = None
        self.qa_chain = None
        self._setup_graph()
        self._setup_qa_chain()
    
    def _setup_graph(self):
        """Initialize the Neo4j graph connection for LangChain"""
        try:
            self.graph = Neo4jGraph(
                url=os.getenv('NEO4j_URI'),
                username=os.getenv('NEO4j_USERNAME'),
                password=os.getenv('NEO4j_PASSWORD')
            )
            print("Neo4j graph connection established for LangChain")
        except Exception as e:
            print(f"Failed to setup graph connection: {str(e)}")
    
    def _setup_qa_chain(self):
        """Setup the GraphRAG QA chain"""
        if not self.graph:
            return
        
        # Create enhanced Cypher generation prompt
        cypher_prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a Neo4j Cypher expert for a healthcare adverse drug reaction database.

Database Schema:
- AgeGroup (5 nodes): Contains age group classifications
- Case (4,307 nodes): Adverse drug reaction case reports with properties: id, primaryid, age, ageUnit, gender, eventDate, reportDate
- Drug (2,500 nodes): Medications with properties: id, name
- Manufacturer (136 nodes): Drug manufacturers with properties: id, manufacturerName
- Outcome (6 nodes): Case outcomes with properties: id, code
- Reaction (2,701 nodes): Adverse reactions with properties: id, description
- ReportSource (5 nodes): Sources of reports with properties: id, code
- Therapy (1,721 nodes): Therapy information with properties: id, primaryid

Key Relationships:
- FALLS_UNDER: Cases fall under age groups
- HAS_REACTION: Cases have adverse reactions
- IS_CONCOMITANT: Drug interactions/concomitant medications
- IS_INTERACTING: Drug interactions (rare)
- IS_PRIMARY_SUSPECT: Primary suspected drugs
- IS_SECONDARY_SUSPECT: Secondary suspected drugs
- PRESCRIBED: Drug prescriptions
- RECEIVED: Drug receipts
- REGISTERED: Case registrations
- REPORTED_BY: Report sources
- RESULTED_IN: Case outcomes

Guidelines:
1. Always use MATCH patterns instead of complex JOINs
2. Use LIMIT for large result sets (default 10-20 unless asked for more)
3. For drug names, use case-insensitive matching: toLower(d.name) CONTAINS toLower('drug_name')
4. For reactions, use case-insensitive matching: toLower(r.description) CONTAINS toLower('reaction')
5. Always return meaningful labels and aggregate data when possible
6. Use COUNT, SUM, AVG for statistical queries
7. Order results by relevance (count, date, etc.)

Examples:
- To find cases with a specific reaction: MATCH (c:Case)-[:HAS_REACTION]->(r:Reaction) WHERE toLower(r.description) CONTAINS toLower('headache') RETURN c, r LIMIT 10
- To find drugs and their reaction counts: MATCH (d:Drug)<-[:IS_PRIMARY_SUSPECT]-(c:Case)-[:HAS_REACTION]->(r:Reaction) RETURN d.name, COUNT(r) as reaction_count ORDER BY reaction_count DESC LIMIT 10
- To analyze by age/gender: MATCH (c:Case) RETURN c.gender, AVG(c.age) as avg_age, COUNT(c) as case_count

Generate only the Cypher query without explanation.
            """),
            ("human", "{question}")
        ])
        
        try:
            self.qa_chain = GraphCypherQAChain.from_llm(
                llm=self.llm,
                graph=self.graph,
                verbose=True,
                cypher_prompt=cypher_prompt,
                return_intermediate_steps=True,
                top_k=20,
                allow_dangerous_requests=True
            )
            print("GraphRAG QA chain setup complete")
        except Exception as e:
            print(f"Failed to setup QA chain: {str(e)}")
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the graph database and return comprehensive results
        """
        if not self.qa_chain:
            return {"error": "QA chain not initialized"}
        
        try:
            # Get the full response with intermediate steps
            response = self.qa_chain.invoke({"query": question})
            
            result = {
                "question": question,
                "answer": response.get("result", "No answer generated"),
                "cypher_query": None,
                "raw_results": None
            }
            
            # Extract intermediate steps if available
            if "intermediate_steps" in response:
                steps = response["intermediate_steps"]
                if steps and len(steps) > 0:
                    result["cypher_query"] = steps[0].get("query", "No query generated")
                    result["raw_results"] = steps[0].get("context", [])
            
            return result
            
        except Exception as e:
            return {
                "question": question,
                "error": f"Query failed: {str(e)}",
                "answer": "I apologize, but I encountered an error while processing your question."
            }
    
    def get_database_summary(self) -> str:
        """Get a summary of the database for context"""
        summary = """
Healthcare Adverse Drug Reaction Database Summary:

This database contains 11,381 nodes and 119,356 relationships tracking adverse drug reactions:

📊 Data Overview:
• 4,307 adverse reaction cases
• 2,500 different drugs
• 2,701 types of adverse reactions
• 136 pharmaceutical manufacturers
• 1,721 therapy records

🔗 Key Relationships:
• 42,138 case-reaction links
• 16,784 concomitant drug relationships
• 7,660 primary suspect drug cases
• 7,232 secondary suspect drug cases
• 8,922 case outcomes

📈 Common Query Types:
1. Drug safety profiles: "What are the most common reactions to [drug name]?"
2. Reaction patterns: "Which drugs most commonly cause [reaction]?"
3. Demographics: "How do reactions vary by age/gender?"
4. Manufacturers: "What reactions are associated with drugs from [manufacturer]?"
5. Trends: "What are the most reported adverse reactions?"
        """
        return summary
    
    def suggest_questions(self) -> List[str]:
        """Suggest example questions users can ask"""
        return [
            "What are the most commonly reported adverse reactions?",
            "Which drugs have the highest number of adverse reaction reports?",
            "What reactions are most common in elderly patients?",
            "Show me the top manufacturers by number of adverse reaction cases",
            "What are the most serious outcomes reported?",
            "Which drugs are most often primary suspects in adverse reactions?",
            "What's the gender distribution of adverse reaction cases?",
            "What reactions are associated with cardiovascular drugs?",
            "Show me concomitant drug patterns in adverse reactions",
            "What's the average age of patients experiencing adverse reactions?"
        ]
    
    def close(self):
        """Close database connections"""
        if self.neo4j_service:
            self.neo4j_service.close()

# Convenience function for quick queries
def ask_question(question: str) -> Dict[str, Any]:
    """
    Quick function to ask a question about the healthcare data
    """
    rag = HealthcareGraphRAG()
    try:
        result = rag.query(question)
        return result
    finally:
        rag.close()

if __name__ == "__main__":
    # Example usage
    rag = HealthcareGraphRAG()
    
    print("Healthcare GraphRAG System Initialized")
    print("=" * 50)
    print(rag.get_database_summary())
    print("\nSuggested Questions:")
    for i, q in enumerate(rag.suggest_questions(), 1):
        print(f"{i}. {q}")
    
    print("\n" + "=" * 50)
    print("Testing with sample questions...")
    
    # Test queries
    sample_questions = [
        "What are the top 5 most commonly reported adverse reactions?",
        "Which drugs have the most adverse reaction reports?"
    ]
    
    for question in sample_questions:
        print(f"\nQ: {question}")
        result = rag.query(question)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"A: {result['answer']}")
            if result.get('cypher_query'):
                print(f"Cypher: {result['cypher_query']}")
    
    rag.close()