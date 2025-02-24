import re
from typing import Dict, List, Optional, Tuple
from .base_parser import BaseParser

class AbilitiesParser(BaseParser):
    """Parser for abilities, saving throws, and skills."""

    ABILITIES = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']

    @classmethod
    def parse_ability_scores(cls, text: str) -> Dict:
        """Parse ability scores and modifiers from text."""        
        score_mod_match = re.match(r'(\d+)\s*\(([+-]\d+)\)', text)
        if score_mod_match:
            return {
                'score': int(score_mod_match.group(1)),
                'modifier': int(score_mod_match.group(2))
            }
        return None

    @classmethod
    def parse_saving_throws(cls, text: str) -> List[Dict]:
        """Parse saving throw bonuses."""
        saves = []
        text = cls.normalize_text(text).replace("Saving Throws", "").strip()
        
        for save in text.split(", "):
            match = re.match(r"(\w+)\s*([+-]\d+)", save)
            if match:
                saves.append({
                    "ability": match.group(1).lower(),
                    "modifier": int(match.group(2))
                })
        
        return saves

    @classmethod
    def parse_skills(cls, text: str) -> List[Dict]:
        """Parse skill proficiencies."""
        skills = []
        text = cls.normalize_text(text).replace("Skills", "").strip()
        
        for skill in text.split(", "):
            match = re.match(r"(\w+(?:\s+\w+)?)\s*([+-]\d+)", skill)
            if match:
                skills.append({
                    "name": match.group(1),
                    "modifier": int(match.group(2))
                })
        
        return skills
