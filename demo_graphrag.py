#!/usr/bin/env python3

from neo4j_service import HealthcareGraphRAG

def demo_healthcare_graphrag():
    """
    Demonstration of the Healthcare GraphRAG system
    """
    print("🏥 Healthcare Adverse Drug Reaction GraphRAG Demo")
    print("=" * 60)
    
    # Initialize the system
    rag = HealthcareGraphRAG()
    
    # Show database summary
    print(rag.get_database_summary())
    
    # Demo questions
    demo_questions = [
        "What are the top 5 most common adverse reactions?",
        "Which drugs have the most adverse reaction reports?", 
        "What's the gender distribution in adverse reaction cases?",
        "Show me reactions most common in patients over 65",
        "Which manufacturers have the most reported adverse reactions?"
    ]
    
    print("\n🔍 Demo Questions and Answers:")
    print("=" * 60)
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 50)
        
        result = rag.query(question)
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
        else:
            print(f"💬 Answer: {result['answer']}")
            if result.get('cypher_query'):
                print(f"🔧 Generated Cypher: {result['cypher_query']}")
        
        print()
    
    rag.close()
    print("✅ Demo completed!")

if __name__ == "__main__":
    demo_healthcare_graphrag()