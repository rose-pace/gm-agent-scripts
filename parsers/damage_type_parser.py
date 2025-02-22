from typing import List

class DamageTypeParser:
    # Standard damage types that can't be modified by nonmagical
    ENERGY_DAMAGE_TYPES = {
        'acid', 'cold', 'fire', 'force', 'lightning',
        'necrotic', 'poison', 'psychic', 'radiant', 'thunder'
    }
    
    # Physical damage types that can be modified by nonmagical
    PHYSICAL_DAMAGE_TYPES = {
        'bludgeoning', 'piercing', 'slashing'
    }
    
    @classmethod
    def parse_damage_types(cls, text: str) -> List[str]:
        """Parse damage types from text, handling nonmagical modifiers correctly."""
        if not text:
            return []
        
        damage_types = set()
        groups = [g.strip() for g in text.split(';')]
        
        for group in groups:
            is_nonmagical = 'nonmagical' in group.lower()
            types = [t.strip().lower() for t in group.split(',')]
            
            for damage_type in types:
                # Skip connecting words
                if damage_type in {'and', 'or', ''} or damage_type.startswith('from'):
                    continue
                
                # Clean up the damage type
                clean_type = damage_type.replace('damage', '').strip()
                
                # Handle base damage type
                base_type = next((t for t in cls.PHYSICAL_DAMAGE_TYPES | cls.ENERGY_DAMAGE_TYPES 
                                if t in clean_type), None)
                
                if base_type:
                    if is_nonmagical and base_type in cls.PHYSICAL_DAMAGE_TYPES:
                        damage_types.add(f'nonmagical {base_type}')
                    else:
                        damage_types.add(base_type)
        
        return sorted(list(damage_types))

    @classmethod
    def validate_damage_type(cls, damage_type: str) -> bool:
        """Validate a single damage type string."""
        if not damage_type:
            return False
            
        parts = damage_type.lower().split()
        
        if len(parts) == 2 and parts[0] == 'nonmagical':
            # Only physical damage types can be nonmagical
            return parts[1] in cls.PHYSICAL_DAMAGE_TYPES
        elif len(parts) == 1:
            # Single word must be a valid damage type
            return parts[0] in cls.PHYSICAL_DAMAGE_TYPES | cls.ENERGY_DAMAGE_TYPES
            
        return False
