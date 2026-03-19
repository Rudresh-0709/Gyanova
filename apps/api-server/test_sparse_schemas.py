#!/usr/bin/env python3
"""
Test script to verify sparse template schemas are correctly defined.
"""

from app.services.node.narration_techniques import get_sparse_template_schema, is_sparse_template_schema

# Test all 4 sparse templates
templates = ['Title card', 'Image and text', 'Text and image', 'Formula block']
print('Testing Sparse Template Schemas:')
print('=' * 60)

all_passed = True
for template in templates:
    is_sparse = is_sparse_template_schema(template)
    schema = get_sparse_template_schema(template)
    print(f'\nTemplate: {template}')
    print(f'  Is Sparse: {is_sparse}')
    if schema:
        print(f'  Required: {schema.get("required_blocks", [])}')
        print(f'  Forbidden: {schema.get("forbidden_blocks", [])}')
        print(f'  Max Blocks: {schema.get("max_blocks", 0)}')
        print(f'  ✓ PASSED')
    else:
        print('  Schema: NOT FOUND')
        print(f'  ✗ FAILED')
        all_passed = False

print('\n' + '=' * 60)
if all_passed:
    print('✓ All sparse template schemas loaded successfully!')
else:
    print('✗ Some schemas are missing!')
