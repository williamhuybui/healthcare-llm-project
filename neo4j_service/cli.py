#!/usr/bin/env python3
import sys
from graph_rag import HealthcareGraphRAG

def main():
    """
    Interactive CLI for the Healthcare GraphRAG system
    """
    print("🏥 Healthcare Adverse Drug Reaction GraphRAG System")
    print("=" * 60)
    
    # Initialize the system
    try:
        rag = HealthcareGraphRAG()
        print("✅ System initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize system: {str(e)}")
        return
    
    # Show database summary
    print("\n" + rag.get_database_summary())
    
    print("\n💡 Example Questions:")
    for i, question in enumerate(rag.suggest_questions()[:5], 1):
        print(f"   {i}. {question}")
    
    print(f"\n{'='*60}")
    print("Ask questions about adverse drug reactions (type 'quit' to exit)")
    print(f"{'='*60}")
    
    try:
        while True:
            print("\n❓ Your question:")
            question = input("> ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if question.lower() in ['help', 'h']:
                print("\n💡 Suggested Questions:")
                for i, q in enumerate(rag.suggest_questions(), 1):
                    print(f"   {i}. {q}")
                continue
            
            if question.lower() == 'summary':
                print(rag.get_database_summary())
                continue
            
            print(f"\n🔍 Analyzing: {question}")
            print("-" * 40)
            
            result = rag.query(question)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"💬 Answer: {result['answer']}")
                
                if result.get('cypher_query'):
                    print(f"\n🔧 Generated Query:")
                    print(f"   {result['cypher_query']}")
                
                if result.get('raw_results') and len(result['raw_results']) > 0:
                    print(f"\n📊 Raw Results: {len(result['raw_results'])} records found")
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
    finally:
        rag.close()

if __name__ == "__main__":
    main()