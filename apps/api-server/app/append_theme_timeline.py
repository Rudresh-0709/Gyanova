import os

css_path = "services/node/slides/gyml/styles/gyml_theme.css"

alternating_css = """
/* ================================================
   TIMELINE ALTERNATING (Zig-Zag)
   ================================================ */

.smart-layout[data-variant="timelineAlternating"] {
    display: grid;
    grid-template-columns: 1fr 2rem 1fr; /* Left | Rail | Right */
    gap: 0;
    position: relative;
    padding-left: 0; /* Override default timeline padding */
}

/* The Central Rail */
.smart-layout[data-variant="timelineAlternating"]::before {
    content: '';
    position: absolute;
    left: 50%;
    top: 0.5rem;
    bottom: 0.5rem;
    width: 2px;
    background: var(--border-strong);
    transform: translateX(-50%);
    z-index: 0;
}

/* Base Card Logic */
.smart-layout[data-variant="timelineAlternating"] .card {
    position: relative;
    border: none;
    background: transparent;
    box-shadow: none;
    padding: 1rem 0;
    margin-bottom: 0; /* Reset margins */
}
/* Revert card ornaments for this variant (it's minimal) */
.smart-layout[data-variant="timelineAlternating"] .card::after { display: none; }
.smart-layout[data-variant="timelineAlternating"] .card-content { border-top: none; }

/* Odd Items (Left Side) */
.smart-layout[data-variant="timelineAlternating"] .card:nth-child(odd) {
    grid-column: 1;
    text-align: right;
    padding-right: 2rem;
    align-items: flex-end; /* Align content to rail */
}

/* Even Items (Right Side) */
.smart-layout[data-variant="timelineAlternating"] .card:nth-child(even) {
    grid-column: 3;
    text-align: left;
    padding-left: 2rem;
    align-items: flex-start; /* Align content to rail */
}

/* The Nodes (Dots) */
.smart-layout[data-variant="timelineAlternating"] .card::before {
    content: '';
    position: absolute;
    top: 1.5rem; /* Align with title */
    width: 12px;
    height: 12px;
    background: #fff;
    border: 3px solid var(--accent-primary);
    border-radius: 50%;
    z-index: 2;
    box-shadow: 0 0 0 4px #f8f7f4; /* Breathing room */
}

/* Node Position for Left Items (Right edge) */
.smart-layout[data-variant="timelineAlternating"] .card:nth-child(odd)::before {
    right: -2.35rem; /* -1rem (gap/2) - 0.75rem (dot centerline) */
    /* Calculation: Grid col 2 is 2rem. Center is 1rem. 
       Card is in col 1. Right edge is at start of col 2.
       Dot needs to be at center of col 2. (Move right 1rem).
       Wait, padding-right is 2rem. card content ends 2rem from edge.
       Border relative to .card? Yes.
       right: - (half rail + half dot)? No.
       The rail is in Column 2. .card is Column 1.
       If card spans col 1, simply: right: -1rem? 
       Grid gap is 0. Col 2 is 2rem wide. Center is 1rem from Right edge of Col 1.
       So right: -1rem - 6px (half dot). = -1.375rem approx.
       Let's use calc.
    */
    right: calc(-1rem - 6px);
}

/* Node Position for Right Items (Left edge) */
.smart-layout[data-variant="timelineAlternating"] .card:nth-child(even)::before {
    left: calc(-1rem - 6px);
}

/* Year Highlight */
.smart-layout[data-variant="timelineAlternating"] .card-year {
    font-size: 1.25rem;
    color: var(--accent-primary);
    margin-bottom: 0.25rem;
}
"""

with open(css_path, "a", encoding="utf-8") as f:
    f.write(alternating_css)

print("Appended Alternating Timeline CSS.")
