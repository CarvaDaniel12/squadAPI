"""
BMad Agent File Parser
Story 1.1: BMad Agent File Parser

Parses .bmad/bmm/agents/*.md files and extracts:
- YAML frontmatter (name, description)
- XML agent block (name, title, icon)
- Persona (role, identity, communication_style, principles)
- Menu items (cmd, workflow, exec, etc.)
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import yaml

from src.models.agent import AgentDefinition, Persona, MenuItem


class AgentParser:
    """Parses BMad agent definition files (.md format)"""
    
    def parse(self, filepath: str | Path) -> AgentDefinition:
        """
        Parse BMad agent file and return AgentDefinition
        
        Args:
            filepath: Path to .bmad/bmm/agents/{agent_id}.md file
            
        Returns:
            AgentDefinition: Parsed agent definition
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Agent file not found: {filepath}")
        
        content = filepath.read_text(encoding='utf-8')
        
        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        
        # Extract and parse XML agent block
        xml_block = self._extract_xml_block(content)
        agent_element = ET.fromstring(xml_block)
        
        # Parse persona
        persona = self._parse_persona(agent_element)
        
        # Parse menu
        menu = self._parse_menu(agent_element)
        
        # Extract workflows from menu
        workflows = [item.workflow for item in menu if item.workflow]
        
        return AgentDefinition(
            id=frontmatter.get('name', filepath.stem),
            name=agent_element.get('name', 'Unknown'),
            title=agent_element.get('title', 'Unknown'),
            icon=agent_element.get('icon', ''),
            persona=persona,
            menu=menu,
            workflows=workflows
        )
    
    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter from markdown file"""
        # Match YAML frontmatter between --- delimiters
        match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        
        if not match:
            return {}
        
        frontmatter_text = match.group(1)
        return yaml.safe_load(frontmatter_text) or {}
    
    def _extract_xml_block(self, content: str) -> str:
        """Extract XML agent block from markdown"""
        # Find content between ```xml and ``` (or just <agent> tags)
        xml_match = re.search(r'```xml\s*\n(.*?)\n```', content, re.DOTALL)
        
        if xml_match:
            return xml_match.group(1).strip()
        
        # Fallback: Look for <agent> tag directly
        agent_match = re.search(r'(<agent.*?</agent>)', content, re.DOTALL)
        
        if agent_match:
            return agent_match.group(1)
        
        raise ValueError("No XML agent block found in file")
    
    def _parse_persona(self, agent_element: ET.Element) -> Persona:
        """Parse persona section from agent XML"""
        persona_elem = agent_element.find('.//persona')
        
        if persona_elem is None:
            # Return default persona
            return Persona(
                role="Agent",
                identity="AI Assistant",
                communication_style="Professional",
                principles="Follow instructions"
            )
        
        return Persona(
            role=self._get_text(persona_elem, 'role', 'Agent'),
            identity=self._get_text(persona_elem, 'identity', 'AI Assistant'),
            communication_style=self._get_text(persona_elem, 'communication_style', 'Professional'),
            principles=self._get_text(persona_elem, 'principles', 'Follow instructions')
        )
    
    def _parse_menu(self, agent_element: ET.Element) -> list[MenuItem]:
        """Parse menu items from agent XML"""
        menu_elem = agent_element.find('.//menu')
        
        if menu_elem is None:
            return []
        
        menu_items = []
        
        for item in menu_elem.findall('item'):
            menu_item = MenuItem(
                cmd=item.get('cmd', ''),
                description=item.text.strip() if item.text else None,
                workflow=item.get('workflow'),
                exec=item.get('exec'),
                data=item.get('data'),
                action=item.get('action')
            )
            menu_items.append(menu_item)
        
        return menu_items
    
    def _get_text(self, parent: ET.Element, tag: str, default: str = '') -> str:
        """Get text content from child element, with default"""
        elem = parent.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
        return default


# Convenience function
def parse_agent_file(filepath: str | Path) -> AgentDefinition:
    """Parse BMad agent file - convenience function"""
    parser = AgentParser()
    return parser.parse(filepath)


