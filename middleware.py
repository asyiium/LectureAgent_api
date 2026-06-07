import logging
from typing import Sequence, Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

class CatchMiddleware(AgentMiddleware):
    def __init__(self, max_calls_per_tool: dict[str, int] = None, default_max: int = 1):
        super().__init__()
        
        self.max_calls = max_calls_per_tool or {}
        self.default_max = default_max
        
        self.state_schema = self.create_state_schema()
    
    def create_state_schema(self):
        from typing import Dict, TypedDict
        
        class ExtendedState(TypedDict):
            tool_call_counts: Dict[str, int]
        
        return ExtendedState
    
    def before_model(self, state, runtime) -> None:
        if "tool_call_counts" not in state:
            state["tool_call_counts"] = {}
        
        messages = state.get("messages", [])
        if not messages:
            return
        
        last_message = messages[-1]
        
        if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
            filtered_tool_calls = []
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get('name')
                current_count = state["tool_call_counts"].get(tool_name, 0)
                max_allowed = self.max_calls.get(tool_name, self.default_max)
                
                if current_count < max_allowed:
                    filtered_tool_calls.append(tool_call)
                else:
                    logger.warning(f"Блокирован повторный вызов инструмента '{tool_name}' (уже вызван {current_count} раз)")
            
            last_message.tool_calls = filtered_tool_calls
    
    def after_tools(self, state, runtime, result: Sequence[ToolMessage]) -> None:
        tool_counts = state.get("tool_call_counts", {})
        
        for tool_message in result:
            if hasattr(tool_message, 'name'):
                tool_name = tool_message.name
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                logger.info(f"Инструмент '{tool_name}' вызван {tool_counts[tool_name]} раз")
        
        state["tool_call_counts"] = tool_counts