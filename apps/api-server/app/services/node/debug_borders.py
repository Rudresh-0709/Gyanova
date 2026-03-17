
import os

path = r"d:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\test_preview_variants\ultra_dense_test.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

debug_css = """
    * { outline: 1px solid rgba(255,0,0,0.2) !important; }
    .body { border: 5px solid red !important; min-height: 100px !important; }
    .cyclic-container { border: 5px solid blue !important; display: block !important; opacity: 1 !important; visibility: visible !important; }
    .fs-radial-container { border: 5px solid green !important; display: block !important; opacity: 1 !important; visibility: visible !important; }
    .slide-section { overflow: visible !important; height: auto !important; }
"""

new_content = content.replace("</style>", debug_css + "\n</style>")

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Debug borders injected.")
