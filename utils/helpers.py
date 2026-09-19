import json
from typing import Any, Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

def parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from an LLM response text, handling potential Markdown formatting blocks.
    
    Args:
        text (str): The raw text response from the LLM.
        
    Returns:
        Optional[Dict[str, Any]]: The parsed JSON dictionary, or None if parsing fails.
    """
    try:
        clean_text = text.strip()
        
        # Strip Markdown code block formatting if present
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
            
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        return json.loads(clean_text.strip())
    except json.JSONDecodeError:
        # This is expected when the LLM responds conversationally instead of calling a tool.
        logger.debug("Response is not JSON. Falling back to conversational response.")
        return None

def format_tool_response(tool_name: str, result: Any) -> str:
    """
    Format the output of a tool into a standardized string for the LLM to process.
    
    Args:
        tool_name (str): The name of the tool executed.
        result (Any): The output or result payload returned by the tool.
        
    Returns:
        str: A formatted string summarizing the tool execution and result.
    """
    return f"Tool '{tool_name}' completed. Result:\n{result}"
