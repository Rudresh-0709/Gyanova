import random

class LayoutSolver:
    def solve(self, slide_data):
        """
        Input: Raw JSON from AI
        Output: A 'Layout Context' telling the HTML which CSS classes to use.
        """
        
        # 1. Layout Archetypes (Corresponding to static/css/layouts.css)
        archetypes = [
            "layout-classic-split",   # Image Left, Content Right
            "layout-magazine",        # Image Center, Text wrap
            "layout-bento-grid"       # Boxy grid like Apple slides
        ]
        
        # 2. Constraints Logic (The "Smart" part)
        # Example: Don't use Cinematic if there is no image
        if not slide_data.get('image_url'):
            archetypes.remove("layout-cinematic")

        # 3. Random Selection
        selected_layout = random.choice(archetypes)
        
        # 4. Content Splitting (For placing text in different grid slots)
        # e.g., Split 4 narration points into 2 Main + 2 Footer
        points = slide_data.get('narration_points', [])
        split_index = len(points) // 2
        
        return {
            "layout_class": selected_layout,
            "image_url": slide_data.get('image_url'),
            "slots": {
                "main_content": points[:split_index],
                "footer_content": points[split_index:],
                "block_data": slide_data.get('content_block')
            }
        }