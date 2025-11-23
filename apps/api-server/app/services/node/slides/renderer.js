/* ------------------------------------------------------
   renderer.js — Core Slide Rendering Engine
   Reads slide JSON from backend → Renders HTML using CSS layouts
   Works with: layouts.css, blocks.css, typography.css, components.css, etc.
--------------------------------------------------------- */

// GLOBAL STATE
let SLIDES = {};          // slide data from Python backend
let SUBTOPICS = [];       // list of subtopics
let currentSubId = null;  // current subtopic id
let currentIndex = 0;     // slide index within subtopic

/* ------------------------------------------------------ */
/* LOAD STATE FROM BACKEND */
/* ------------------------------------------------------ */
export function loadState(jsonState) {
    SLIDES = jsonState.slides;
    SUBTOPICS = jsonState.sub_topics;
    // default: first subtopic
    currentSubId = SUBTOPICS[0].id;
    currentIndex = 0;
    renderSlide();
}

/* ------------------------------------------------------ */
/* MAIN RENDER FUNCTION */
/* ------------------------------------------------------ */
export function renderSlide() {
    const slideData = SLIDES[currentSubId][currentIndex];
    if (!slideData) return;

    const container = document.getElementById("slide-root");
    container.innerHTML = ""; // clear previous slide

    // Create slide wrapper
    const slide = document.createElement("div");
    const layoutClass = slideData.design?.layout_mode 
                 || slideData.layout 
                 || "layout-center";

    slide.className = `slide ${layoutClass} fade-in`;

    // Helper to append content to correct container
    let textContainer = slide;
    let visualContainer = slide;

    // If split layout, create wrappers
    if (slideData.layout === "layout-left" || slideData.layout === "layout-right" || slideData.layout === "layout-split") {
        textContainer = document.createElement("div");
        textContainer.className = "text";
        visualContainer = document.createElement("div");
        visualContainer.className = "visual";
    }

    /* TITLE */
    if (slideData.title) {
        const titleEl = document.createElement("h1");
        titleEl.textContent = slideData.title;
        titleEl.className = "fade-up";
        textContainer.appendChild(titleEl);
    }

    /* POINTS */
    if (slideData.points && slideData.points.length > 0) {
        const ul = document.createElement("ul");
        ul.className = "points stagger";
        slideData.points.forEach(pt => {
            const li = document.createElement("li");
            li.textContent = pt;
            ul.appendChild(li);
        });
        textContainer.appendChild(ul);
    }

    /* CONTENT BLOCKS */
    if (slideData.contentBlocks) {
        slideData.contentBlocks.forEach(block => {
            const blockEl = renderBlock(block);
            if (blockEl) {
                // Heuristic: Text-heavy blocks go to text container, visual blocks to visual container
                if (["explanation", "story", "takeaways"].includes(block.type)) {
                    textContainer.appendChild(blockEl);
                } else {
                    visualContainer.appendChild(blockEl);
                }
            }
        });
    }

    /* IMAGE */
    // Auto-construct image path if using AI images
    if (slideData.imageType === "ai_enhanced_image" && !slideData.imageURL) {
        const safeTitle = slideData.title.replace(/ /g, "_");
        // Assuming images are stored in static/images/{sub_id}/{Title_With_Underscores}.png
        slideData.imageURL = `static/images/${currentSubId}/${safeTitle}.png`;
        slideData.has_image = true;
    }

    if (slideData.has_image && slideData.imageURL) {
        const img = document.createElement("img");
        img.src = slideData.imageURL;
        img.className = "fade-up";
        visualContainer.appendChild(img);
    }

    // Append containers to slide if split layout
    if (slideData.layout === "layout-left" || slideData.layout === "layout-right" || slideData.layout === "layout-split") {
        slide.appendChild(textContainer);
        slide.appendChild(visualContainer);
    }

    container.appendChild(slide);
    updateProgressBar();
    updateSlideIndicator();
}

