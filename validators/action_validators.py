from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from enum import Enum

class AttackType(str, Enum):
    MELEE_WEAPON = "melee_weapon"
    RANGED_WEAPON = "ranged_weapon"
    MELEE_SPELL = "melee_spell"
    RANGED_SPELL = "ranged_spell"

class Attack(BaseModel):
    type: AttackType
    bonus: int
    ability_used: Optional[str]
    magical_bonus: Optional[int]
    is_finesse: Optional[bool]
    reach: Optional[str]
    range: Optional[str]

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
