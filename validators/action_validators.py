import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from enum import Enum

class WeaponType(str, Enum):
    WEAPON = "weapon"
    SPELL = "spell"

class UsageType(str, Enum):
    RECHARGE = "recharge"
    PER_DAY = "per_day"
    PER_SHORT_REST = "per_short_rest"
    PER_LONG_REST = "per_long_rest"
    COSTS = "costs"

class Usage(BaseModel):
    type: UsageType
    value: Optional[int] = None
    times: Optional[int] = None
    range: Optional[List[int]] = None

    @field_validator('range')
    @classmethod
    def validate_range(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            # Ensure values are 1-6
            if not all(1 <= x <= 6 for x in v):
                raise ValueError('Recharge range values must be between 1 and 6')
            # Ensure sorted and consecutive
            if sorted(v) != list(range(min(v), max(v) + 1)):
                raise ValueError('Recharge range must be consecutive numbers')
        return v

    @field_validator('value')
    @classmethod
    def validate_value(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        if v is not None:
            usage_type = info.data.get('type')
            if usage_type == UsageType.COSTS and not (1 <= v <= 20):
                raise ValueError('Cost value must be between 1 and 20')
            elif usage_type == UsageType.RECHARGE and not (1 <= v <= 6):
                raise ValueError('Recharge value must be between 1 and 6')
        return v

    @field_validator('times')
    @classmethod
    def validate_times(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        if v is not None and not (1 <= v <= 10):
            raise ValueError('Times value must be between 1 and 10')
        return v

class Attack(BaseModel):
    weapon_type: WeaponType
    is_melee: bool
    is_ranged: bool
    bonus: int
    ability_used: Optional[str]
    magical_bonus: Optional[int]
    reach: Optional[str]  # Only used if is_melee is True
    range: Optional[str]  # Only used if is_ranged is True

    @field_validator('reach')
    @classmethod
    def validate_reach(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        if v and not info.data.get('is_melee', False):
            raise ValueError('Reach can only be specified for melee attacks')
        return v

    @field_validator('range')
    @classmethod
    def validate_range(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        if v and not info.data.get('is_ranged', False):
            raise ValueError('Range can only be specified for ranged attacks')
        return v

    @field_validator('is_melee', 'is_ranged')
    @classmethod
    def validate_attack_types(cls, v: bool, info: ValidationInfo) -> bool:
        if not v and not info.data.get('is_melee', False) and not info.data.get('is_ranged', False):
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
    damage_two_handed: Optional[str] = None  # Two-handed damage formula for versatile weapons
    damage_type: str
    additional_effects: Optional[str]

    @field_validator('damage_two_handed')
    @classmethod
    def validate_two_handed_damage(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Check for valid dice formula pattern
            if not re.match(r'^\d+d\d+(?:\s*[+-]\s*\d+)?$', v):
                raise ValueError('Invalid two-handed damage formula')
        return v

class Action(BaseModel):
    name: str
    description: str
    attack: Optional[Attack]
    hit: Optional[DamageRoll]
    usage: Optional[Usage] = None

class LegendaryAction(BaseModel):
    name: str
    description: str
    cost: int
    usage: Optional[Usage] = None

    @field_validator('cost')
    @classmethod
    def validate_cost(cls, v: int) -> int:
        if not (1 <= v <= 3):
            raise ValueError('Legendary action cost must be between 1 and 3')
        return v

class LairAction(BaseModel):
    name: str
    description: str
    usage: Optional[Usage] = None

class RegionalEffectMechanics(BaseModel):
    save_dc: int = Field(ge=1, le=30)
    save_type: str = Field(
        pattern=r'^(strength|dexterity|constitution|intelligence|wisdom|charisma)$'
    )
    effects: str = Field(min_length=1)

class RegionalEffect(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    mechanics: Optional[RegionalEffectMechanics] = None

class RegionalEffects(BaseModel):
    range: str = Field(pattern=r"^\d+ (?:feet|miles)$")
    duration: str = Field(min_length=1)
    effects: List[RegionalEffect] = Field(min_items=1)

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