/* ------------------------------------------------------ */
/* RENDER DIFFERENT BLOCK TYPES */
/* ------------------------------------------------------ */
function renderBlock(block) {
    switch (block.type) {

        case "timeline":
            return renderTimeline(block);

        case "explanation":
            return renderExplanation(block);

        case "comparison":
            return renderComparison(block);

        case "statistics":
            return renderStatistics(block);

        case "story":
            return renderStory(block);

        case "takeaways":
            return renderTakeaways(block);

        default:
            return null;
    }
}

/* ---------------- TIMELINE ---------------- */
function renderTimeline(block) {
    const wrap = document.createElement("div");
    wrap.className = "timeline fade-up";

    block.events.forEach(ev => {
        const item = document.createElement("div");
        item.className = "timeline-item";

        const year = document.createElement("h4");
        year.textContent = ev.year;

        const desc = document.createElement("p");
        desc.textContent = ev.description;

        item.appendChild(year);
        item.appendChild(desc);
        wrap.appendChild(item);
    });
    return wrap;
}

/* ---------------- EXPLANATION ---------------- */
function renderExplanation(block) {
    const wrap = document.createElement("div");
    wrap.className = "block-explanation fade-up";

    block.paragraphs.forEach(txt => {
        const p = document.createElement("p");
        p.textContent = txt;
        wrap.appendChild(p);
    });

    return wrap;
}

/* ---------------- COMPARISON ---------------- */
function renderComparison(block) {
    const wrap = document.createElement("div");
    wrap.className = "comparison fade-up";

    const left = document.createElement("div");
    left.className = "side";
    left.innerHTML = `<h3>${block.left_title || "Left"}</h3>`;
    block.left_points?.forEach(p => {
        const li = document.createElement("p"); li.textContent = p;
        left.appendChild(li);
    });

    const right = document.createElement("div");
    right.className = "side";
    right.innerHTML = `<h3>${block.right_title || "Right"}</h3>`;
    block.right_points?.forEach(p => {
        const li = document.createElement("p"); li.textContent = p;
        right.appendChild(li);
    });

    wrap.appendChild(left);
    wrap.appendChild(right);
    return wrap;
}

/* ---------------- STATISTICS ---------------- */
function renderStatistics(block) {
    const wrap = document.createElement("div");
    wrap.className = "statistics fade-up";

    block.items.forEach(stat => {
        const box = document.createElement("div");
        box.className = "stat";

        box.innerHTML = `
      <div class="stat-number">${stat.value}</div>
      <div class="stat-label">${stat.label}</div>
    `;

        wrap.appendChild(box);
    });

    return wrap;
}

/* ---------------- STORY ---------------- */
function renderStory(block) {
    const wrap = document.createElement("div");
    wrap.className = "story fade-up";
    wrap.textContent = block.text;
    return wrap;
}

/* ---------------- TAKEAWAYS ---------------- */
function renderTakeaways(block) {
    const wrap = document.createElement("div");
    wrap.className = "takeaways fade-up";

    const ul = document.createElement("ul");
    block.items.forEach(t => {
        const li = document.createElement("li");
        li.textContent = t;
        ul.appendChild(li);
    });

    wrap.appendChild(ul);
    return wrap;
}

/* ------------------------------------------------------ */
/* SLIDE NAVIGATION */
/* ------------------------------------------------------ */
export function nextSlide() {
    const list = SLIDES[currentSubId];
    if (currentIndex < list.length - 1) {
        currentIndex++;
        renderSlide();
    }
}

export function prevSlide() {
    if (currentIndex > 0) {
        currentIndex--;
        renderSlide();
    }
}

/* ------------------------------------------------------ */
/* UI UPDATES */
/* ------------------------------------------------------ */
function updateProgressBar() {
    const el = document.querySelector(".progress-bar");
    if (!el) return;

    const total = SLIDES[currentSubId].length;
    const percent = ((currentIndex + 1) / total) * 100;
    el.style.width = percent + "%";
}

function updateSlideIndicator() {
    const el = document.querySelector(".slide-indicator");
    if (!el) return;

    const total = SLIDES[currentSubId].length;
    el.textContent = `${currentIndex + 1} / ${total}`;
}
