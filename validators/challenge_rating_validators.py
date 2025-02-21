from pydantic import BaseModel, ValidationInfo, field_validator
from typing import Union
from fractions import Fraction
from .dnd_constants import CR_TO_XP

class ChallengeRating(BaseModel):
    rating: Union[float, str]  # Can be float or fraction string like "1/4"
    xp: int

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: Union[float, str]) -> Union[float, str]:
        if isinstance(v, str):
            # Handle fraction strings
            if '/' in v:
                try:
                    Fraction(v)  # Validate fraction format
                except ValueError:
                    raise ValueError(f'Invalid CR fraction: {v}')
            else:
                try:
                    float(v)  # Validate numeric string
                except ValueError:
                    raise ValueError(f'Invalid CR value: {v}')
        elif isinstance(v, (int, float)):
            if not (0 <= v <= 30):
                raise ValueError('CR must be between 0 and 30')
        else:
            raise ValueError('CR must be a number or fraction string')
        return v

    @field_validator('xp')
    @classmethod
    def validate_xp(cls, v: int, info: ValidationInfo) -> int:
        rating = info.data.get('rating')
        if rating is None:
            raise ValueError('CR rating is required to validate XP')

        # Convert rating to string key for lookup
        key = str(rating) if isinstance(rating, (str, int)) else float(rating)
        
        # Get expected XP
        expected_xp = CR_TO_XP.get(key)
        if expected_xp is None:
            raise ValueError(f'Invalid CR value for XP lookup: {rating}')
        
        if v != expected_xp:
            raise ValueError(f'XP value {v} does not match expected value {expected_xp} for CR {rating}')
        
        return v
