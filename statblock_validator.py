from pydantic import BaseModel, field_validator, ValidationInfo
from typing import List, Optional, Dict
from datetime import date
import re
from validators.action_validators import ActionSet, LegendaryActionSet, LairActionSet, RegionalEffect, RegionalEffects
from validators.spellcasting_validators import SpellcastingTrait
from validators.ability_validators import calculate_proficiency_bonus
from validators.challenge_rating_validators import ChallengeRating
from parsers.damage_type_parser import DamageTypeParser

class Metadata(BaseModel):
    name: str
    title: Optional[str] = None
    version: str
    date_created: date
    last_modified: Optional[date] = None
    source: str
    tags: Optional[List[str]] = None

class CreatureInfo(BaseModel):
    size: str
    type: str
    subtypes: Optional[List[str]] = None
    alignment: str
    challenge_rating: ChallengeRating

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
    special: Optional[str] = None

class Initiative(BaseModel):
    bonus: int
    average: int

class CoreStats(BaseModel):
    armor_class: ArmorClass
    hit_points: HitPoints
    speed: Speed
    initiative: Initiative

class AbilityScore(BaseModel):
    score: int
    modifier: int

class SavingThrow(BaseModel):
    ability: str
    modifier: int

class Skill(BaseModel):
    name: str
    modifier: int

class Proficiencies(BaseModel):
    saving_throws: Optional[List[SavingThrow]] = None
    skills: Optional[List[Skill]] = None
    bonus: Optional[int] = None

class Defenses(BaseModel):
    damage_resistances: Optional[List[str]] = None
    damage_immunities: Optional[List[str]] = None
    condition_immunities: Optional[List[str]] = None

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

class Description(BaseModel):
    unparsed_text: Optional[str] = None # Original text before classification
    appearance: Optional[str] = None
    personality: Optional[str] = None  
    background: Optional[str] = None
    tactics: Optional[str] = None

class StatBlockValidator(BaseModel):
    """Pydantic model for stat block validation"""
    metadata: Metadata
    creature_info: CreatureInfo
    core_stats: CoreStats    
    abilities: Dict[str, AbilityScore]
    proficiency: Proficiencies
    defenses: Optional[Defenses]    
    senses: Senses
    languages: Languages
    traits: Optional[List[dict]] = None
    spellcasting: Optional[SpellcastingTrait] = None
    actions: ActionSet
    legendary_actions: Optional[LegendaryActionSet] = None
    lair_actions: Optional[LairActionSet] = None
    regional_effects: Optional[RegionalEffects] = None
    description: Optional[Description] = None
    additional_info: Optional[Dict[str, Optional[List[str]]]] = None

    @field_validator('alignment')
    @classmethod
    def validate_alignment(cls, v: str) -> str:
        if not re.match(r'^(lawful|neutral|chaotic)? ?(good|neutral|evil)?$', v) and v != 'unaligned':
            raise ValueError('Invalid alignment')
        return v

    @field_validator('armor_class')
    @classmethod
    def validate_armor_class(cls, v: ArmorClass) -> int:
        if not (0 <= v.value <= 30):
            raise ValueError('Armor class must be between 0 and 30')
        return v

    @field_validator('hit_points')
    @classmethod
    def validate_hit_points(cls, v: HitPoints) -> int:
        if v.average < 1:
            raise ValueError('Hit points must be at least 1')
        return v

    @field_validator('speed')
    @classmethod
    def validate_speed(cls, v: Speed) -> dict:
        for key, value in v.model_dump().items():
            if value is None:
                continue
            if key in ['walk', 'fly', 'swim', 'burrow', 'climb'] and (value % 5 != 0 or not (0 <= value <= 120)):
                raise ValueError(f'{key} speed must be a multiple of 5 and between 0 and 120')
        return v

    @field_validator('proficiency_bonus', mode='before')
    @classmethod
    def validate_proficiency_bonus(cls, v: Optional[int], info: ValidationInfo) -> int:
        cr = info.data.get('challenge_rating')
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
    def validate_senses(cls, v: Senses) -> dict:
        for key, value in v.model_dump().items():
            if value is None:
                continue
            if key in ['darkvision', 'blindsight', 'tremorsense', 'truesight'] and (value % 5 != 0 or not (0 <= value <= 120)):
                raise ValueError(f'{key} must be a multiple of 5 and between 0 and 120')
            if key == 'passive_perception' and not (0 <= value <= 30):
                raise ValueError('Passive perception must be between 0 and 30')
        return v

    @field_validator('regional_effects', mode='after')  # Change mode to 'after'
    @classmethod
    def validate_regional_effects(cls, v: Optional[RegionalEffects], info: ValidationInfo) -> Optional[RegionalEffects]:
        if v is not None:
            abilities = info.data.get('abilities', {})
            proficiency = info.data.get('proficiency_bonus')
            
            # Only validate save DCs if mechanics are present
            if any(effect.mechanics for effect in v.effects):
                if not abilities or proficiency is None:
                    # Just log a warning during conversion
                    print("Warning: Deferring save DC validation until final validation")
                    return v
                    
                for effect in v.effects:
                    if effect.mechanics and effect.mechanics.save_dc:
                        save_dc = effect.mechanics.save_dc
                        ability_mod = abilities.get(effect.mechanics.save_type, {}).get('modifier', 0)
                        expected_dc = 8 + proficiency + ability_mod
                        
                        if save_dc != expected_dc:
                            raise ValueError(f'Save DC {save_dc} does not match expected DC {expected_dc} for {effect.name}')
        return v

    @field_validator('damage_resistances')
    @classmethod
    def validate_damage_resistances(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        
        for resistance in v:
            if not DamageTypeParser.validate_damage_type(resistance):
                raise ValueError(f'Invalid damage resistance type: {resistance}')
        return v

    @field_validator('damage_immunities')
    @classmethod
    def validate_damage_immunities(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        
        for immunity in v:
            if not DamageTypeParser.validate_damage_type(immunity):
                raise ValueError(f'Invalid damage immunity type: {immunity}')
        return v

    class Config:
        extra = 'allow'  # Allow extra fields
