import re
from typing import Dict, List, Optional, Tuple
from validators.spellcasting_validators import (
    SpellcastingType, SpellcastingAbility
)

class SpellcastingParser:
    """Parser for spellcasting traits and spell-like abilities."""
    
    ABILITY_PATTERNS = {
        r'intelligence': SpellcastingAbility.INTELLIGENCE,
        r'wisdom': SpellcastingAbility.WISDOM,
        r'charisma': SpellcastingAbility.CHARISMA
    }

    def parse_spellcasting_trait(self, text: str, abilities: dict) -> Optional[Dict]:
        """Parse spellcasting trait text into structured data."""
        if not any(x in text.lower() for x in ['spellcasting', 'innate spellcasting']):
            return None

        # Initialize spellcasting data
        spellcasting_data = {
            'type': self._determine_casting_type(text),
            'ability': self._parse_ability(text),
            'special_bonuses': [],
            'at_will': [],
            'spell_slots': [],
            'limited_use': []
        }

        # Parse DC and attack bonus
        dc, attack_bonus, base_modifier = self._parse_modifiers(text)
        if not base_modifier:
            base_modifier = abilities[spellcasting_data['ability'].lower()].get('modifier')
        if not base_modifier:
            raise ValueError('Spellcasting ability modifier not found')
        spellcasting_data.update({
            'dc': dc,
            'attack_bonus': attack_bonus,
            'base_modifier': base_modifier
        })

        # Parse spells based on type
        if spellcasting_data['type'] == SpellcastingType.INNATE:
            self._parse_innate_spells(text, spellcasting_data)
        else:
            self._parse_regular_spells(text, spellcasting_data)

        return spellcasting_data

    def _determine_casting_type(self, text: str) -> SpellcastingType:
        """Determine spellcasting type from text."""
        text_lower = text.lower()
        if 'innate spellcasting' in text_lower:
            return SpellcastingType.INNATE.value
        elif 'pact magic' in text_lower:
            return SpellcastingType.PACT_MAGIC.value
        return SpellcastingType.REGULAR.value

    def _parse_ability(self, text: str) -> SpellcastingAbility:
        """Parse spellcasting ability."""
        text_lower = text.lower()
        for pattern, ability in self.ABILITY_PATTERNS.items():
            if pattern in text_lower:
                return ability.value
        return SpellcastingAbility.WISDOM.value  # Default if not found

    def _parse_modifiers(self, text: str) -> Tuple[int, int, int]:
        """Parse DC, attack bonus, and base modifier."""
        dc_match = re.search(r'spell save DC (\d+)', text)
        attack_match = re.search(r'([+-]\d+) to hit with spell attacks', text)
        modifier_match = re.search(r'spellcasting ability (?:modifier )?is ([+-]\d+)', text)

        dc = int(dc_match.group(1)) if dc_match else 10
        attack_bonus = int(attack_match.group(1)) if attack_match else 0
        base_modifier = int(modifier_match.group(1)) if modifier_match else 0

        return dc, attack_bonus, base_modifier

    def _parse_innate_spells(self, text: str, data: Dict) -> None:
        """Parse innate spellcasting details."""
        lines = text.splitlines()
        for line in lines:
        # At will spells
            at_will_match = re.search(r'At will:\s*([^\.]+)', line)
            if at_will_match:
                data['at_will'] = self._parse_spell_list(at_will_match.group(1))
                continue

            # Limited use spells

            for freq in ['3/day', '2/day', '1/day', '1/rest', '1/dawn']:
                freq_match = re.search(freq + r'(?: [Ee]{1}ach)?:\s*([^\.]+)', line)
                if freq_match:
                    data['limited_use'].append({
                        'frequency': freq,
                        'spells': self._parse_spell_list(freq_match.group(1))
                    })

    def _parse_regular_spells(self, text: str, data: Dict) -> None:
        """Parse regular spellcasting details."""
        lines = text.splitlines()
        for line in lines:
            # Parse cantrips
            cantrip_match = re.search(r'Cantrips \(at will\):\s*([^\.]+)', line)
            if cantrip_match:
                data['at_will'] = self._parse_spell_list(cantrip_match.group(1))
                continue

            # Parse spell slots
            slot_pattern = r'(\d)(?:st|nd|rd|th) level \((\d) slots?\):\s*([^\.]+)'
            for match in re.finditer(slot_pattern, line):
                level = int(match.group(1))
                slots = int(match.group(2))
                spells = self._parse_spell_list(match.group(3))
                data['spell_slots'].append({
                    'level': level,
                    'slots': slots,
                    'spells': spells
                })

    def _parse_spell_list(self, text: str) -> List[Dict]:
        """Parse comma-separated spell list with optional notes."""
        spells = []
        for spell in text.split(','):
            spell = spell.strip()
            if not spell:
                continue
            # Check for notes in parentheses
            note_match = re.search(r'(.*?)\s*\((.*?)\)', spell)
            if note_match:
                spells.append({
                    'name': note_match.group(1).strip(),
                    'notes': note_match.group(2).strip()
                })
            else:
                spells.append({'name': spell})
        return spells