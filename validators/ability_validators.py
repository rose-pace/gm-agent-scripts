from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from enum import Enum

# TODO: This code isn't currenly used but may be valuable to update the validator to use it

# class AbilityScore(BaseModel):
#     score: int
#     modifier: int

#     @field_validator('score')
#     @classmethod
#     def validate_score(cls, v: int) -> int:
#         if not (1 <= v <= 30):
#             raise ValueError('Ability score must be between 1 and 30')
#         return v

#     @field_validator('modifier')
#     @classmethod
#     def validate_modifier(cls, score: int, modifier: int) -> int:
#         expected = (score - 10) // 2
#         if modifier != expected:
#             raise ValueError(f'Ability modifier must be {expected} for score {score}')
#         return modifier

# class SkillProficiency(str, Enum):
#     NONE = "none"
#     PROFICIENT = "proficient"
#     EXPERT = "expert"

# class Skill(BaseModel):
#     name: str
#     ability: str
#     proficiency: SkillProficiency
#     bonus: int

#     @field_validator('bonus')
#     @classmethod
#     def validate_bonus(cls, v: int, values: Dict) -> int:
#         ability_mod = values.get('ability_modifier', 0)
#         prof_bonus = values['proficiencies'].get('bonus', 2)  # Default to 2 if not provided
        
#         if values.get('proficiency') == SkillProficiency.EXPERT:
#             expected = ability_mod + (prof_bonus * 2)
#         elif values.get('proficiency') == SkillProficiency.PROFICIENT:
#             expected = ability_mod + prof_bonus
#         else:
#             expected = ability_mod
            
#         if v != expected:
#             raise ValueError(f'Skill bonus {v} does not match calculated value {expected}')
#         return v

# class SavingThrow(BaseModel):
#     ability: str
#     proficient: bool
#     bonus: int

#     @field_validator('bonus')
#     @classmethod
#     def validate_bonus(cls, v: int, values: Dict) -> int:
#         ability_mod = values.get('ability_modifier', 0)
#         prof_bonus = values['proficiencies'].get('bonus', 2)
        
#         expected = ability_mod + (prof_bonus if values.get('proficient') else 0)
#         if v != expected:
#             raise ValueError(f'Saving throw bonus {v} does not match calculated value {expected}')
#         return v

# class AbilitySet(BaseModel):
#     strength: AbilityScore
#     dexterity: AbilityScore
#     constitution: AbilityScore
#     intelligence: AbilityScore
#     wisdom: AbilityScore
#     charisma: AbilityScore
#     skills: Optional[List[Skill]]
#     saving_throws: Optional[List[SavingThrow]]

#     @field_validator('skills')
#     @classmethod
#     def validate_skills(cls, v: Optional[List[Skill]], values: Dict) -> Optional[List[Skill]]:
#         if v is not None:
#             ability_scores = {
#                 'strength': values.get('strength'),
#                 'dexterity': values.get('dexterity'),
#                 'constitution': values.get('constitution'),
#                 'intelligence': values.get('intelligence'),
#                 'wisdom': values.get('wisdom'),
#                 'charisma': values.get('charisma')
#             }
            
#             for skill in v:
#                 if skill.ability in ability_scores:
#                     skill.ability_modifier = ability_scores[skill.ability].modifier
#         return v

def calculate_proficiency_bonus(cr: str) -> int:
    """Calculate proficiency bonus based on Challenge Rating."""
    # Convert CR to a number, handling fractions
    rating = 1
    if '/' not in cr:
        rating = int(cr)
        
    if rating < 1:
        return 2
    return 2 + ((rating - 1) // 4)
