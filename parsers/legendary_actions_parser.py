import re
from typing import Dict, List, Optional
from .base_parser import BaseParser
from .usage_parser import UsageParser

class LegendaryActionsParser(BaseParser):
    """Parser for legendary actions."""
    
    @classmethod
    def parse_legendary_actions(cls, text: str, paragraphs: List[str]) -> Dict:
        """Parse legendary actions section."""
        # Extract slots per round from description
        slots_match = re.search(r"can take (\d+) legendary actions?", cls.normalize_text(text))
        slots = int(slots_match.group(1)) if slots_match else 3  # Default to 3
        
        legendary_actions = {
            "slots_per_round": slots,
            "description": text,
            "actions": []
        }
        
        for para in paragraphs:
            title, description = cls.split_name_description(para)
            name, _ = cls.extract_parenthetical(title)
            
            # Parse cost if specified
            cost_match = re.search(r"\(costs (\d+) actions\)", name.lower())
            cost = int(cost_match.group(1)) if cost_match else 1
            name = re.sub(r"\(costs \d+ actions\)", "", name)
            
            legendary_actions["actions"].append({
                "name": name.strip(),
                "description": description,
                "cost": cost,
                "usage": UsageParser.parse_usage(title)
            })
        
        return legendary_actions
