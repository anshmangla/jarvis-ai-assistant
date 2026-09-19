from typing import Dict, Any, List

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from pydantic import create_model, Field

from config import config
from assistant.memory import Memory
from plugins.plugin_loader import load_plugins
from utils.logger import logger


def _build_tool_from_skill(skill: Any) -> StructuredTool:
    """Dynamically converts a custom BaseSkill into a LangChain StructuredTool using Pydantic."""
    fields = {}
    for param_name, param_info in skill.parameters.items():
        ptype = str
        typ_str = param_info.get("type", "string")
        if typ_str == "integer":
            ptype = int
        elif typ_str == "boolean":
            ptype = bool
        elif typ_str == "number":
            ptype = float
            
        description = param_info.get("description", "")
        if "default" in param_info:
            fields[param_name] = (ptype, Field(default=param_info["default"], description=description))
        else:
            fields[param_name] = (ptype, Field(..., description=description))
            
    # Create dynamic Pydantic schema for the tool
    schema_name = f"{skill.name.title().replace('_', '')}Schema"
    schema_cls = create_model(schema_name, **fields)
    
    return StructuredTool.from_function(
        func=skill.run,
        name=skill.name,
        description=skill.description,
        args_schema=schema_cls
    )

class Agent:
    """The central agent orchestrating the Brain (LLM), memory, and skills natively via LangGraph."""

    def __init__(self) -> None:
        """Initialize the agent, loading skills, memory, and the LangGraph orchestrator."""
        self.memory = Memory()
        self.skills = load_plugins()
        logger.info(f"Agent initialized with {len(self.skills)} skills.")

        # Convert BaseSkills to natively supported LangChain Tools
        self.tools = [_build_tool_from_skill(skill) for skill in self.skills.values()]
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model_name=config.LLM_MODEL,
            temperature=0.3, # Keep it relatively low for reliable tool calling
            max_tokens=1024
        )
        
        # Create LangGraph ReAct agent loop
        self.graph = create_react_agent(self.llm, tools=self.tools)

    def process_command(self, user_input: str) -> str:
        """
        Process a user command end-to-end using LangGraph multi-step execution.
        
        Args:
            user_input (str): The transcribed or typed command.

        Returns:
            str: The final output of the assistant.
        """
        logger.info(f"Processing command (LangGraph): '{user_input}'")

        # -- 1. Fetch memory context -------------------------------------------
        memory_context = self.memory.get_facts_summary()
        recent_history = self.memory.get_recent_history(turns=6)

        sys_prompt = (
            "You are J.A.R.V.I.S., a highly capable Personal AI Assistant.\n"
            "Your personality is helpful, concise, smart, and efficient. Avoid overly verbose responses.\n"
            "When the user asks you to perform an action (such as opening an application, opening a website or browser, sending an email, searching the web, or setting reminders), ALWAYS call the appropriate tool to execute it.\n"
            "Never assume an application is already open or that an action is already completed based on conversation history; always invoke the tool."
        )
        
        if memory_context:
            sys_prompt += f"\n\nKnown facts about the user:\n{memory_context}"
            
        if recent_history:
            sys_prompt += f"\n\nRecent conversation history (for reference):\n{recent_history}"

        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_input)
        ]

        # -- 2. Run graph execution --------------------------------------------
        try:
            # graph.invoke runs the ReAct loop (LLM -> Tool -> LLM -> Tool -> Finish)
            result = self.graph.invoke({"messages": messages})
            response_msg = result["messages"][-1].content
            
        except Exception as e:
            logger.error(f"LangGraph execution error: {e}")
            response_msg = "I encountered an error while trying to process your request."

        # -- 3. Persist turns to memory ------------------------------------
        self.memory.save_message("user", user_input)
        self.memory.save_message("assistant", response_msg)

        return response_msg
