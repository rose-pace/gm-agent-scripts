from typing import Dict, List, Optional, Union
import re
import yaml
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Document processing
from docx import Document  # python-docx for reading .docx files
from docx.text.paragraph import Paragraph
from docx.text.run import Run

# Data validation and processing
from pydantic import BaseModel, Field, validator  # For data validation
import pandas as pd  # For data manipulation if needed
from rich import print  # For better console output
from rich.console import Console
from rich.table import Table

from statblock_validator import StatBlockValidator
from docx_statblock_converter import DocxStatBlockConverter

# Usage example:
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert D&D stat blocks from DOCX to YAML schema')
    parser.add_argument('input', help='Input DOCX file')
    parser.add_argument('output', help='Output YAML file')
    parser.add_argument('-c', '--collection', dest='collection', help='Collection name for the stat blocks', default='monsters')
    parser.add_argument('-t', '--tags', dest='tags', help='Tags for the stat blocks', nargs='*', default=[])
    parser.add_argument('--report', help='Generate detailed conversion report', action='store_true')
    
    args = parser.parse_args()
    print(f"Converting {args.input} to {args.output} using rules from {args.rules}")
    
    # Initialize converter
    converter = DocxStatBlockConverter(args.collection, args.tags)
    
    try:
        # Convert document
        converted_data = converter.convert_docx_to_schema(args.input)
        
        # Save output
        if args.report:
            converter.output_conversion_report()

        with open(args.output, 'w') as f:
            yaml.dump(converted_data, f, sort_keys=False, allow_unicode=True)
                
        print(f"Successfully converted {args.input} to {args.output}")
        
    except Exception as e:
        import traceback
        print("[red]Error during conversion:[/red]")
        print(f"{str(e)}")
        print("\n[yellow]Stack trace:[/yellow]")
        traceback.print_exc()
