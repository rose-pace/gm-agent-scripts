import re
from typing import Dict, List
from .base_parser import BaseParser
from .usage_parser import UsageParser

class LairActionsParser(BaseParser):
    """Parser for lair actions."""
    
    @classmethod
    def parse_lair_actions(cls, text: str, paragraphs: List[str]) -> Dict:
        """Parse lair actions section."""
        lair_actions = {
            "description": cls.normalize_text(text),
            "initiative_count": 20,  # Default value
            "actions": []
        }
        
        # Try to find initiative count
        initiative_match = re.search(r"on initiative count (\d+)", cls.normalize_text(text.lower()))
        if initiative_match:
            lair_actions["initiative_count"] = int(initiative_match.group(1))
        
        for para in paragraphs:
            title, description = cls.split_name_description(para)
            name, _ = cls.extract_parenthetical(title)
            
            lair_actions["actions"].append({
                "name": name,
                "description": description,
                "usage": UsageParser.parse_usage(title)
            })
        
        return lair_actions
