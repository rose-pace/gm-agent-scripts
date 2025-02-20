# D&D 5e Stat Block Conversion Tool

A Python tool for converting D&D 5e monster stat blocks from DOCX documents into structured YAML format, with validation and formatting preservation.

## Features

- Converts DOCX stat blocks to YAML format
- Maintains game mechanical accuracy through validation
- Preserves formatting and structure
- Handles all standard stat block features:
  - Core stats (AC, HP, Speed, etc.)
  - Ability scores and modifiers
  - Skills and saving throws
  - Actions and attacks
  - Special abilities
  - Legendary actions
  - Lair actions
  - Regional effects

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gm-agent-scripts.git
cd gm-agent-scripts
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:

```python
from docx_statblock_converter import DocxStatBlockConverter

# Initialize converter
converter = DocxStatBlockConverter(
    validation_rules_path='statblock-validation.yaml',
    collection='core_monsters',
    tags=['official', 'basic_rules']
)

# Convert DOCX to YAML
creature_data = converter.convert_docx_to_schema('monster.docx')

# Generate report and save YAML
converter.output_conversion_report('monster.yaml')
```

## File Structure

- `docx_statblock_converter.py` - Main converter class
- `statblock_validator.py` - Pydantic validation models
- `statblock-schema.yaml` - YAML schema definition
- `statblock-validation.yaml` - Validation rules

## Schema Validation

The tool validates against a predefined schema to ensure:
- Required fields are present
- Data types are correct
- Game mechanical constraints are met
- Relationships between fields are valid

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Recognition

This tool is designed for use with Dungeons & Dragons 5th Edition. D&D and all official materials are property of Wizards of the Coast LLC.
