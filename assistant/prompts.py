from typing import List, Dict, Any

# ==========================================
# SYSTEM PROMPT
# ==========================================
SYSTEM_PROMPT = """You are a highly capable Personal AI Assistant, named Nova (or Jarvis), running on a local machine.
You are powered by a Groq LLM.

Your personality is helpful, concise, smart, and efficient — like J.A.R.V.I.S. from Iron Man. 
You avoid overly verbose responses. You directly answer questions or execute the required commands.

You have access to a set of tools (skills). When the user asks you to perform an action, you should respond with a tool call. If the user expects a conversation, respond conversationally.
"""

# ==========================================
# CONVERSATIONAL PROMPT
# ==========================================
def get_conversational_prompt(memory: str = "", recent_history: str = "") -> str:
    """
    Returns the conversational prompt incorporating memory facts and recent history.
    """
    prompt = f"{SYSTEM_PROMPT}\n\n"
    
    if memory:
        prompt += f"Here are some facts you remember about the user:\n{memory}\n\n"
        
    if recent_history:
        prompt += f"Recent Conversation History:\n{recent_history}\n\n"
        
    return prompt

# ==========================================
# TOOL SELECTION PROMPT
# ==========================================
def get_tool_selection_prompt(user_input: str, available_tools: List[Dict[str, Any]]) -> str:
    """
    Returns the prompt instructing the LLM to select a tool or respond conversationally.
    """
    tools_str = ""
    for tool in available_tools:
        tools_str += f"""
- Tool: {tool['name']}
  Description: {tool['description']}
  Parameters: {tool['parameters']}
"""

    prompt = f"""{SYSTEM_PROMPT}

You must decide whether to call a tool or respond conversationally based on the User's input.

AVAILABLE TOOLS:
{tools_str}

If a tool is needed, you MUST format your response as valid JSON returning the tool to use and its arguments.
Example Tool Response:
```json
{{
  "tool": "web_search",
  "arguments": {{
    "query": "latest AI news"
  }}
}}
```

If no tool is needed, respond conversationally. Ensure your response does NOT look like a JSON block.

User Input: "{user_input}"
Select a tool (JSON) or respond conversationally:
"""
    return prompt
