from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class AgentState(BaseModel):
    """State model for the healthcare AI agent workflow."""
    
    # Input data
    user_id: str = Field(description="User ID from the system")
    user_message: str = Field(description="User's input message/query")
    user_profile: Optional[Dict[str, Any]] = Field(default=None, description="User profile information")
    
    # Reasoning layer outputs  
    reasoning_plan: Optional[Dict[str, Any]] = Field(default=None, description="Structured reasoning plan from Layer 1")
    
    # Action layer data
    action_results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from tool executions")
    references: List[str] = Field(default_factory=list, description="Source references for citations")
    
    # Final outputs
    final_answer: Optional[str] = Field(default=None, description="Final formatted response to user")
    confidence_score: Optional[float] = Field(default=None, description="Confidence in the response (0-1)")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    
    # Conversation context
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Previous messages in conversation")
    
    # Error handling
    errors: List[str] = Field(default_factory=list, description="Any errors encountered during processing")
    
    # Streaming updates
    processing_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Real-time processing steps")
    current_step: Optional[str] = Field(default=None, description="Current processing step")
    
    class Config:
        arbitrary_types_allowed = True