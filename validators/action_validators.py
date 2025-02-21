from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from enum import Enum

class WeaponType(str, Enum):
    WEAPON = "weapon"
    SPELL = "spell"

class Attack(BaseModel):
    weapon_type: WeaponType
    is_melee: bool
    is_ranged: bool
    bonus: int
    ability_used: Optional[str]
    magical_bonus: Optional[int]
    is_finesse: Optional[bool]
    reach: Optional[str]  # Only used if is_melee is True
    range: Optional[str]  # Only used if is_ranged is True

    @field_validator('reach')
    @classmethod
    def validate_reach(cls, v: Optional[str], values: dict) -> Optional[str]:
        if v and not values.get('is_melee', False):
            raise ValueError('Reach can only be specified for melee attacks')
        return v

    @field_validator('range')
    @classmethod
    def validate_range(cls, v: Optional[str], values: dict) -> Optional[str]:
        if v and not values.get('is_ranged', False):
            raise ValueError('Range can only be specified for ranged attacks')
        return v

    @field_validator('is_melee', 'is_ranged')
    @classmethod
    def validate_attack_types(cls, v: bool, values: dict) -> bool:
        if not v and not values.get('is_melee', False) and not values.get('is_ranged', False):
            raise ValueError('Attack must be either melee, ranged, or both')
        return v

    @field_validator('magical_bonus')
    @classmethod
    def validate_magical_bonus(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (0 <= v <= 3):
            raise ValueError('Magical bonus must be between 0 and 3')
        return v

class DamageRoll(BaseModel):
    damage: str  # Damage dice/formula
    damage_type: str
    additional_effects: Optional[str]

class Action(BaseModel):
    name: str
    description: str
    attack: Optional[Attack]
    hit: Optional[DamageRoll]
    usage: Optional[str]

class LegendaryAction(BaseModel):
    name: str
    description: str
    cost: int
    usage: Optional[str]

    @field_validator('cost')
    @classmethod
    def validate_cost(cls, v: int) -> int:
        if not (1 <= v <= 3):
            raise ValueError('Legendary action cost must be between 1 and 3')
        return v

class LairAction(BaseModel):
    name: str
    description: str
    usage: Optional[str]

class RegionalEffect(BaseModel):
    name: str
    description: str
    mechanics: Optional[dict]

class ActionSet(BaseModel):
    standard: List[Action]
    bonus_actions: Optional[List[Action]]
    reactions: Optional[List[Action]]

class LegendaryActionSet(BaseModel):
    slots_per_round: int
    description: str
    actions: List[LegendaryAction]

    @field_validator('slots_per_round')
    @classmethod
    def validate_slots(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError('Legendary action slots must be between 1 and 5')
        return v

class LairActionSet(BaseModel):
    initiative_count: int
    description: str
    actions: List[LairAction]

    @field_validator('initiative_count')
    @classmethod
    def validate_initiative(cls, v: int) -> int:
        if not (0 <= v <= 20):
            raise ValueError('Initiative count must be between 0 and 20')
        return v
