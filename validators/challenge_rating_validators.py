from pydantic import BaseModel, ValidationInfo, field_validator
from typing import Union, ClassVar
from fractions import Fraction

class ChallengeRating(BaseModel):
    rating: Union[float, str]  # Can be float or fraction string like "1/4"
    xp: int

    # CR to XP mapping as per D&D 5e rules
    CR_TO_XP: ClassVar = {
        0: 0,       "0": 10,     "1/8": 25,    "1/4": 50,    "1/2": 100,
        1: 200,     2: 450,      3: 700,       4: 1100,      5: 1800,
        6: 2300,    7: 2900,     8: 3900,      9: 5000,      10: 5900,
        11: 7200,   12: 8400,    13: 10000,    14: 11500,    15: 13000,
        16: 15000,  17: 18000,   18: 20000,    19: 22000,    20: 25000,
        21: 33000,  22: 41000,   23: 50000,    24: 62000,    25: 75000,
        26: 90000,  27: 105000,  28: 120000,   29: 135000,   30: 155000
    }

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
        expected_xp = cls.CR_TO_XP.get(key)
        if expected_xp is None:
            raise ValueError(f'Invalid CR value for XP lookup: {rating}')
        
        if v != expected_xp:
            raise ValueError(f'XP value {v} does not match expected value {expected_xp} for CR {rating}')
        
        return v
