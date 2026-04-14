import re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\slides\gyml\validator.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add sequentialSteps and sequentialOutput to smart_layout variants if it's there
# Let's see what is currently in validator.py
print(repr(text))
