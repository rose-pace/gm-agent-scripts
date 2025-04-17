import re
from typing import Dict, List, Optional
from .base_parser import BaseParser
from validators.action_validators import WeaponType
from .usage_parser import UsageParser

class ActionsParser(BaseParser):
    """Parser for actions, including attacks and damage."""

    @classmethod
    def parse_attack(cls, text: str) -> Optional[Dict]:
        """Parse attack details from text."""
        attack_match = re.search(
            r'(?:Melee or Ranged|(?:Melee|Ranged)) '
            r'(?:Weapon|Spell )?Attack(?: Roll)?:\s*([+-]\d+)(?: to hit)?'
            r'(?:, (?:reach|range) ((?:\d+/\d+|\d+) ft\.))?'
            r'(?:or (?:reach|range) ((?:\d+/\d+|\d+) ft\.))?',
            text
        )

        if not attack_match:
            return None

        weapon_or_spell = WeaponType.SPELL if 'Spell Attack' in text else WeaponType.WEAPON
        
        attack_info = {
            "weapon_type": weapon_or_spell.value,
            "is_melee": 'melee' in text.lower(),
            "is_ranged": 'range' in text.lower(),
            "bonus": int(attack_match.group(1)),
            "ability_used": None,
            "magical_bonus": None,
            "reach": None,
            "range": None
        }

        # Add reach/range based on attack types
        if attack_info["is_melee"]:
            attack_info["reach"] = attack_match.group(2)
        if attack_info["is_ranged"]:
            attack_info["range"] = attack_match.group(3) if attack_match.group(3) else attack_match.group(2)

        # Check for magical weapon bonus
        magic_match = re.search(r'(?:with a )?([+-]\d+) magical', text.lower())
        if magic_match:
            attack_info["magical_bonus"] = int(magic_match.group(1))

        return attack_info

    @classmethod
    def parse_damage(cls, text: str) -> Optional[Dict]:
        """Parse damage roll and type from text."""
        damage_pattern = r'Hit:\s*\d+\s*\(([\dd+\s-]+)\)\s*([\w\s,]+)\s*damage'
        two_handed_pattern = r'or\s*\d+\s*\(([\dd+\s-]+)\)\s*([\w\s,]+)\s*damage when used with two hands'
        # Add pattern for simpler damage format without dice notation
        simple_damage_pattern = r'Hit:\s*(\d+)\s*([\w\s,]+)\s*damage'
        
        damage_match = re.search(damage_pattern, text)
        two_handed_match = re.search(two_handed_pattern, text)
        simple_damage_match = re.search(simple_damage_pattern, text)
        
        if not damage_match and not simple_damage_match:
            return None

        hit_info = {
            "damage": damage_match.group(1).strip() if damage_match else simple_damage_match.group(1).strip(),
            "damage_type": damage_match.group(2).strip() if damage_match else simple_damage_match.group(2).strip(),
        }
        
        if two_handed_match:
            hit_info["damage_two_handed"] = two_handed_match.group(1).strip()
            
        effects_pattern = r'damage(?:(?:,|\.) (.+?)(?:$|\.(?:\s|$)))'
        additional_match = re.search(effects_pattern, text)
        if additional_match:
            hit_info["additional_effects"] = additional_match.group(1).strip()
            
        return hit_info

    @classmethod
    def parse_action(cls, text: str, name: str = None) -> Dict:
        """Parse a complete action entry."""
        if not name:
            name, text = cls.split_name_description(text)

        return {
            "name": cls.extract_parenthetical(name)[0],
            "description": text,
            "attack": cls.parse_attack(text),
            "hit": cls.parse_damage(text),
            "usage": UsageParser.parse_usage(name)
        }
