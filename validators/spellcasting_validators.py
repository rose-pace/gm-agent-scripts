from pydantic import BaseModel, ValidationInfo, field_validator
from typing import List, Optional
from enum import Enum

class SpellcastingType(str, Enum):
    INNATE = "Innate"
    REGULAR = "Regular"
    PACT_MAGIC = "Pact Magic"

class SpellcastingAbility(str, Enum):
    INTELLIGENCE = "Intelligence"
    WISDOM = "Wisdom"
    CHARISMA = "Charisma"

class Spell(BaseModel):
    name: str
    notes: Optional[str] = None

class SpellLevel(BaseModel):
    level: int
    slots: int
    spells: List[Spell]

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: int) -> int:
        if not (0 <= v <= 9):
            raise ValueError('Spell level must be between 0 and 9')
        return v

    @field_validator('slots')
    @classmethod
    def validate_slots(cls, v: int) -> int:
        if not (1 <= v <= 4):
            raise ValueError('Spell slots must be between 1 and 4')
        return v

class LimitedUseSpells(BaseModel):
    frequency: str  # e.g., "3/day"
    spells: List[Spell]

    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        if not any(v.endswith(period) for period in ['/day', '/short rest', '/long rest']):
            raise ValueError('Frequency must end with /day, /short rest, or /long rest')
        try:
            uses = int(v.split('/')[0])
            if uses < 1:
                raise ValueError
        except ValueError:
            raise ValueError('Frequency must start with a positive number')
        return v

class SpecialBonus(BaseModel):
    description: str
    value: int

class SpellcastingTrait(BaseModel):
    type: SpellcastingType
    ability: SpellcastingAbility
    dc: int
    attack_bonus: int
    base_modifier: int
    special_bonuses: Optional[List[SpecialBonus]] = None
    at_will: Optional[List[Spell]] = None
    spell_slots: Optional[List[SpellLevel]] = None
    limited_use: Optional[List[LimitedUseSpells]] = None

    @field_validator('dc')
    @classmethod
    def validate_dc(cls, v: int, info: ValidationInfo) -> int:
        if not (0 <= v <= 30):
            raise ValueError('Spell save DC must be between 0 and 30')
        # Validate DC matches ability modifier + proficiency + 8
        ability_mod = info.data.get('base_modifier')
        if ability_mod is not None:
            proficiency = info.data.get('proficiency_bonus', 2)  # Default to 2 if not provided
            expected_dc = 8 + ability_mod + proficiency
            if v != expected_dc:
                raise ValueError(f'DC {v} does not match calculated DC {expected_dc}')
        return v

    @field_validator('attack_bonus')
    @classmethod
    def validate_attack_bonus(cls, v: int, info: ValidationInfo) -> int:
        if not (0 <= v <= 30):
            raise ValueError('Spell attack bonus must be between 0 and 30')
        # Validate attack bonus matches ability modifier + proficiency
        ability_mod = info.data.get('base_modifier')
        if ability_mod is not None:
            proficiency = info.data.get('proficiency_bonus', 2)
            expected_bonus = ability_mod + proficiency
            if v != expected_bonus:
                raise ValueError(f'Attack bonus {v} does not match calculated bonus {expected_bonus}')
        return v

    @field_validator('base_modifier')
    @classmethod
    def validate_base_modifier(cls, v: int) -> int:
        if not (-5 <= v <= 10):
            raise ValueError('Base modifier must be between -5 and +10')
        return v

    @field_validator('special_bonuses')
    @classmethod
    def validate_special_bonuses(cls, v: Optional[List[SpecialBonus]]) -> Optional[List[SpecialBonus]]:
        if v is None:
            return v
        # Ensure total bonus doesn't exceed reasonable limits
        total_bonus = sum(bonus.value for bonus in v)
        if total_bonus > 10:  # Maximum reasonable total bonus
            raise ValueError('Total special bonuses exceed reasonable limits')
        return v
