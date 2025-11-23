import random

def solve_layout_for_slide(slide_json):
    """
    Input: One slide object from your JSON.
    Output: A configuration dict for Jinja2.
    """
    
    # 1. EXTRACT DATA
    # We assume you have a function that turns 'imagePrompt' into a URL
    # For now, we use a placeholder
    image_url = f"https://placehold.co/1920x1080?text={slide_json['title'].replace(' ', '+')}"
    
    main_block = slide_json['contentBlocks'][0] # The Timeline or Explanation
    narration_points = slide_json['points']
    
    # 2. DEFINE ARCHETYPES (The Menu of Layouts)
    # Weight: How likely this layout is to appear (Higher = More frequent)
    archetypes = [
        { 
            "id": "layout-classic-split", 
            "weight": 40,
            "compatible_blocks": ["timeline", "explanation", "steps"] 
        },
        { 
            "id": "layout-cinematic", 
            "weight": 30,
            "compatible_blocks": ["explanation", "statistics", "story"] 
            # Note: Timelines often look bad in Cinematic/Overlay mode because they need space
        },
        { 
            "id": "layout-magazine", 
            "weight": 20,
            "compatible_blocks": ["explanation", "steps", "timeline"] 
        },
        { 
            "id": "layout-bento", 
            "weight": 10,
            "compatible_blocks": ["statistics", "explanation"] 
        }
    ]
    
    # 3. FILTER: Which layouts work for THIS content?
    valid_layouts = []
    block_type = main_block['type'] # e.g., "timeline"
    
    for arch in archetypes:
        # Rule 1: Is the block type allowed?
        if block_type not in arch['compatible_blocks']:
            continue
            
        # Rule 2: If "Cinematic", we can't have too much text in points
        if arch['id'] == 'layout-cinematic' and len(narration_points) > 3:
            continue
            
        valid_layouts.append(arch)
    
    # Fallback if filters remove everything
    if not valid_layouts:
        selected_id = "layout-classic-split"
    else:
        # Weighted Random Selection
        selected = random.choices(
            valid_layouts, 
            weights=[x['weight'] for x in valid_layouts], 
            k=1
        )[0]
        selected_id = selected['id']

    # 4. PREPARE CONTEXT FOR JINJA
    return {
        "layout_class": selected_id,
        "title": slide_json['title'],
        "image_url": image_url,
        
        # Pass the Raw Block Data so Jinja can handle specific logic
        "block_data": main_block, 
        "block_type": block_type,
        
        "narration_points": narration_points
    }