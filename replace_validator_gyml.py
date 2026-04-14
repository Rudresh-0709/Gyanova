import re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\slides\gyml\validator.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''            "processAccordion",
            "hubAndSpoke",
            "relationshipMap",
            "ribbonFold",
            "statsBadgeGrid",
            "diamondRibbon",
            "diamondGrid",
            "diamondHub",
            "featureShowcase",
            "cyclicBlock",
            "sequentialOutput",''',
'''            "processAccordion",
            "hubAndSpoke",
            "relationshipMap",
            "ribbonFold",
            "statsBadgeGrid",
            "diamondRibbon",
            "diamondGrid",
            "diamondHub",
            "featureShowcase",
            "cyclicBlock",
            "sequentialOutput",
            "sequentialSteps",'''
)

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\slides\gyml\validator.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

