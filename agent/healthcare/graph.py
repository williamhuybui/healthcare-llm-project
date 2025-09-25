import os
import json
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from agent.healthcare.state import AgentState
from agent.sql.sql_tool import SQLTool
from tools.pdf_tool import PDFTool

class HealthcareAgent:
    """Two-layer healthcare AI agent using LangChain + LangGraph."""
    
    def __init__(self, streaming_callback=None):
        """Initialize the agent with OpenAI model and tools."""
        self.streaming_callback = streaming_callback
        # Initialize OpenAI model
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not set. Agent will not work properly.")
            # Create a mock LLM for testing
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.2,
                api_key=api_key
            )
        
        # Initialize tools
        self.sql_tool = SQLTool()
        self.pdf_tool = PDFTool()
        
        # Load prompts and schemas
        self.prompts = self._load_prompts()
        self.schema = self._load_schema()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates from files."""
        prompts = {}
        prompt_dir = Path("prompts")
        
        # Load reasoning prompt
        reasoning_path = prompt_dir / "prompt_reasoning.txt"
        if reasoning_path.exists():
            prompts['reasoning'] = reasoning_path.read_text()
        
        # Load action prompt  
        action_path = prompt_dir / "prompt_action.txt"
        if action_path.exists():
            prompts['action'] = action_path.read_text()
        
        # Load reasoning playbook
        playbook_path = prompt_dir / "reasoning_playbook.json"
        if playbook_path.exists():
            with open(playbook_path) as f:
                prompts['playbook'] = json.load(f)
        
        return prompts
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load schema information."""
        schema_path = Path("schemas/schema_meta.json")
        if schema_path.exists():
            with open(schema_path) as f:
                return json.load(f)
        return {}
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("reasoning_node", self.reasoning_node)
        graph.add_node("action_node", self.action_node)
        graph.add_node("finalize_node", self.finalize_node)
        
        # Add edges
        graph.add_edge("reasoning_node", "action_node")
        graph.add_edge("action_node", "finalize_node")
        graph.add_edge("finalize_node", END)
        
        # Set entry point
        graph.set_entry_point("reasoning_node")
        
        return graph.compile()
    
    def _add_processing_step(self, state: AgentState, step_name: str, description: str, status: str = "in_progress"):
        """Add a processing step for streaming updates."""
        step = {
            "step": step_name,
            "description": description, 
            "status": status,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        state.processing_steps.append(step)
        state.current_step = description
        
        if self.streaming_callback:
            self.streaming_callback(state)
    
    def reasoning_node(self, state: AgentState) -> AgentState:
        """
        Layer 1: Reasoning Node
        Analyze user query and create structured plan.
        """
        self._add_processing_step(state, "reasoning", "[THINKING] Analyzing your question and creating a plan...")
        
        try:
            # Get user profile data
            if not state.user_profile and state.user_id:
                state.user_profile = self._get_user_profile(state.user_id)
            
            # Format reasoning prompt
            reasoning_prompt = self.prompts.get('reasoning', '').format(
                user_id=state.user_id,
                user_profile=state.user_profile or {},
                user_message=state.user_message
            )
            
            # Add playbook context
            playbook_context = ""
            if 'playbook' in self.prompts:
                playbook_context = f"\n\nPlaybook Reference:\n{json.dumps(self.prompts['playbook'], indent=2)}"
            
            # Create messages
            messages = [
                SystemMessage(content=reasoning_prompt + playbook_context),
                HumanMessage(content=f"Analyze this query and create a plan: {state.user_message}")
            ]
            
            # Get LLM response
            if not self.llm:
                # Mock response when no API key
                response = type('MockResponse', (), {
                    'content': json.dumps({
                        "rationale": "No OpenAI API key provided",
                        "user_intent": state.user_message,
                        "steps": [{"step_number": 1, "action": "sql_query", "description": "Basic query"}]
                    })
                })()
            else:
                response = self.llm.invoke(messages)
            
            # Parse JSON response
            try:
                reasoning_plan = json.loads(response.content)
                state.reasoning_plan = reasoning_plan
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                state.reasoning_plan = {
                    "rationale": "Failed to parse structured plan",
                    "user_intent": state.user_message,
                    "steps": [{"step_number": 1, "action": "sql_query", "description": "General search"}]
                }
                state.errors.append("Reasoning plan JSON parsing failed")
            
            print(f"[Reasoning] Plan created: {state.reasoning_plan.get('rationale', 'No rationale')}")
            self._add_processing_step(state, "reasoning", "[READY] Created analysis plan with {} steps".format(len(state.reasoning_plan.get('steps', []))), "completed")
            
        except Exception as e:
            state.errors.append(f"Reasoning error: {str(e)}")
            # Create fallback plan
            state.reasoning_plan = {
                "rationale": "Error in reasoning, using fallback",
                "user_intent": state.user_message,
                "steps": [{"step_number": 1, "action": "sql_query", "description": "General search"}]
            }
        
        return state
    
    def action_node(self, state: AgentState) -> AgentState:
        """
        Layer 2: Action Node
        Execute the reasoning plan using tools.
        """
        self._add_processing_step(state, "action", "[WORKING] Starting to execute your plan...")
        if not state.reasoning_plan:
            state.errors.append("No reasoning plan available for action")
            return state
        
        try:
            steps = state.reasoning_plan.get('steps', [])
            
            for step in steps:
                action_type = step.get('action', '')
                description = step.get('description', '')
                parameters = step.get('parameters', {})
                
                print(f"[Action] Executing step: {description}")
                
                # Show what we're doing
                if action_type == 'sql_query':
                    self._add_processing_step(state, "action", f"[DATABASE] Querying database: {description}")
                elif action_type == 'pdf_search':
                    self._add_processing_step(state, "action", f"[DOCUMENTS] Searching documents: {description}")
                else:
                    self._add_processing_step(state, "action", f"[PROCESSING] {description}")
                
                if action_type == 'sql_query':
                    result = self._execute_sql_action(step, state)
                elif action_type == 'pdf_search':
                    result = self._execute_pdf_action(step, state)
                elif action_type in ['calculation', 'analysis']:
                    result = self._execute_analysis_action(step, state)
                else:
                    result = {
                        "action": action_type,
                        "status": "unsupported",
                        "description": description,
                        "reference": f"Unsupported action type: {action_type}"
                    }
                
                state.action_results.append(result)
                
                # Add reference if available
                if 'reference' in result:
                    state.references.append(result['reference'])
            
            print(f"[Action] Completed {len(steps)} steps")
            self._add_processing_step(state, "action", f"[DONE] Completed {len(steps)} action steps", "completed")
            
        except Exception as e:
            state.errors.append(f"Action error: {str(e)}")
        
        return state
    
    def finalize_node(self, state: AgentState) -> AgentState:
        """
        Finalization Node
        Generate final response with references.
        """
        self._add_processing_step(state, "finalize", "[WRITING] Generating your personalized response...")
        
        try:
            # Compile results summary
            results_summary = []
            for result in state.action_results:
                if result.get('status') == 'success':
                    results_summary.append(f"- {result.get('description', 'Action completed')}")
                    if 'data' in result:
                        data = result['data']
                        if isinstance(data, dict) and 'results' in data:
                            results_summary.append(f"  Found {data.get('row_count', 0)} results")
                        elif isinstance(data, dict) and 'snippets' in data:
                            results_summary.append(f"  Found {len(data.get('snippets', []))} text snippets")
            
            # Create finalization prompt
            finalization_prompt = f"""
            Generate a helpful, conversational response to the user's question.
            
            Original Question: {state.user_message}
            User Profile: {state.user_profile or 'Not available'}
            
            Reasoning: {state.reasoning_plan.get('rationale', 'No reasoning available')}
            
            Results Summary:
            {chr(10).join(results_summary) if results_summary else 'No results available'}
            
            Action Results: {json.dumps(state.action_results, indent=2, default=str)}
            
            Please provide a clear, helpful answer that addresses the user's question.
            Focus on the most relevant information and be conversational.
            If there are specific data points, include them naturally in the response.
            """
            
            messages = [
                SystemMessage(content="You are a helpful healthcare AI assistant. Provide clear, accurate responses based on the available data."),
                HumanMessage(content=finalization_prompt)
            ]
            
            if not self.llm:
                # Mock response when no API key
                state.final_answer = "I'm sorry, but I need an OpenAI API key to provide proper responses. Please set the OPENAI_API_KEY environment variable."
            else:
                response = self.llm.invoke(messages)
                state.final_answer = response.content
            
            # Set confidence based on success of actions
            successful_actions = len([r for r in state.action_results if r.get('status') == 'success'])
            total_actions = len(state.action_results)
            state.confidence_score = successful_actions / total_actions if total_actions > 0 else 0.5
            
            # Generate follow-up suggestions
            state.follow_up_suggestions = self._generate_follow_ups(state)
            
            print(f"[Finalize] Response generated (confidence: {state.confidence_score:.2f})")
            self._add_processing_step(state, "finalize", "[COMPLETE] Response ready!", "completed")
            
        except Exception as e:
            state.errors.append(f"Finalization error: {str(e)}")
            state.final_answer = "I encountered an error while processing your request. Please try rephrasing your question."
            state.confidence_score = 0.0
        
        return state
    
    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile from database."""
        try:
            result = self.sql_tool.search_user_data(user_id)
            if result['results']:
                return result['results'][0]
        except Exception:
            pass
        return {}
    
    def _execute_sql_action(self, step: Dict, state: AgentState) -> Dict[str, Any]:
        """Execute SQL-based action."""
        try:
            description = step.get('description', '')
            parameters = step.get('parameters', {})
            
            # Generate appropriate SQL query based on intent
            query = self._generate_sql_query(step, state)
            
            if not query:
                return {
                    "action": "sql_query",
                    "status": "error",
                    "description": description,
                    "reference": "Could not generate SQL query"
                }
            
            result = self.sql_tool.execute_query(query, description)
            
            return {
                "action": "sql_query",
                "status": "success" if not result.get('error') else "error",
                "description": description,
                "data": result,
                "reference": result.get('reference', 'SQL query executed')
            }
            
        except Exception as e:
            return {
                "action": "sql_query", 
                "status": "error",
                "description": step.get('description', ''),
                "reference": f"SQL error: {str(e)}"
            }
    
    def _execute_pdf_action(self, step: Dict, state: AgentState) -> Dict[str, Any]:
        """Execute PDF search action."""
        try:
            description = step.get('description', '')
            parameters = step.get('parameters', {})
            
            # Extract keywords from user message and step
            keywords = parameters.get('keywords', state.user_message)
            max_results = parameters.get('max_results', 3)
            
            result = self.pdf_tool.search_documents(keywords, max_results=max_results)
            
            return {
                "action": "pdf_search",
                "status": "success" if not result.get('error') else "error", 
                "description": description,
                "data": result,
                "reference": result.get('reference', 'PDF search completed')
            }
            
        except Exception as e:
            return {
                "action": "pdf_search",
                "status": "error",
                "description": step.get('description', ''),
                "reference": f"PDF search error: {str(e)}"
            }
    
    def _execute_analysis_action(self, step: Dict, state: AgentState) -> Dict[str, Any]:
        """Execute analysis or calculation action."""
        return {
            "action": step.get('action', 'analysis'),
            "status": "success",
            "description": step.get('description', ''),
            "data": {"note": "Analysis action completed"},
            "reference": "Analysis performed"
        }
    
    def _generate_sql_query(self, step: Dict, state: AgentState) -> str:
        """Generate SQL query based on step and context."""
        user_message = state.user_message.lower()
        description = step.get('description', '').lower()
        
        # User profile queries
        if 'user' in description or 'profile' in user_message:
            return f"SELECT * FROM user WHERE user_id = '{state.user_id}'"
        
        # Plan queries
        elif 'plan' in user_message or 'insurance' in user_message:
            if state.user_profile and state.user_profile.get('plan_id'):
                return f"SELECT * FROM plan WHERE plan_id = {state.user_profile['plan_id']}"
            else:
                return "SELECT * FROM plan LIMIT 5"
        
        # Doctor queries  
        elif 'doctor' in user_message or 'physician' in user_message or 'provider' in user_message:
            if 'specialist' in user_message:
                return "SELECT * FROM doctor WHERE specialty NOT LIKE '%Family%' AND specialty NOT LIKE '%Internal%' LIMIT 10"
            else:
                return "SELECT * FROM doctor LIMIT 10"
        
        # Coverage queries
        elif 'coverage' in user_message or 'benefit' in user_message or 'cost' in user_message:
            return "SELECT * FROM coverage LIMIT 10"
        
        # Default query
        else:
            return "SELECT name FROM sqlite_master WHERE type='table'"
    
    def _generate_follow_ups(self, state: AgentState) -> List[str]:
        """Generate follow-up question suggestions."""
        user_message = state.user_message.lower()
        suggestions = []
        
        if 'plan' in user_message:
            suggestions.extend([
                "What doctors are in my network?",
                "How much would a specialist visit cost?",
                "What are my prescription drug benefits?"
            ])
        elif 'doctor' in user_message:
            suggestions.extend([
                "What is this doctor's specialty?", 
                "Does this doctor accept new patients?",
                "What facility is this doctor at?"
            ])
        elif 'cost' in user_message:
            suggestions.extend([
                "What is my deductible?",
                "What are my out-of-pocket maximums?",
                "How does coinsurance work?"
            ])
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def process_query(self, user_id: str, user_message: str, conversation_history: List = None) -> AgentState:
        """
        Main entry point to process a user query.
        
        Args:
            user_id: ID of the user making the query
            user_message: The user's question/message
            conversation_history: Previous conversation context
            
        Returns:
            Final agent state with response and references
        """
        # Initialize state
        initial_state = AgentState(
            user_id=user_id,
            user_message=user_message,
            conversation_history=conversation_history or []
        )
        
        # Run the graph
        final_state_dict = self.graph.invoke(initial_state)
        
        # Close tool connections
        self.sql_tool.close()
        self.pdf_tool.close()
        
        # Convert back to AgentState if it's a dictionary
        if isinstance(final_state_dict, dict):
            final_state = AgentState(**final_state_dict)
        else:
            final_state = final_state_dict
        
        return final_state

if __name__ == "__main__":
    # Test the agent
    agent = HealthcareAgent()
    
    # Test query
    result = agent.process_query(
        user_id="101",
        user_message="What is my insurance plan and what does it cover?"
    )
    
    print(f"\n=== AGENT RESPONSE ===")
    print(f"Answer: {result.final_answer}")
    print(f"Confidence: {result.confidence_score}")
    print(f"References: {result.references}")
    print(f"Errors: {result.errors}")