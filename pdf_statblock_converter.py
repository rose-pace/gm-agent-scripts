#!/usr/bin/env python3
"""
PDF Monster Stat Block Converter for D&D 5e 2024 Rules
Extracts monster stat blocks from PDFs and converts them to YAML format that matches the schema.
"""

import os
import re
import yaml
import argparse
import datetime
from pypdf import PdfReader
import pymupdf

# Import all parsers
from parsers.core_stats_parser import CoreStatsParser
from parsers.abilities_parser import AbilitiesParser
from parsers.actions_parser import ActionsParser
from parsers.spellcasting_parser import SpellcastingParser
from parsers.damage_type_parser import DamageTypeParser
from parsers.usage_parser import UsageParser

class StatBlockExtractor:
    def __init__(self, debug=False):
        self.debug = debug

    def normalize_statblock_text(self, text):
        """Clean up common spacing and formatting issues in extracted stat blocks."""
        # Fix ability score labels
        text = re.sub(r'S</b><b>tr', 'STR', text)
        text = re.sub(r'D</b><b>ex', 'DEX', text)
        text = re.sub(r'C</b><b>on', 'CON', text)
        text = re.sub(r'I</b><b>nt', 'INT', text)
        text = re.sub(r'W</b><b>is', 'WIS', text)
        text = re.sub(r'C</b><b>ha', 'CHA', text)
        
        # Normalize multiple spaces
        text = re.sub(r'[^\S\r\n]+', ' ', text)
        
        return text
        
    def extract_text_from_pdf(self, pdf_path, start_page=None, end_page=None):
        """Extract text from PDF file."""
        reader = PdfReader(pdf_path)
        
        # If no page range is specified, process all pages
        if start_page is None:
            start_page = 0
        if end_page is None:
            end_page = len(reader.pages)
        
        # Ensure page numbers are within valid range
        start_page = max(0, min(start_page, len(reader.pages) - 1))
        end_page = max(start_page + 1, min(end_page, len(reader.pages)))

        doc = pymupdf.open(pdf_path)
        
        full_text = "<statblock>\n"
        for page_num in range(start_page, end_page):
            page = doc[page_num]
            blocks = page.get_textpage().extractDICT()['blocks']

            for block in blocks:
                if block['type'] == 0:  # Text block
                    for line in block['lines']:
                        for span in line['spans']:
                            text = span['text'].strip()
                            if 'player\'s handbook' in text.lower():
                                # skip this line
                                continue
                            if span['flags'] & pymupdf.TEXT_FONT_BOLD:
                                full_text += f'<b>{text}</b>'
                            else:
                                full_text += text

                            if 'monster manual 2024' in text.lower():
                                # end of stat block, add extra newline
                                full_text += '\n</statblock>\n\n<statblock>'
                                break

                            
                        # Add a newline after each line
                        full_text += '\n'

        # fix formatting issues
        full_text = self.normalize_statblock_text(full_text)
                        
        # remove last opening tag
        if full_text.endswith('<statblock>\n'):
            full_text = full_text.strip()[:-len('<statblock>\n')] 

        return full_text
    
    def find_stat_blocks(self, text):
        """Identify monster stat blocks in the text using <statblock> tags."""
        monster_blocks = []
        
        # Find all content between <statblock> and </statblock> tags
        pattern = r'<statblock>\s*(.*?)\s*</statblock>'
        statblock_matches = re.findall(pattern, text, re.DOTALL)
        
        for block_text in statblock_matches:
            # Extract monster name from the first line
            lines = block_text.strip().split('\n')
            if not lines:
                continue
                
            monster_name = lines[0].strip()
            
            if self.debug:
                print(f"Found monster: {monster_name}")
                
            monster_blocks.append((monster_name, block_text.strip()))
        
        return monster_blocks

    def parse_monster_stat_block(self, name, block_text):
        """Parse a 2024 format monster stat block into structured data based on the schema."""
        # Initialize monster data with required schema fields
        monster_data = {
            'metadata': {
                'name': name,
                'version': '1.0',
                'date_created': datetime.datetime.now().strftime('%Y-%m-%d'),
                'last_modified': datetime.datetime.now().strftime('%Y-%m-%d'),
                'source': 'Monster Manual 2024',
            },
            'creature_info': {},
            'core_stats': {},
            'abilities': {},
            'proficiencies': {
                'saving_throws': [],
                'skills': [],
            },
            'defenses': {},
            'senses': {},
            'languages': {},
        }

        # split the block text into lines for easier processing
        lines = block_text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]  # Remove empty lines
        # First line is the name which we already have so skip it
        lines = lines[1:]
        
        # Extract size, type, and alignment
        line = lines.pop(0)  # First line after name
        parsed = CoreStatsParser.parse_subheader(line)
        if parsed:
            monster_data['creature_info'].update(parsed)
        
        # Extract AC
        line = lines.pop(0)  # next line
        ac_match = re.search(r'<b>AC</b>(\d+)', line)
        if ac_match:
            monster_data['core_stats']['armor_class'] = {
                'value': int(ac_match.group(1)),
                'type': None  # Not specified in the stat block
            }
        
        # Extract HP
        line = lines.pop(0)  # next line
        hp_match = re.search(r'<b>HP</b>(\d+)\s+\((.*?)\)', line)
        if hp_match:
            monster_data['core_stats']['hit_points'] = {
                'average': int(hp_match.group(1)),
                'roll': hp_match.group(2)
            }

        # Extract speed
        line = lines.pop(0)  # next line
        if not lines[0].startswith('<b>Initiative</b>'):
            line += ' ' + lines.pop(0)  # next line if not initiative
        line = line.replace('<b>Speed</b>', '').strip()
        speeds = CoreStatsParser.parse_speed(line)
        if speeds:
            monster_data['core_stats']['speed'] = speeds
        
        # Extract Initiative       
        line = lines.pop(0)  # next line
        if not lines[0].startswith('MOD'):
            line += ' ' + lines.pop(0)
        initiative_match = re.search(r'<b>Initiative</b>\s+([+-]\d+)\s+\((\d+)\)', line)
        if initiative_match:
            monster_data['initiative'] = {
                'modifier': initiative_match.group(1),
                'score': int(initiative_match.group(2))
            }
        
        # skip next 3 lines as they do not include relevant information
        lines = lines[3:]
        # Extract ability scores and modifiers
        abilities_found = 0
                
        abilities = {}
        saving_throws = []
        ability_names = {
            'STR': 'strength',
            'DEX': 'dexterity',
            'CON': 'constitution',
            'INT': 'intelligence',
            'WIS': 'wisdom',
            'CHA': 'charisma',
        }
        # parse abilities: 'score', 'modifier', 'save'
        current_key = None
        current_part = 'score'

        while abilities_found < 6:
            line = lines.pop(0)
            if line.startswith('<b>'):
                # new ability
                current_key = line[3:6].upper()
                abilities[ability_names[current_key]] = {}
                line = line[10:]  # remove <b> and ability name
                
            # split by whitespace
            parts = line.split()
            for part in parts:
                if current_part == 'score':
                    abilities[ability_names[current_key]] = {
                        'score': int(part),
                        'modifier': 0
                    }
                    current_part = 'modifier'
                elif current_part == 'modifier':
                    abilities[ability_names[current_key]]['modifier'] = int(part)
                    current_part = 'save'
                elif current_part == 'save':
                    saving_throws.append({
                        'ability': ability_names[current_key],
                        'modifier': int(part)
                    })
                    current_part = 'score'
                    current_key = None

                    abilities_found += 1
        
        monster_data['abilities'].update(abilities)
        monster_data['proficiencies']['saving_throws'] = saving_throws

        bold_pattern = re.compile(r'<b>(.*?)</b>')

        line = lines.pop(0)  # next line
        while line.strip() != 'Traits':
            if line.startswith('<b>'):
                if current_part:
                    monster_data = self._extract_skills_to_cr(current_part, current_key, monster_data)
                current_key = bold_pattern.search(line).group(1).lower()
                current_part = line[line.find('</b>') + 4:].strip()
            else:
                current_part += ' ' + line.strip()

            line = lines.pop(0)  # next line

        if current_part:
            monster_data = self._extract_skills_to_cr(current_part, current_key, monster_data)

        # Split up remainder into sections
        section_names = ['Actions', 'Reactions', 'Traits', 'Legendary Actions']
        sections = {
            'Traits': {},
        }
        current_section = 'Traits'
        current_feature = None
        for line in lines:
            if line.strip() in section_names:
                current_section = line.strip()
                sections[current_section] = {}
            elif line.strip().startswith('Monster Manual'):
                break
            elif line.strip().startswith('<b>'):
                # This is a new feature of this section
                current_feature = bold_pattern.search(line).group(1).lower()
                text = line[line.find('</b>') + 4:].strip()
                if text:
                    text += ' '
                sections[current_section][current_feature] = text
            else:
                sections[current_section][current_feature] += line.strip() + ' '
        
        # Extract traits
        if sections.get('Traits'):
            monster_data['traits'] = {}
            traits = sections['Traits']
            # First trait is the proficiency bonus
            proficiency_bonus = traits.get('proficiency bonus')
            if proficiency_bonus:
                monster_data['proficiencies']['bonus'] = int(proficiency_bonus.strip())
                del traits['proficiency bonus']

            # Remove treasure trait if present
            if traits.get('treasure'):
                del traits['treasure']

            # loop through traits and add to monster_data
            for trait_name, trait_desc in traits.items():
                # Check for usage in trait name
                if '(' in trait_name:
                    usage = UsageParser.parse_usage(trait_name)
                    trait_name = trait_name.split('(')[0].strip()
                    monster_data['traits'][trait_name] = {
                        'description': trait_desc.strip(),
                        'usage': usage
                    }
                else:
                    monster_data['traits'][trait_name] = {
                        'description': trait_desc.strip()
                    }

        # Extract actions
        monster_data['actions'] = {}
        if sections.get('Actions'):
            actions = sections['Actions']
            # spell casting is now in actions section
            if actions.get('spellcasting'):
                spellcasting = actions['spellcasting']
                del actions['spellcasting']
                # find first colon and add newline after it
                colon_index = spellcasting.find(':')
                if colon_index != -1:
                    spellcasting = spellcasting[:colon_index + 1] + '\n' + spellcasting[colon_index + 1:]
                spell_usage = ['at will', '1/day', '2/day', '3/day']
                # create newline before each usage
                for usage in spell_usage:
                    spellcasting = spellcasting.replace(usage, '\n' + usage)
                # prepend innate spellcasting to the spellcasting text to force innate logic
                spellcasting = 'Innate Spellcasting: ' + spellcasting
                # parse spellcasting
                monster_data['spellcasting'] = SpellcastingParser().parse_spellcasting_trait(spellcasting, monster_data['abilities'], monster_data['proficiencies']['bonus'])

            # loop through actions and add to monster_data
            standard_actions = []
            bonus_actions = []
            for action_name, action_desc in actions.items():
                action = {}
                is_bonus_action = False
                # Check for usage in action name
                if '(bonus action)' in action_name:
                    is_bonus_action = True
                    action_name = action_name.replace('(bonus action)', '').strip()
                    action = {
                        'name': action_name,
                        'description': action_desc.strip(),
                    }
                elif '(' in action_name:
                    action_name = action_name.split('(')[0].strip()
                    action = {
                        'name': action_name,
                        'description': action_desc.strip(),
                    }
                    usage = UsageParser.parse_usage(action_name)
                    if usage:
                        action['usage'] = usage
                else:
                    action = {
                        'name': action_name,
                        'description': action_desc.strip()
                    }
                attack = ActionsParser.parse_attack(action_desc)
                if attack:
                    action['attack'] = attack
                    action['hit'] = ActionsParser.parse_damage(action_desc)
                
                if is_bonus_action:
                    bonus_actions.append(action)
                else:
                    standard_actions.append(action)
            # set standard actions
            if standard_actions:
                monster_data['actions']['standard'] = standard_actions
            if bonus_actions:
                monster_data['actions']['bonus_actions'] = bonus_actions

        # Extract reactions
        if sections.get('Reactions'):
            actions = sections['Reactions']
            # loop through reactions and add to monster_data
            reactions = []
            for action_name, action_desc in actions.items():
                action = {}
                # Check for usage in action name
                if '(' in action_name:
                    action_name = action_name.split('(')[0].strip()
                    action = {
                        'name': action_name,
                        'description': action_desc.strip(),
                    }
                    usage = UsageParser.parse_usage(action_name)
                    if usage:
                        action['usage'] = usage
                else:
                    action = {
                        'name': action_name,
                        'description': action_desc.strip()
                    }
                attack = ActionsParser.parse_attack(action_desc)
                if attack:
                    action['attack'] = attack
                    action['hit'] = ActionsParser.parse_damage(action_desc)

                reactions.append(action)
            # set reactions
            monster_data['actions']['reactions'] = reactions
        
        # Extract legendary actions
        if sections.get('Legendary Actions'):
            actions = sections['Legendary Actions']
            # first is legendary action description
            key = next(k for k in actions.keys() if k.startswith('legendary action'))
            legendary_actions_desc = actions[key]
            monster_data['legendary_actions'] = {
                'slots_per_round': 3,
                'description': legendary_actions_desc.strip(),
            }
            del actions[key]
                
            # loop through each action
            legendary_actions = []
            for action_name, action_desc in actions.items():
                legendary_actions.append({
                    'name': action_name,
                    'description': action_desc.strip(),
                    'cost': 1,
                })
            # set legendary actions
            monster_data['legendary_actions']['actions'] = legendary_actions
        
        # Extract source information
        source_match = re.search(r'Monster Manual 2024 p\.\s+(\d+)', block_text)
        if source_match:
            monster_data['metadata']['source'] = 'Monster Manual 2024'
            monster_data['metadata']['page'] = int(source_match.group(1))
        
        # Add generic tags and collection
        monster_data['metadata']['collection'] = 'monsters'
        monster_data['metadata']['tags'] = [
            monster_data['creature_info']['type'],
            monster_data['creature_info']['size'].lower(),
            'official',
            '5e',
            '2024',
        ]
        
        return monster_data
    
    def _extract_skills_to_cr(self, text, key, monster_data):
        if key == 'skills':
            monster_data['proficiencies']['skills'] = AbilitiesParser.parse_skills(text)
        if key == 'passive perception':
            monster_data['senses']['passive_perception'] = int(text.strip())
        if key == 'immunities':
            monster_data['defenses']['damage_immunities'] = DamageTypeParser.parse_damage_types(text.strip())
        if key == 'condition immunities':
            monster_data['defenses']['condition_immunities'] = [c.strip() for c in text.split(", ")]
        if key == 'senses':
            monster_data['senses'].update(CoreStatsParser.parse_senses(text.strip()))
        if key == 'languages':
            monster_data['languages'] = CoreStatsParser.parse_languages(text.strip())
        if key == 'cr':
            monster_data['creature_info']['cr'] = CoreStatsParser.parse_challenge_rating(f'Challenge {text.strip()}')

        return monster_data
    
    def _parse_ability_entries(self, section_text):
        """Parse ability entries (traits, actions, reactions, legendary actions)."""
        entries = []
        
        # Remove section headers and trailing content
        clean_text = re.sub(r'^(?:Actions|Reactions|Traits|Legendary Actions).*?\n', '', section_text, flags=re.MULTILINE)
        
        # Split by ability entries (each starts with a capitalized name)
        entry_pattern = r'([A-Z][A-Za-z\s]+(?:\([^)]*\))?)\s+(.*?)(?=\n[A-Z][A-Za-z\s]+(?:\([^)]*\))?\s+|\Z)'
        
        for match in re.finditer(entry_pattern, clean_text, re.DOTALL):
            name = match.group(1).strip()
            description = match.group(2).strip()
            
            # Skip if this is just a section header
            if name in ['Actions', 'Reactions', 'Traits', 'Legendary Actions']:
                continue
            
            # Parse attack information if present
            attack_info = self._parse_attack_info(description)
            
            entry = {
                'name': name,
                'description': description
            }
            
            # Add attack info if found
            if attack_info:
                entry.update(attack_info)
            
            # Check for usage limitations
            usage_info = self._parse_usage_info(name, description)
            if usage_info:
                entry['usage'] = usage_info
            
            entries.append(entry)
        
        return entries
    
    def _parse_attack_info(self, description):
        """Extract attack information from ability description."""
        attack_info = {}
        
        # Check if this is an attack action
        melee_match = re.search(r'Melee(?:\s+or\s+Ranged)?\s+Attack\s+Roll:\s+([+-]\d+)', description)
        ranged_match = re.search(r'Ranged(?:\s+or\s+Melee)?\s+Attack\s+Roll:\s+([+-]\d+)', description)
        
        if melee_match or ranged_match:
            attack_info['attack'] = {}
            
            # Determine attack type (melee, ranged, or both)
            attack_info['attack']['is_melee'] = bool(melee_match)
            attack_info['attack']['is_ranged'] = bool(ranged_match)
            
            # Get attack bonus
            if melee_match:
                attack_info['attack']['bonus'] = int(melee_match.group(1))
            elif ranged_match:
                attack_info['attack']['bonus'] = int(ranged_match.group(1))
            
            # Determine weapon type (spell or weapon)
            if 'spell' in description.lower():
                attack_info['attack']['weapon_type'] = 'spell'
            else:
                attack_info['attack']['weapon_type'] = 'weapon'
            
            # Extract reach or range
            reach_match = re.search(r'reach\s+(\d+)\s+ft', description, re.IGNORECASE)
            if reach_match and attack_info['attack']['is_melee']:
                attack_info['attack']['reach'] = f"{reach_match.group(1)} ft."
            
            range_match = re.search(r'range\s+(\d+(?:/\d+)?)\s+ft', description, re.IGNORECASE)
            if range_match and attack_info['attack']['is_ranged']:
                attack_info['attack']['range'] = f"{range_match.group(1)} ft."
            
            # Extract damage information
            hit_match = re.search(r'Hit:\s+(.*?)(?=\.|$)', description)
            if hit_match:
                hit_text = hit_match.group(1)
                
                # Extract damage dice
                damage_match = re.search(r'(\d+(?:d\d+)?(?:\s*[+-]\s*\d+)?)\s+([\w\s]+?)\s+damage', hit_text)
                if damage_match:
                    if 'hit' not in attack_info:
                        attack_info['hit'] = {}
                    
                    attack_info['hit']['damage'] = damage_match.group(1)
                    attack_info['hit']['damage_type'] = damage_match.group(2).strip()
                    
                    # Check for additional effects
                    effects_match = re.search(r'damage(?:\.|,\s+and\s+)(.*)', hit_text)
                    if effects_match:
                        attack_info['hit']['additional_effects'] = effects_match.group(1).strip()
        
        return attack_info
    
    def _parse_usage_info(self, name, description):
        """Extract usage limitations from ability name and description."""
        usage_info = {}
        
        # Check for recharge abilities
        recharge_match = re.search(r'\(Recharge\s+(\d+)(?:-(\d+))?\)', name)
        if recharge_match:
            usage_info['type'] = 'recharge'
            
            # Single number or range
            if recharge_match.group(2):  # Range like 5-6
                usage_info['range'] = [int(recharge_match.group(1)), int(recharge_match.group(2))]
            else:  # Single value like "Recharge 6"
                usage_info['value'] = int(recharge_match.group(1))
                
            return usage_info
        
        # Check for per-day abilities
        per_day_match = re.search(r'\((\d+)/Day\)', name)
        if per_day_match:
            usage_info['type'] = 'per_day'
            usage_info['times'] = int(per_day_match.group(1))
            return usage_info
        
        # Check description for usage limits
        if re.search(r'(\d+)/day', description, re.IGNORECASE):
            day_match = re.search(r'(\d+)/day', description, re.IGNORECASE)
            usage_info['type'] = 'per_day'
            usage_info['times'] = int(day_match.group(1))
            return usage_info
        
        # Check for short/long rest limitations
        if re.search(r'short rest', description, re.IGNORECASE) and re.search(r'(\d+)(?:\s+time|\s+use)', description, re.IGNORECASE):
            times_match = re.search(r'(\d+)(?:\s+time|\s+use)', description, re.IGNORECASE)
            usage_info['type'] = 'per_short_rest'
            usage_info['times'] = int(times_match.group(1))
            return usage_info
        
        if re.search(r'long rest', description, re.IGNORECASE) and re.search(r'(\d+)(?:\s+time|\s+use)', description, re.IGNORECASE):
            times_match = re.search(r'(\d+)(?:\s+time|\s+use)', description, re.IGNORECASE)
            usage_info['type'] = 'per_long_rest'
            usage_info['times'] = int(times_match.group(1))
            return usage_info
        
        return None
    
    def extract_save_yaml(self, monster_data, output_dir):
        """Save monster data as a YAML file matching the schema."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a filename from the monster name
        filename = monster_data['metadata']['name'].lower().replace(' ', '_') + '.yaml'
        file_path = os.path.join(output_dir, filename)
        
        # Custom YAML dump to properly handle certain data types
        class NoAliasDumper(yaml.SafeDumper):
            def ignore_aliases(self, data):
                return True
        
        # Ensure proper format for fraction challenge ratings
        if 'cr' in monster_data['creature_info'] and '/' in str(monster_data['creature_info']['cr']['rating']):
            monster_data['creature_info']['cr']['rating'] = str(monster_data['creature_info']['cr']['rating'])
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(monster_data, f, Dumper=NoAliasDumper, sort_keys=False, default_flow_style=False)
        
        return file_path

def main():
    """Main function to process PDF and extract stat blocks."""
    parser = argparse.ArgumentParser(description='Convert D&D 5e monster stat blocks from PDF to YAML.')
    parser.add_argument('pdf_path', help='Path to the PDF file.')
    parser.add_argument('--output', '-o', default='monsters_yaml', help='Output directory for YAML files.')
    parser.add_argument('--start-page', type=int, help='Start page number (0-indexed).')
    parser.add_argument('--end-page', type=int, help='End page number (0-indexed).')
    parser.add_argument('--debug', action='store_true', help='Print debug information.')
    parser.add_argument('--single-monster', help='Extract only this monster name (case sensitive).')
    
    args = parser.parse_args()
    
    extractor = StatBlockExtractor(debug=args.debug)
    
    # Extract text from PDF
    if args.debug:
        print(f"Reading PDF file: {args.pdf_path}")
    
    pdf_text = extractor.extract_text_from_pdf(args.pdf_path, args.start_page, args.end_page)

    os.makedirs('debug', exist_ok=True)
    
    if args.debug:
        debug_file = os.path.join('debug', 'pdf_extract_debug.txt')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(pdf_text)
        print(f"Saved raw PDF text to {debug_file}")

    # Find and parse stat blocks
    monster_blocks = extractor.find_stat_blocks(pdf_text)
    
    if not monster_blocks:
        print("No monster stat blocks found.")
        return
    
    print(f"Found {len(monster_blocks)} monster stat blocks.")
    
    if args.single_monster:
        monster_blocks = [(name, text) for name, text in monster_blocks if name == args.single_monster]
        if not monster_blocks:
            print(f"Monster '{args.single_monster}' not found.")
            return
    
    # Process each monster block
    for monster_name, block_text in monster_blocks:
        print(f"Processing: {monster_name}")
        
        if args.debug:
            debug_file = os.path.join('debug', f"{monster_name.lower().replace(' ', '_')}_debug.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(block_text)
            print(f"Saved monster block text to {debug_file}")
        
        monster_data = extractor.parse_monster_stat_block(monster_name, block_text)
        file_path = extractor.extract_save_yaml(monster_data, args.output)
        print(f"Saved to: {file_path}")
    
    print(f"Processed {len(monster_blocks)} monsters.")

if __name__ == "__main__":
    main()