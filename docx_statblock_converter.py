from typing import Any, Dict, List
import unicodedata
import re
from datetime import datetime
from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph
from rich.console import Console
from rich.table import Table
from statblock_validator import StatBlockValidator
from parsers.spellcasting_parser import SpellcastingParser
from validators.action_validators import WeaponType
from validators.dnd_constants import CR_TO_XP  # Add this import

class DocxStatBlockConverter:
    def __init__(self, collection: str = None, tags: List[str] = None):
        """Initialize converter with validation rules."""
        self.collection = collection
        self.tags = tags or []
        self.current_creature = {}
        self.console = Console()

    def extract_text_from_docx(self, docx_path: str) -> Dict[str, List[Paragraph]]:
        """
        Extract text from DOCX file while preserving formatting.
        Returns dictionary of sections with their paragraphs.
        """
        doc = Document(docx_path)
        sections = {}
        current_section = 'corestats'
        current_paragraphs = []

        for paragraph in doc.paragraphs:
            # Check if this is a main header
            if self._is_main_header(paragraph):
                sections['header'] = self._normalize_text(paragraph.text)
            # Check if this is a subheader
            elif self._is_subheader(paragraph):
                sections['subheader'] = self._normalize_text(paragraph.text)
            # Check if this is a section header
            elif self._is_section_header(paragraph):
                # Save previous section
                if current_paragraphs:
                    sections[current_section] = current_paragraphs
                # Start new section
                current_section = self._get_section_name(paragraph.text)
                current_paragraphs = []
            else:
                # Skip empty paragraphs
                if paragraph.text.strip():
                    current_paragraphs.append(paragraph)

        # Add last section
        if current_paragraphs:
            sections[current_section] = current_paragraphs

        return sections
    
    def _is_main_header(self, paragraph: Paragraph) -> bool:
        """
        Check if paragraph is a main header based on formatting.
        """
        return paragraph.style.name.lower() == 'heading 1'
    
    def _is_subheader(self, paragraph: Paragraph) -> bool:
        """
        Check if paragraph is a subheader based on formatting.
        """
        return paragraph.style.name.lower() == 'heading 2'

    def _is_section_header(self, paragraph: Paragraph) -> bool:
        """
        Check if paragraph is a section header based on formatting.
        """
        # Check for bold formatting or specific styles
        return paragraph.style.name.lower() == 'heading 3'

    def _get_section_name(self, text: str) -> str:
        """Convert section header text to section identifier."""
        clean_text = text.lower().strip().strip('.')
        return self.SECTION_MARKERS.get(clean_text, clean_text)

    def convert_docx_to_schema(self, docx_path: str) -> Dict:
        """Convert DOCX stat block to schema format."""
        sections = self.extract_text_from_docx(docx_path)
        
        # Initialize with required fields
        self.current_creature = {
            'metadata': {
                'name': sections['header'],  # Name belongs in metadata
                'version': '1.0',
                'date_created': datetime.now().strftime('%Y-%m-%d'),
                'last_modified': datetime.now().strftime('%Y-%m-%d'),
                'source': Path(docx_path).name,
                'collection': self.collection,
                'tags': self.tags
            },
            'damage_resistances': [],
            'damage_immunities': [],
            'condition_immunities': [],
            'senses': {
                'passive_perception': 10,
                'special': []
            },
            'languages': {
                'spoken': []
            },
            'description': {
                'appearance': None,
                'personality': None,
                'background': None,
                'tactics': None
            },
            'additional_info': {
                'variant_rules': [],
                'notes': []
            }
        }
        
        # Process main sections
        self._process_subheader(sections['subheader'])
        self._process_core_stats(sections.get('corestats', []))
        self._process_abilities(sections.get('corestats', []))
        self._process_defenses(sections.get('corestats', []))
        self._process_senses_and_languages(sections.get('corestats', []))
        self._process_traits(sections.get('traits', []))
        
        # Process actions
        standard_actions = self._process_actions(sections.get('actions', []), "standard")
        bonus_actions = self._process_actions(sections.get('bonus_actions', []), "bonus")
        reactions = self._process_actions(sections.get('reactions', []), "reaction")
        
        self.current_creature["actions"] = {
            'standard': standard_actions,
            'bonus_actions': bonus_actions if bonus_actions else None,
            'reactions': reactions if reactions else None
        }
        
        # Process optional sections
        if 'legendary_actions' in sections:
            self._process_legendary_actions(sections['legendary_actions'])
        if 'lair_actions' in sections:
            self._process_lair_actions(sections['lair_actions'])
        if 'regional_effects' in sections:
            self._process_regional_effects(sections['regional_effects'])

        # Validate converted data
        self._validate_converted_data()
        
        return self.current_creature

    def _validate_converted_data(self) -> None:
        """
        Validate converted data using Pydantic model.
        """
        try:
            StatBlockValidator(**self.current_creature)
        except Exception as e:
            self.console.print("[red]Validation Error:[/red]")
            self.console.print(e)
            raise

    def output_conversion_report(self) -> None:
        """
        Generate a detailed report of the conversion process.
        """
        table = Table(title="Conversion Report")
        table.add_column("Section", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Notes", style="yellow")
        
        # Add rows for each processed section
        for section, status in self.conversion_status.items():
            table.add_row(
                section,
                "✓" if status['success'] else "✗",
                status.get('notes', '')
            )
        
        # Print to console
        self.console.print(table)

    # Constants and patterns
    SECTION_MARKERS = {
        'actions': 'actions',
        'legendary actions': 'legendary_actions',
        'lair actions': 'lair_actions',
        'regional effects': 'regional_effects',
        'traits': 'traits',
        'bonus actions': 'bonus_actions',
        'reactions': 'reactions'
    }

    MELEE_ATTACK_PATTERN = r'^Melee (?:Weapon|Spell) Attack:\s*(?P<bonus>[+-]\d+) to hit, reach (?P<distance>\d+ ft\.)'
    RANGED_ATTACK_PATTERN = r'^Ranged (?:Weapon|Spell) Attack:\s*(?P<bonus>[+-]\d+) to hit, range (?P<distance>\d+/\d+ ft\.)'

    def _process_subheader(self, subheader: str) -> None:
        """Process header section containing size, type, alignment."""
        if not subheader:
            raise ValueError("Incomplete header section")
        
        # Match pattern: "{size} {type} ({subtype}), {alignment}"
        pattern = r"^([\w\s]+) ([\w\s]+)(?: \(([\w\s,]+)\))?, ([\w\s]+)$"
        match = re.match(pattern, subheader)
        
        if not match:
            raise ValueError(f"Could not parse creature type line: {subheader}")
        
        self.current_creature.update({
            "size": match.group(1).strip(),
            "type": match.group(2).strip(),
            "subtype": match.group(3).strip() if match.group(3) else None,
            "alignment": match.group(4).strip()
        })

    def _process_core_stats(self, paragraphs: List[Paragraph]) -> None:
        """Process core statistics section."""
        for para in paragraphs:
            text = self._normalize_text(para.text)
            
            if text.startswith("Armor Class"):
                ac_match = re.match(r"Armor Class (\d+)(?: \(([\w\s,]+)\))?", text)
                if ac_match:
                    self.current_creature["armor_class"] = {
                        "value": int(ac_match.group(1)),
                        "type": ac_match.group(2) if ac_match.group(2) else None
                    }
            
            elif text.startswith("Hit Points"):
                hp_match = re.match(r"Hit Points (\d+)(?: \(([\d\w\s+]+)\))?", text)
                if hp_match:
                    self.current_creature["hit_points"] = {
                        "average": int(hp_match.group(1)),
                        "roll": hp_match.group(2) if hp_match.group(2) else None
                    }
            
            elif text.startswith("Challenge"):
                cr_match = re.match(r"Challenge (\d+(?:/\d+)?)\s*\(([,\d]+)\s*XP\)", text)
                if cr_match:
                    rating = cr_match.group(1)
                    # Lookup XP value based on CR rating rather than using the text value
                    xp = self._get_xp_for_cr(rating)
                    self.current_creature["challenge_rating"] = {
                        "rating": rating,
                        "xp": xp
                    }
            
            # Speed
            elif text.startswith("Speed"):
                speeds = {}
                speed_text = text.replace("Speed", "").strip()
                speed_parts = speed_text.split(", ")
                
                for part in speed_parts:
                    speed_match = re.match(r"(\w+)?\s*(\d+)\s*ft\.?", part)
                    if speed_match:
                        speed_type = speed_match.group(1) or "walk"
                        speeds[speed_type.lower()] = int(speed_match.group(2))
                
                self.current_creature["speed"] = speeds

    def _get_xp_for_cr(self, cr: str) -> int:
        """Get XP value for a given Challenge Rating."""
        return CR_TO_XP.get(str(cr), 0)

    def _process_abilities(self, paragraphs: List[Paragraph]) -> None:
        """Process abilities section - let Pydantic handle validation."""
        abilities = {}
        saving_throws = []
        skills = []
        
        for para in paragraphs:
            text = self._normalize_text(para.text)
            # Parse ability scores
            matches = re.finditer(r'(\w{3})\s+(\d+)\s*\(([+-]\d+)\)', text)
            for match in matches:
                ability = match.group(1).lower()
                score = int(match.group(2))
                modifier = int(match.group(3))
                abilities[ability] = {
                    'score': score,
                    'modifier': modifier
                }
            
            # Parse saving throws
            if text.startswith("Saving Throws"):
                saves = text.replace("Saving Throws", "").strip()
                for save in saves.split(", "):
                    save_match = re.match(r"(\w+)\s*([+-]\d+)", save)
                    if save_match:
                        saving_throws.append({
                            "ability": save_match.group(1).lower(),
                            "modifier": int(save_match.group(2))  # Changed from bonus to modifier
                        })
            
            # Parse skills
            elif text.startswith("Skills"):
                skill_text = text.replace("Skills", "").strip()
                for skill in skill_text.split(", "):
                    skill_match = re.match(r"(\w+(?:\s+\w+)?)\s*([+-]\d+)", skill)
                    if skill_match:
                        skills.append({
                            "name": skill_match.group(1),
                            "modifier": int(skill_match.group(2))  # Changed from bonus to modifier
                        })
        
        self.current_creature.update({
            "abilities": abilities,
            "saving_throws": saving_throws if saving_throws else None,
            "skills": skills if skills else None
        })

    def _normalize_text(self, text: str) -> str:
        """Strip text and remove non-breaking spaces."""
        return unicodedata.normalize('NFKC', text).strip()

    def _is_run_bold(self, run) -> bool:
        """
        Check if a run is bold using multiple methods.
        - Checks direct bold property
        - Checks for 'Strong' style
        - Checks font.bold property
        """
        return (
            run.bold or  # Direct bold property
            (hasattr(run, 'style') and run.style and 'Strong' in run.style.name) or  # Style name
            (hasattr(run, 'font') and run.font and run.font.bold)  # Font property
        )

    def _extract_name_from_bold_runs(self, paragraph: Paragraph) -> tuple[str, str]:
        """
        Extract name from contiguous bold runs at start of paragraph.
        Returns tuple of (name, remaining_text).
        """
        leading_bold = ''
        for run in paragraph.runs:
            if self._is_run_bold(run):
                name += run.text
            else:
                break
        
        name = self._normalize_text(leading_bold.strip(' .:'))
        description = self._normalize_text(paragraph.text[len(leading_bold):]).strip(' .:')
        return name, description

    def _process_actions(self, paragraphs: List[Paragraph], action_type: str = "standard") -> List[Dict]:
        """Process actions section with spell action detection."""
        actions = []
        current_action = None
        spellcasting_parser = SpellcastingParser()
        
        for para in paragraphs:
            if para.runs and self._is_run_bold(para.runs[0]):  # Updated check
                if current_action:
                    # Check if current action is spellcasting
                    if 'spellcasting' in current_action['name'].lower():
                        spellcasting = spellcasting_parser.parse_spellcasting_trait(f'{current_action['name']} {current_action['description']}')
                        if spellcasting:
                            self.current_creature['spellcasting'] = spellcasting
                    else:
                        actions.append(current_action)
                
                name, description = self._extract_name_from_bold_runs(para)
                
                # Build action dictionary
                current_action = {
                    "name": name,
                    "description": description,
                    "attack": None,
                    "hit": None,
                    "usage": None
                }
                
                # Parse attack if present
                attack_match = re.search(
                    r'(?:Melee or Ranged|(?:Melee|Ranged)) '
                    r'(?:Weapon|Spell) Attack:\s*([+-]\d+) to hit'
                    r'(?:, (?:reach|range) ((?:\d+/\d+|\d+) ft\.))?'
                    r'(?:or (?:reach|range) ((?:\d+/\d+|\d+) ft\.))?',
                    description
                )
                
                if attack_match:
                    weapon_or_spell = WeaponType.SPELL if 'Spell Attack' in description else WeaponType.WEAPON
                    
                    # Base attack info
                    attack_info = {
                        "weapon_type": weapon_or_spell.value,
                        "is_melee": 'melee' in description.lower(),
                        "is_ranged": 'range' in description.lower(),
                        "bonus": int(attack_match.group(1)),
                        "ability_used": None,
                        "magical_bonus": None,
                        "is_finesse": False,
                        "reach": None,
                        "range": None
                    }
                    
                    # Add reach/range based on attack types
                    if attack_info["is_melee"]:
                        attack_info["reach"] = attack_match.group(2)
                    if attack_info["is_ranged"]:
                        attack_info["range"] = attack_match.group(3) if attack_match.group(3) else attack_match.group(2)
                    
                    # Check for magical weapon bonus
                    magic_match = re.search(r'(?:with a )?([+-]\d+) magical', description.lower())
                    if magic_match:
                        attack_info["magical_bonus"] = int(magic_match.group(1))
                    
                    # Handle weapon-specific attributes
                    if weapon_or_spell == WeaponType.WEAPON:
                        # Check for finesse property
                        if 'finesse' in description.lower():
                            attack_info["is_finesse"] = True
                            attack_info["ability_used"] = 'dex'
                        else:
                            attack_info["ability_used"] = 'dex' if attack_info["is_ranged"] else 'str'
                    
                    current_action["attack"] = attack_info
                    
                    # Parse damage
                    damage_match = re.search(r'Hit:\s*\d+\s*\(([\dd+\s-]+)\)\s*([\w\s,]+)\s*damage', description)
                    if damage_match:
                        # Check for additional effects after damage
                        additional_match = re.search(r'damage(?:,|\.) (.+?)(?:$|\.(?:\s|$))', description)
                        current_action["hit"] = {
                            "damage": damage_match.group(1).strip(),
                            "damage_type": damage_match.group(2).strip(),
                            "additional_effects": additional_match.group(1).strip() if additional_match else None
                        }
            
            elif current_action:
                current_action["description"] += f"\n{self._normalize_text(para.text)}"
        
        # Add last action
        if current_action:
            # Check if current action is spellcasting
            if 'spellcasting' in current_action['name'].lower():
                spellcasting = spellcasting_parser.parse_spellcasting_trait(f'{current_action['name']} {current_action['description']}')
                if spellcasting:
                    self.current_creature['spellcasting'] = spellcasting
            else:
                actions.append(current_action)
        
        return actions

    def _process_legendary_actions(self, paragraphs: List[Paragraph]) -> None:
        """Process legendary actions section."""
        if not paragraphs:
            return
        
        # Extract slots per round from description
        slots_match = re.search(r"can take (\d+) legendary actions?", self._normalize_text(paragraphs[0].text))
        slots = int(slots_match.group(1)) if slots_match else 3  # Default to 3
        
        legendary_actions = {
            "slots_per_round": slots,
            "description": paragraphs[0].text,
            "actions": []
        }
        
        for para in paragraphs[1:]:  # Skip the first paragraph (description)
            if para.runs and self._is_run_bold(para.runs[0]):  # Updated check
                name, description = self._extract_name_from_bold_runs(para)
                
                # Parse cost if specified
                cost_match = re.search(r"\(costs (\d+) actions\)", name.lower())
                cost = int(cost_match.group(1)) if cost_match else 1
                name = re.sub(r"\(costs \d+ actions\)", "", name)
                
                # Add required usage field
                legendary_actions["actions"].append({
                    "name": name.strip(),
                    "description": description,
                    "cost": cost,
                    "usage": None  # Required field
                })
        
        self.current_creature["legendary_actions"] = legendary_actions

    def _process_lair_actions(self, paragraphs: List[Paragraph]) -> None:
        """Process lair actions section."""
        if not paragraphs:
            return
            
        lair_actions = {
            "description": self._normalize_text(paragraphs[0].text),
            "initiative_count": 20,
            "actions": []
        }
        
        # Try to find initiative count
        initiative_match = re.search(r"on initiative count (\d+)", self._normalize_text(paragraphs[0].text.lower()))
        if initiative_match:
            lair_actions["initiative_count"] = int(initiative_match.group(1))
        
        current_action = None
        for para in paragraphs[1:]:
            if para.runs and self._is_run_bold(para.runs[0]):  # Updated check
                if current_action:
                    lair_actions["actions"].append(current_action)
                
                name, description = self._extract_name_from_bold_runs(para)
                
                current_action = {
                    "name": name,
                    "description": description,
                    "usage": None  # Required field
                }
            elif current_action:
                current_action["description"] += f"\n{self._normalize_text(para.text)}"
        
        # Add last action
        if current_action:
            lair_actions["actions"].append(current_action)
        
        self.current_creature["lair_actions"] = lair_actions

    def _process_defenses(self, paragraphs: List[Paragraph]) -> None:
        """Process damage and condition immunities/resistances."""
        for para in paragraphs:
            text = self._normalize_text(para.text)
            
            if text.startswith("Damage Resistances"):
                resistances = text.replace("Damage Resistances", "").strip()
                self.current_creature["damage_resistances"] = [r.strip() for r in resistances.split(", ")]
            
            elif text.startswith("Damage Immunities"):
                immunities = text.replace("Damage Immunities", "").strip()
                self.current_creature["damage_immunities"] = [i.strip() for i in immunities.split(", ")]
            
            elif text.startswith("Condition Immunities"):
                conditions = text.replace("Condition Immunities", "").strip()
                self.current_creature["condition_immunities"] = [c.strip() for c in conditions.split(", ")]

    def _process_senses_and_languages(self, paragraphs: List[Paragraph]) -> None:
        """Process senses and languages sections."""
        for para in paragraphs:
            text = self._normalize_text(para.text)
            
            if text.startswith("Senses"):
                senses = {}
                sense_text = text.replace("Senses", "").strip()
                
                # Parse passive perception
                pp_match = re.search(r"passive Perception (\d+)", sense_text)
                if pp_match:
                    senses["passive_perception"] = int(pp_match.group(1))
                    sense_text = re.sub(r"passive Perception \d+", "", sense_text)
                
                # Parse other senses
                for sense in sense_text.split(","):
                    sense = sense.strip()
                    if sense:
                        distance_match = re.match(r"(\w+) (\d+) ft", sense)
                        if distance_match:
                            senses[distance_match.group(1).lower()] = int(distance_match.group(2))
                
                self.current_creature["senses"] = senses
            
            elif text.startswith("Languages"):
                languages = text.replace("Languages", "").strip()
                if languages:
                    self.current_creature["languages"]["spoken"] = [l.strip() for l in languages.split(",")]
                else:
                    self.current_creature["languages"]["spoken"] = ["—"]

    def _process_traits(self, paragraphs: List[Paragraph]) -> None:
        """Process traits section with spellcasting detection."""
        traits = []
        current_trait = None
        spellcasting_parser = SpellcastingParser()

        for para in paragraphs:
            if para.runs and self._is_run_bold(para.runs[0]):
                if current_trait:
                    # Check if current trait is spellcasting
                    if 'spellcasting' in current_trait['name'].lower():
                        spellcasting = spellcasting_parser.parse_spellcasting_trait(f'{current_trait['name']} {current_trait['description']}')
                        if spellcasting:
                            self.current_creature['spellcasting'] = spellcasting
                    else:
                        traits.append(current_trait)

                name, description = self._extract_name_from_bold_runs(para)
                current_trait = {
                    'name': name,
                    'description': description
                }
            elif current_trait:
                current_trait['description'] += f'\n{self._normalize_text(para.text)}'

        # Handle last trait
        if current_trait:
            if 'spellcasting' in current_trait['name'].lower():
                spellcasting = spellcasting_parser.parse_spellcasting_trait(f'{current_trait['name']} {current_trait['description']}')
                if spellcasting:
                    self.current_creature['spellcasting'] = spellcasting
            else:
                traits.append(current_trait)

        self.current_creature['traits'] = traits if traits else None

    def _process_regional_effects(self, paragraphs: List[Paragraph]) -> None:
        """Process regional effects section."""
        if not paragraphs:
            return
        
        description = self._normalize_text(paragraphs[0].text)
        effects = []
        
        current_effect = None
        for para in paragraphs[1:]:
            if para.runs and self._is_run_bold(para.runs[0]):
                if current_effect:
                    effects.append(current_effect)
                
                name, description = self._extract_name_from_bold_runs(para)
                
                current_effect = {
                    "name": name,
                    "description": description,
                    "mechanics": None
                }
            elif current_effect:
                current_effect["description"] += f"\n{self._normalize_text(para.text)}"
        
        if current_effect:
            effects.append(current_effect)
        
        # Set regional effects as a list of effects
        self.current_creature["regional_effects"] = effects
