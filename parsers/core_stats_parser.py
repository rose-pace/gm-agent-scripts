import re
from typing import Dict, Optional, Tuple
from .base_parser import BaseParser
from dnd_constants import CR_TO_XP

class CoreStatsParser(BaseParser):
    """Parser for basic creature statistics."""

    @classmethod
    def parse_subheader(cls, text: str) -> Dict:
        """Parse size, type, and alignment from subheader text."""
        pattern = r"^([\w\s]+) ([\w\s]+)(?: \(([\w\s,]+)\))?, ([\w\s]+)$"
        match = re.match(pattern, cls.normalize_text(text))
        
        if not match:
            raise ValueError(f"Could not parse creature type line: {text}")
        
        return {
            "size": match.group(1).strip(),
            "type": match.group(2).strip(),
            "subtype": match.group(3).strip() if match.group(3) else None,
            "alignment": match.group(4).strip()
        }

    @classmethod
    def parse_armor_class(cls, text: str) -> Dict:
        """Parse armor class value and type."""
        match = re.match(r"Armor Class (\d+)(?: \(([\w\s,]+)\))?", cls.normalize_text(text))
        if not match:
            raise ValueError(f"Could not parse armor class: {text}")
        
        return {
            "value": int(match.group(1)),
            "type": match.group(2) if match.group(2) else None
        }

    @classmethod
    def parse_hit_points(cls, text: str) -> Dict:
        """Parse hit points average and roll."""
        match = re.match(r"Hit Points (\d+)(?: \(([\d\w\s+]+)\))?", cls.normalize_text(text))
        if not match:
            raise ValueError(f"Could not parse hit points: {text}")
        
        return {
            "average": int(match.group(1)),
            "roll": match.group(2) if match.group(2) else None
        }
    
    @classmethod
    def parse_senses(cls, text: str) -> Dict:
        """Parse senses."""
        senses = {}
        sense_text = cls.normalize_text(text).replace("Senses", "").strip()

        # Parse passive perception
        pp_match = re.search(r"passive Perception (\d+)", sense_text)
        if pp_match:
            senses["passive_perception"] = int(pp_match.group(1))
            sense_text = re.sub(r"passive Perception \d+", "", sense_text).strip()
        
        sense_parts = sense_text.split(", ")
        for part in sense_parts:
            match = re.match(r"(\w+)\s+(\d+)\s*ft\.?", part)
            if match:
                senses[match.group(1).lower()] = int(match.group(2))
        
        return senses
    
    @classmethod
    def parse_languages(cls, text: str) -> Dict:
        """Parse languages including telepathy and special abilities."""
        languages = {
            "spoken": [],
            "telepathy": None,
            "special": None
        }
        
        if not text:
            languages["spoken"] = ["—"]
            return languages

        languages_text = cls.normalize_text(text).replace("Languages", "").strip()
        if not languages_text or languages_text.lower() == "none":
            languages["spoken"] = ["—"]
            return languages

        # Split on commas but handle parenthetical expressions
        parts = []
        current_part = []
        paren_level = 0
        
        for char in languages_text:
            if char == '(' or char == '[':
                paren_level += 1
            elif char == ')' or char == ']':
                paren_level -= 1
            elif char == ',' and paren_level == 0:
                parts.append(''.join(current_part).strip())
                current_part = []
                continue
            current_part.append(char)
        
        if current_part:
            parts.append(''.join(current_part).strip())

        # Process each part
        spoken = []
        for part in parts:
            part = part.strip()
            
            # Check for telepathy
            telepathy_match = re.search(r'telepathy\s+(\d+)\s*ft', part.lower())
            if telepathy_match:
                languages["telepathy"] = int(telepathy_match.group(1))
                continue

            # Check for special language abilities
            if any(indicator in part.lower() for indicator in 
                  ['understands', 'can\'t speak', 'cannot speak', 'but doesn\'t speak',
                   'communicates', 'comprehends', 'knows the meaning']):
                languages["special"] = part
                continue

            # If not telepathy or special, it's a spoken language
            if part and part != '—':
                spoken.append(part)

        languages["spoken"] = spoken if spoken else ["—"]
        return languages

    @classmethod
    def parse_challenge_rating(cls, text: str) -> Dict:
        """Parse challenge rating and calculate XP."""
        match = re.match(r"Challenge (\d+(?:/\d+)?)\s*\(([,\d]+)\s*XP\)", cls.normalize_text(text))
        if not match:
            raise ValueError(f"Could not parse challenge rating: {text}")
        
        rating = match.group(1)
        return {
            "rating": rating,
            "xp": CR_TO_XP.get(str(rating), 0)
        }

    @classmethod
    def parse_speed(cls, text: str) -> Dict:
        """Parse movement speeds."""
        speeds = {}
        speed_text = cls.normalize_text(text).replace("Speed", "").strip()
        speed_parts = speed_text.split(", ")

        special = []
        
        for part in speed_parts:
            speed_match = re.match(r"(?:(\w+)\s+)?(\d+)\s*ft\.?(.*)", part)
            if speed_match:
                speed_type = speed_match.group(1) or "walk"
                speeds[speed_type.lower()] = int(speed_match.group(2))

                extra = speed_match.group(3)
                if extra:
                    if 'hover' in extra.lower():
                        speeds['hover'] = True
                    else:
                        special.append(extra.strip())

        if special:
            speeds['special'] = '; '.join(s.strip() for s in special if s.strip())
        
        return speeds
