"""
Tool Definitions for Function Calling
Story 1.13: Tool Definition System

Defines tools that agents can call (load_file, save_file, web_search, etc.)
"""

from typing import List, Dict

# OpenAI-compatible tool definitions
TOOLS_REGISTRY: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "load_file",
            "description": "Load workflow, agent, or config file from project filesystem. Only allowed for files in .bmad/, docs/, or config/ directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to project root (e.g., '.bmad/bmm/workflows/research/workflow.yaml')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_file",
            "description": "Save content to a file in the project. Only allowed for files in docs/ or output directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to project root (e.g., 'docs/research-report.md')"
                    },
                    "content": {
                        "type": "string",
                        "description": "File content to save"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in a directory. Only allowed for .bmad/, docs/, or config/ directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to project root"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_workflow_status",
            "description": "Update workflow status file with completed workflow output path",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow": {
                        "type": "string",
                        "description": "Workflow name (e.g., 'research', 'product-brief')"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Path to generated file"
                    }
                },
                "required": ["workflow", "output_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information (Story 1.16 - not implemented yet)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def get_tools() -> List[Dict]:
    """Get all available tools"""
    return TOOLS_REGISTRY


def get_tool_by_name(name: str) -> Dict | None:
    """Get tool definition by name"""
    for tool in TOOLS_REGISTRY:
        if tool["function"]["name"] == name:
            return tool
    return None

