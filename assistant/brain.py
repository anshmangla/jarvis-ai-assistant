import json
from typing import Optional, Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import config
from utils.logger import logger
from utils.helpers import parse_llm_json
from assistant.prompts import get_tool_selection_prompt, get_conversational_prompt

class Brain:
    """Handles LLM reasoning using LangChain and Groq API."""
    
    def __init__(self):
        """Initialize the Groq LLM via LangChain."""
        logger.info(f"Initializing Brain (Model: {config.LLM_MODEL})...")
        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model_name=config.LLM_MODEL,
            temperature=0.3, # Keep it relatively low for reliable tool calling
            max_tokens=1024
        )

    def determine_action(self, user_input: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ask the LLM to decide whether to call a tool or chat, given the user input.
        
        Args:
            user_input (str): The user's query or command.
            available_tools (List[Dict[str, Any]]): The list of serialized tool schemas.
            
        Returns:
            Dict[str, Any]: A dictionary containing either the raw 'response' text 
                            or 'tool' and 'arguments' for parsing.
        """
        prompt = get_tool_selection_prompt(user_input, available_tools)
        
        try:
            messages = [
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            content = response.content
            
            # Check if the LLM returned JSON (tool call format)
            parsed_json = parse_llm_json(content)
            
            if parsed_json and "tool" in parsed_json:
                logger.info(f"LLM decided to use tool: {parsed_json['tool']}")
                return parsed_json
            
            # No tool matched; return conversational response
            return {"response": content}
            
        except Exception as e:
            logger.error(f"Error determining action in LLM: {e}")
            return {"response": "I encountered an error while trying to process your request."}

    def generate_response(self, user_input: str, context: str = "", memory: str = "", history: str = "") -> str:
        """
        Produce a conversational response taking into account facts and tool outputs context.
        
        Args:
            user_input (str): The user's prompt.
            context (str): Any tool output context string to incorporate.
            memory (str): Facts from memory.
            history (str): Recent conversation history.
            
        Returns:
            str: The LLM's conversational response.
        """
        prompt = get_conversational_prompt(memory, history)
        
        # We construct messages explicitly
        messages = [
            SystemMessage(content=prompt)
        ]
        
        if context:
            messages.append(SystemMessage(content=f"Context from recent tools:\n{context}"))
            
        messages.append(HumanMessage(content=user_input))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating conversational response in LLM: {e}")
            return "I'm having trouble thinking right now."
