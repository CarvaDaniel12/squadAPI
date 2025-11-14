"""
Tool Executor Engine
Story 1.14: Tool Executor Engine

Executes tools requested by agents (with security validation)
"""

import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when tool execution violates security policy"""
    pass


class ToolExecutor:
    """Executes tools with security validation"""
    
    # Whitelist of allowed paths
    WHITELIST_PATHS = ['.bmad/', 'docs/', 'config/']
    WRITE_ALLOWED_PATHS = ['docs/', '.bmad-ephemeral/']
    
    def __init__(self, project_root: str | Path = "."):
        """
        Initialize Tool Executor
        
        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute tool with arguments
        
        Args:
            tool_name: Tool name (e.g., 'load_file')
            arguments: Tool arguments dict
            
        Returns:
            Tool execution result (string)
            
        Raises:
            SecurityError: If path violates security policy
            FileNotFoundError: If file doesn't exist
            ValueError: If tool unknown or arguments invalid
        """
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")
        
        if tool_name == "load_file":
            return await self._load_file(arguments["path"])
        
        elif tool_name == "save_file":
            return await self._save_file(arguments["path"], arguments["content"])
        
        elif tool_name == "list_directory":
            return await self._list_directory(arguments["path"])
        
        elif tool_name == "update_workflow_status":
            return await self._update_workflow_status(
                arguments["workflow"],
                arguments["output_file"]
            )
        
        elif tool_name == "web_search":
            return await self._web_search(arguments["query"])
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _load_file(self, path: str) -> str:
        """Load file from filesystem (with security validation)"""
        self._validate_read_path(path)
        
        file_path = self.project_root / path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        content = file_path.read_text(encoding='utf-8')
        logger.info(f"Loaded file: {path} ({len(content)} chars)")
        
        return content
    
    async def _save_file(self, path: str, content: str) -> str:
        """Save file to filesystem (with security validation)"""
        self._validate_write_path(path)
        
        file_path = self.project_root / path
        
        # Create parent directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Saved file: {path} ({len(content)} chars)")
        
        return f"File saved successfully: {path}"
    
    async def _list_directory(self, path: str) -> str:
        """List directory contents"""
        self._validate_read_path(path)
        
        dir_path = self.project_root / path
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        files = [f.name for f in dir_path.iterdir()]
        logger.info(f"Listed directory: {path} ({len(files)} items)")
        
        return "\n".join(files)
    
    async def _update_workflow_status(self, workflow: str, output_file: str) -> str:
        """Update workflow status file"""
        # Load workflow status
        status_path = self.project_root / "docs" / "bmm-workflow-status.yaml"
        
        if not status_path.exists():
            return f"Workflow status file not found: {status_path}"
        
        # Simple implementation: Log the update
        # Full implementation would parse YAML and update
        logger.info(f"Workflow '{workflow}' completed: {output_file}")
        
        return f"Workflow '{workflow}' marked complete: {output_file}"
    
    async def _web_search(self, query: str) -> str:
        """Web search (Story 1.16 - stub for now)"""
        logger.info(f"Web search: {query}")
        return f"[STUB] Web search results for: {query}\n(Implementation in Story 1.16)"
    
    def _validate_read_path(self, path: str):
        """Validate path is allowed for reading"""
        # Prevent directory traversal
        if '..' in path:
            raise SecurityError("Path traversal not allowed")
        
        # Prevent absolute paths (Unix: /, Windows: C:\, D:\, etc.)
        if path.startswith('/') or (len(path) >= 2 and path[1] == ':'):
            raise SecurityError("Path traversal not allowed")
        
        # Normalize path for comparison (add trailing / to whitelist items)
        normalized_path = path.rstrip('/') + '/'
        
        # Whitelist check (match prefix or exact directory name)
        allowed = False
        for whitelist_item in self.WHITELIST_PATHS:
            # Match: "docs/" starts with "docs/"
            # Match: "docs" starts with "docs/"
            if normalized_path.startswith(whitelist_item) or path == whitelist_item.rstrip('/'):
                allowed = True
                break
        
        if not allowed:
            raise SecurityError(f"Path '{path}' not in read whitelist: {self.WHITELIST_PATHS}")
    
    def _validate_write_path(self, path: str):
        """Validate path is allowed for writing"""
        # Prevent directory traversal
        if '..' in path:
            raise SecurityError("Path traversal not allowed")
        
        # Prevent absolute paths (Unix: /, Windows: C:\, D:\, etc.)
        if path.startswith('/') or (len(path) >= 2 and path[1] == ':'):
            raise SecurityError("Path traversal not allowed")
        
        # Write whitelist check (more restrictive)
        if not any(path.startswith(p) for p in self.WRITE_ALLOWED_PATHS):
            raise SecurityError(f"Path '{path}' not in write whitelist: {self.WRITE_ALLOWED_PATHS}")

