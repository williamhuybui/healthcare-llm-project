#!/usr/bin/env python3
"""
Test script to demonstrate the complete Healthcare AI Assistant functionality
"""

import os
import sqlite3
from agent.graph import HealthcareAgent

def test_database():
    """Test database connection and data"""
    print("=== Testing Database ===")
    try:
        conn = sqlite3.connect('healthcare.db')
        cursor = conn.cursor()
        
        # Test each table
        tables = ['user', 'plan', 'doctor', 'facility', 'coverage']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"[OK] {table}: {count} records")
            
        # Test a specific query
        cursor.execute("""
        SELECT u.display_name, p.plan_name, p.plan_type 
        FROM user u 
        JOIN plan p ON u.plan_id = p.plan_id 
        LIMIT 2
        """)
        results = cursor.fetchall()
        print(f"[OK] Sample user-plan data: {results}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return False

def test_agent_streaming():
    """Test the agent with streaming"""
    print("\n=== Testing Agent with Streaming ===")
    streaming_updates = []
    
    def capture_streaming(state):
        streaming_updates.append({
            'step': state.current_step,
            'total_steps': len(state.processing_steps)
        })
        print(f"  [STREAM] {state.current_step}")
    
    try:
        agent = HealthcareAgent(streaming_callback=capture_streaming)
        
        print("Processing query: 'What is my insurance plan?'")
        result = agent.process_query('102', 'What is my insurance plan?')
        
        print(f"\n[OK] Streaming updates captured: {len(streaming_updates)}")
        print(f"[OK] Final answer length: {len(result.final_answer) if result.final_answer else 0} characters")
        print(f"[OK] References found: {len(result.references)}")
        print(f"[OK] Confidence: {result.confidence_score}")
        
        if result.final_answer:
            print(f"\nResponse preview: {result.final_answer[:200]}...")
        
        return True
    except Exception as e:
        print(f"[ERROR] Agent error: {e}")
        return False

def main():
    """Run all tests"""
    print("Healthcare AI Assistant - System Test")
    print("=" * 50)
    
    db_ok = test_database()
    agent_ok = test_agent_streaming()
    
    print("\n" + "=" * 50)
    if db_ok and agent_ok:
        print("[SUCCESS] All systems operational!")
        print("\nTo start the web interface:")
        print("  python main.py")
        print("  Then open: http://127.0.0.1:8050")
    else:
        print("[WARNING] Some issues detected. Check errors above.")

if __name__ == "__main__":
    main()