import re

def create_sandbox():
    try:
        with open("variants_test.html", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("variants_test.html not found.")
        return

    # Extract the styles
    style_match = re.search(r'(<style>.*?</style>)', content, re.DOTALL)
    
    if not style_match:
        print("Could not find style block.")
        return
        
    style_content = style_match.group(1)
    
    # Save the styles to a separate CSS file (stripping the tags)
    raw_css = style_content.replace("<style>", "").replace("</style>", "")
    with open("gyml_sandbox.css", "w", encoding="utf-8") as f:
        f.write(raw_css.strip())
        
    # Extract just the <head> tags without the inline styles
    head_match = re.search(r'(<head>.*?)<style>', content, re.DOTALL)
    if head_match:
        head_tags = head_match.group(1)
    else:
        # Fallback if no head match
        head_tags = """<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GyML Slides Sandbox</title>
"""

    sandbox_html = f"""<!DOCTYPE html>
<html lang="en">
{head_tags.strip()}
    <link rel="stylesheet" href="gyml_sandbox.css">
</head>
<body>
    <div class="gyml-deck">
        <!-- 
          =============================================================
          SANDBOX SLIDE
          Replace the contents inside this section with your content blocks
          to test them with the actual viewport and styling.
          ============================================================= 
        -->
        <section data-image-layout="blank" data-density="balanced" style="--item-color: #6366f1;">
            
            <header class="header">
                <div class="topic-label">Testing Sandbox</div>
                <h1>Preview Content Blocks Here</h1>
            </header>
            
            <div class="body">
                
                <!-- =============== PASTE YOUR CONTENT BLOCK BELOW =============== -->
                
                <div style="padding: 2rem; border: 2px dashed #cbd5e1; border-radius: 12px; text-align: center; color: #64748b;">
                    <h2>Paste your block HTML here!</h2>
                    <p>It will render exactly as it does in the slide engine.</p>
                </div>
                
                <!-- =============== PASTE YOUR CONTENT BLOCK ABOVE =============== -->

            </div>
            
            <footer class="footer">
                <div class="footer-dots">
                    <span class="dot active"></span>
                </div>
            </footer>
            
        </section>
    </div>
    
    <!-- Scripts for animations/reveals -->
    <script>
        setTimeout(() => {{
            document.querySelectorAll('.anim-fade').forEach(el => el.classList.add('active'));
        }}, 500);
    </script>
</body>
</html>
"""

    with open("content_block_sandbox.html", "w", encoding="utf-8") as f:
        f.write(sandbox_html)
    
    print("Created content_block_sandbox.html and gyml_sandbox.css successfully!")

if __name__ == "__main__":
    create_sandbox()
