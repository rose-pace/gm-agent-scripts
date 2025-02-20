from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict
from datetime import date
import re
from validators.action_validators import ActionSet, LegendaryActionSet, LairActionSet, RegionalEffect
from validators.spellcasting_validators import SpellcastingTrait
from validators.ability_validators import calculate_proficiency_bonus
from validators.challenge_rating_validators import ChallengeRating

class Metadata(BaseModel):
    name: str
    title: Optional[str] = None
    version: str
    date_created: date
    last_modified: Optional[date] = None
    source: str
    tags: Optional[List[str]] = None

class ArmorClass(BaseModel):
    value: int
    type: Optional[str] = None

class HitPoints(BaseModel):
    average: int
    roll: str

class Speed(BaseModel):
    walk: Optional[int] = None
    fly: Optional[int] = None
    swim: Optional[int] = None
    burrow: Optional[int] = None
    climb: Optional[int] = None
    hover: Optional[bool] = None
    units: str = "ft."
    special: Optional[str] = None

class AbilityScore(BaseModel):
    score: int
    modifier: int

class SavingThrow(BaseModel):
    ability: str
    modifier: int

class Skill(BaseModel):
    name: str
    modifier: int

class Senses(BaseModel):
    darkvision: Optional[int] = None
    blindsight: Optional[int] = None
    tremorsense: Optional[int] = None
    truesight: Optional[int] = None
    passive_perception: int
    special: Optional[List[str]] = None

class Languages(BaseModel):
    spoken: List[str]
    telepathy: Optional[int] = None
    special: Optional[str] = None

class StatBlockValidator(BaseModel):
    """Pydantic model for stat block validation"""
    metadata: Metadata
    size: str
    type: str
    subtypes: Optional[List[str]] = None
    alignment: str
    armor_class: ArmorClass
    hit_points: HitPoints
    speed: Speed
    abilities: Dict[str, AbilityScore]
    saving_throws: Optional[List[SavingThrow]] = None
    skills: Optional[List[Skill]] = None
    damage_resistances: Optional[List[str]] = None
    damage_immunities: Optional[List[str]] = None
    condition_immunities: Optional[List[str]] = None
    senses: Senses
    languages: Languages
    traits: Optional[List[dict]] = None
    spellcasting: Optional[SpellcastingTrait] = None
    actions: ActionSet
    legendary_actions: Optional[LegendaryActionSet] = None
    lair_actions: Optional[LairActionSet] = None
    regional_effects: Optional[List[RegionalEffect]] = None
    description: Optional[Dict[str, Optional[str]]] = None
    additional_info: Optional[Dict[str, Optional[List[str]]]] = None
    challenge_rating: ChallengeRating
    proficiency_bonus: Optional[int] = None

    @field_validator('alignment')
    @classmethod
    def validate_alignment(cls, v: str) -> str:
        if not re.match(r'^(lawful|neutral|chaotic)? ?(good|neutral|evil)?$', v) and v != 'unaligned':
            raise ValueError('Invalid alignment')
        return v

    @field_validator('armor_class')
    @classmethod
    def validate_armor_class(cls, v: int) -> int:
        if not (0 <= v <= 30):
            raise ValueError('Armor class must be between 0 and 30')
        return v

    @field_validator('hit_points')
    @classmethod
    def validate_hit_points(cls, v: int) -> int:
        if v < 1:
            raise ValueError('Hit points must be at least 1')
        return v

    @field_validator('speed')
    @classmethod
    def validate_speed(cls, v: dict) -> dict:
        for key, value in v.items():
            if key in ['walk', 'fly', 'swim', 'burrow', 'climb'] and (value % 5 != 0 or not (0 <= value <= 120)):
                raise ValueError(f'{key} speed must be a multiple of 5 and between 0 and 120')
        return v

    @field_validator('proficiency_bonus', mode='before')
    @classmethod
    def validate_proficiency_bonus(cls, v: Optional[int], values: Dict) -> int:
        cr = values.get('challenge_rating')
        if cr is None:
            raise ValueError('Challenge rating is required to validate proficiency bonus')
            
        rating = cr.rating
        if isinstance(rating, str):
            # Handle fraction strings
            if '/' in rating:
                num, denom = rating.split('/')
                rating = float(int(num) / int(denom))
            else:
                rating = float(rating)
                
        expected = calculate_proficiency_bonus(rating)
        if v is not None and v != expected:
            raise ValueError(f'Proficiency bonus {v} does not match CR {rating} (should be {expected})')
        return expected

    @field_validator('senses')
    @classmethod
    def validate_senses(cls, v: dict) -> dict:
        for key, value in v.items():
            if key in ['darkvision', 'blindsight', 'tremorsense', 'truesight'] and (value % 5 != 0 or not (0 <= value <= 120)):
                raise ValueError(f'{key} must be a multiple of 5 and between 0 and 120')
            if key == 'passive_perception' and not (0 <= value <= 30):
                raise ValueError('Passive perception must be between 0 and 30')
        return v

    class Config:
        extra = 'allow'  # Allow extra fields
