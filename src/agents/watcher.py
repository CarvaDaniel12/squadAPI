"""
Agent Hot-Reload Support
Story 1.10: Agent Hot-Reload Support

Watches .bmad/bmm/agents/ for file changes and reloads automatically
"""

import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class AgentWatcher:
    """Watches agent files for changes and triggers reload"""
    
    def __init__(self, agents_dir: Path, on_change_callback: Callable):
        """
        Initialize Agent Watcher
        
        Args:
            agents_dir: Directory to watch (.bmad/bmm/agents/)
            on_change_callback: Async callback to call when changes detected
        """
        self.agents_dir = agents_dir
        self.on_change = on_change_callback
        self._last_modified = {}
    
    async def check_for_changes(self) -> bool:
        """
        Check if any agent files changed
        
        Returns:
            True if changes detected, False otherwise
        """
        changed = False
        
        for file in self.agents_dir.glob("*.md"):
            if file.stem in ['README', 'index']:
                continue
            
            current_mtime = file.stat().st_mtime
            last_mtime = self._last_modified.get(str(file), 0)
            
            if current_mtime > last_mtime:
                logger.info(f"Agent file changed: {file.name}")
                self._last_modified[str(file)] = current_mtime
                changed = True
        
        if changed:
            await self.on_change()
        
        return changed


# Note: Full file watcher with watchdog library can be added post-MVP
# For MVP: Manual reload via endpoint or periodic check

