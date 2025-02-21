# Project: D&D 5e Stat Block Conversion Tool

## Purpose:
- Convert D&D 5e stat blocks from DOCX format to structured YAML
- Maintain game mechanical accuracy and validation
- Support standard stat block features and special abilities
- Handle formatting and structure variations in source documents

## Coding Guidelines
- Always check any edits against the schema in statblock-schema.yaml and validation in statblock-validation.yaml
- Prefer single quotes for strings
- Add concise and descriptive comments to clarify logic
- Use pydantic for all validation
- Prefer string comparisons in lowercase if case is not needed

## Files to reference:
1. statblock-schema.yaml
2. statblock-validation.yaml