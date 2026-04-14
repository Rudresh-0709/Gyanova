import re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\v2\gyml_generator_v2.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '''  PROCESS STEPS: processSteps, processArrow, processAccordion''',
    '''  PROCESS STEPS: processSteps, processArrow, processAccordion, sequentialSteps, sequentialOutput'''
)

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\v2\gyml_generator_v2.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

