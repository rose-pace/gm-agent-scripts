import re
from typing import Dict, List, Optional
from .base_parser import BaseParser

class RegionalEffectsParser(BaseParser):
    """Parser for regional effects."""
    
    @classmethod
    def parse_regional_effects(cls, text: str, paragraphs: List[str]) -> Dict:
        """Parse regional effects section."""
        # Extract range and duration from first paragraph
        range_match = re.search(r"within (\d+ (?:feet|miles))", text)
        
        duration = None
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if sentences:
            duration = sentences[-1]
        
        regional_effects = {
            "range": range_match.group(1) if range_match else None,
            "duration": duration,
            "effects": []
        }
        
        for para in paragraphs:
            name, description = cls.split_name_description(para)
            
            effect = {
                "name": name,
                "description": description,
                "mechanics": cls._parse_effect_mechanics(description)
            }
            
            regional_effects["effects"].append(effect)
        
        return regional_effects

    @staticmethod
    def _parse_effect_mechanics(text: str) -> Optional[dict]:
        """Parse saving throws and effects from regional effect description."""
        mechanics = {}
        
        # Look for save DC pattern
        dc_match = re.search(r"DC (\d+) (\w+) saving throw", text)
        if dc_match:
            mechanics["save_dc"] = int(dc_match.group(1))
            mechanics["save_type"] = dc_match.group(2).lower()
            
            # Look for effects after the saving throw
            effects_match = re.search(r"saving throw(?:,|\.|\s?or) (.+?)(?:$|\.(?:\s|$))", text)
            if effects_match:
                mechanics["effects"] = effects_match.group(1).strip()
        
        return mechanics if mechanics else None
