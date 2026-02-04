import os

css_path = "services/node/slides/gyml/styles/gyml_theme.css"

# define new styles
new_css = """/*
 * GyML Theme - Structural Ornaments & Affordances
 */

:root {
    /* Semantic Colors */
    --accent-primary: #5AB2BA; /* Gamma Teal */
    --accent-secondary: #0F172A;
    --border-subtle: rgba(0, 0, 0, 0.08);
    --border-strong: rgba(0, 0, 0, 0.15);
    
    /* Rhythm */
    --space-xs: 0.5rem;
    --space-sm: 1rem;
    --space-md: 2rem;
    --space-lg: 3.5rem;
}

/* 1. SECTION SEPARATORS */
.block-separator {
    height: 1px;
    background: var(--border-subtle);
    margin: var(--space-md) 0;
    width: 100%;
}

/* 2. CARD AFFORDANCES */
.card {
    position: relative;
    background: #ffffff;
    border: 1px solid var(--border-strong);
    border-radius: 6px;
    padding: var(--space-md) var(--space-sm) var(--space-sm) var(--space-sm); /* Top heavy padding */
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    overflow: hidden;
}

/* Top Accent Line */
.card::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--accent-primary);
    opacity: 0.8;
}

/* Inner Divider (Subtle) */
.card-content {
    border-top: 1px solid var(--border-subtle); /* Separating Icon/Number from content */
    padding-top: var(--space-sm);
    margin-top: var(--space-sm);
}
.card-number + .card-content, 
.card-icon + .card-content {
    border-top: none; /* Only if no header element? simpler: just use spacing */
    border-top: 1px solid transparent; 
}

/* 3. TIMELINE GRAMMAR */
/* Vertical Rail */
.smart-layout[data-variant="timeline"] {
    position: relative;
    padding-left: 3rem; /* Space for rail */
}

/* The Rail */
.smart-layout[data-variant="timeline"]::before {
    content: '';
    position: absolute;
    left: 1rem;
    top: 0.5rem;
    bottom: 0.5rem;
    width: 2px;
    background: var(--border-strong); /* Visible rail */
    z-index: 0;
}

/* The Nodes */
.smart-layout[data-variant="timeline"] .card::before {
    content: '';
    position: absolute;
    left: -2.35rem; /* center on rail (1rem) relative to card padding */
    top: 2rem; /* Align with title */
    width: 12px;
    height: 12px;
    background: #fff;
    border: 2px solid var(--accent-primary);
    border-radius: 50%;
    z-index: 1;
    box-shadow: 0 0 0 4px #f8f7f4; /* inner breathing room from rail */
}

/* 4. VISUAL RHYTHM (Margins) */

/* Title is Loud */
h1 {
    margin-bottom: var(--space-md); 
}

/* Primary Block is Loud */
.columns, .smart-layout {
    margin-bottom: var(--space-md);
}

/* Supporting Blocks are Quiet */
p {
    margin-bottom: var(--space-sm);
}

/* Card Titles are Medium */
.card-title {
    margin-bottom: var(--space-xs);
    font-weight: 700;
}

/* 5. CODE BLOCK ROLE */
.code-block[data-role="primary"] {
    border: 1px solid var(--border-strong);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.code-block[data-role="example"] {
    font-size: 0.85em;
    background: #f8f9fa;
    border-left: 3px solid var(--accent-primary);
}

"""

with open(css_path, "w", encoding="utf-8") as f:
    f.write(new_css)

print("Updated gyml_theme.css with visual ornaments.")
