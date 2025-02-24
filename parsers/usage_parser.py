import re
from typing import Optional, Dict

class UsageParser:
    """Parser for usage/recharge mechanics."""

    # Usage patterns
    USAGE_PATTERNS = {
        'recharge': r'recharge (\d+)(?:-(\d+))?',
        'per_day': r'(\d+)/day',
        'per_short_rest': r'(\d+)/short rest',
        'per_long_rest': r'(\d+)/long rest',
        'costs': r'costs? (\d+)',
    }

    @classmethod
    def parse_usage(cls, description: str) -> Optional[Dict]:
        """Parse usage restrictions from ability description."""
        description_lower = description.lower()
        
        # Check for recharge
        recharge_match = re.search(cls.USAGE_PATTERNS['recharge'], description_lower)
        if recharge_match:
            start = int(recharge_match.group(1))
            end = int(recharge_match.group(2)) if recharge_match.group(2) else start
            return {
                'type': 'recharge',
                'value': start if start == end else None,
                'range': list(range(start, end + 1)) if start != end else None
            }
        
        # Check for per day
        per_day_match = re.search(cls.USAGE_PATTERNS['per_day'], description_lower)
        if per_day_match:
            return {
                'type': 'per_day',
                'times': int(per_day_match.group(1))
            }
            
        # Check for per short rest
        short_rest_match = re.search(cls.USAGE_PATTERNS['per_short_rest'], description_lower)
        if short_rest_match:
            return {
                'type': 'per_short_rest',
                'times': int(short_rest_match.group(1))
            }
            
        # Check for per long rest
        long_rest_match = re.search(cls.USAGE_PATTERNS['per_long_rest'], description_lower)
        if long_rest_match:
            return {
                'type': 'per_long_rest',
                'times': int(long_rest_match.group(1))
            }
            
        # Check for resource cost
        cost_match = re.search(cls.USAGE_PATTERNS['costs'], description_lower)
        if cost_match:
            return {
                'type': 'costs',
                'value': int(cost_match.group(1))
            }
        
        return None
