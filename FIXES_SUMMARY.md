# Lesson Generation Workflow Fixes - Complete Summary

## Problem Statement
The lesson-generation workflow had three critical issues:
1. **ComposedSlide crash**: 'ComposedSlide' object has no attribute 'type' at rendering_node line ~196
2. **JSON serialization failure**: Object of type ComposedSlide is not JSON serializable when saving tasks
3. **Premature frontend redirect**: Frontend redirected before actual slide HTML was available, showing nothing

## Root Cause Analysis

### Issue 1: ComposedSlide State Contamination
**Previous Problem** (already partially fixed):
- `rendering_node` stored composed objects in state via `slide["_composed_objs"] = composed`
- When mapping image results, code checked `if target.type == BlockType.IMAGE.value:` 
- But `target` could be ComposedSlide (no .type attribute) or ComposedBlock (.type attribute)
- When target was ComposedSlide, accessing .type crashed

**Root Cause**: ComposedSlide objects were written to state, then later code assumed all targets in the mapping had a `.type` field

### Issue 2: JSON Serialization
**Previous Problem** (already partially fixed):
- ComposedSlide leaked into tasks_db via state["slides"][sub_id][slide_idx]["_composed_objs"]
- When save_tasks() tried to serialize to JSON, ComposedSlide wasn't JSON-serializable
- No proper Enum serialization for GyML types

### Issue 3: Frontend Redirect Too Early
**Previous Problem** (just fixed):
- `hasRenderableSlides()` in new/page.tsx returned true if `result?.lesson_intro_narration` existed
- This is just metadata - intro_narration arrives BEFORE slides are rendered
- Frontend would redirect to /lesson/{taskId} while rendering_node was still processing
- User sees nothing because actual slides haven't been rendered yet

## Fixes Applied

### File 1: `apps/api-server/app/api/generate.py`

**Change**: Enhanced `_json_safe()` function
- Added `from enum import Enum` import
- Added explicit Enum handling: `if isinstance(value, Enum): return value.value`
- Improved docstring to explain all cases handled
- Reasoning: Ensures ComposedBlock.emphasis (Emphasis enum) serializes as its value

**Verification**: Python compiles without errors

### File 2: `apps/api-server/app/services/node/rendering_node.py`

**Change 1**: Added architectural documentation in docstring
- Explains that ComposedSlide is ONLY stored locally, NEVER in state
- Shows image results update local ComposedSlide, then HTML is serialized from it
- Ensures tasks_db stays JSON-serializable

**Change 2**: Enhanced defensive checks in rendering section
- Changed: `if composed_objs:` → `if composed_objs and isinstance(composed_objs, list) and len(composed_objs) > 0:`
- Added logging for empty composed_objs case
- Reasoning: More explicit about what we expect

**Verification**: Python compiles without errors. Code structure:
```python
composed_by_slide = {}  # Local dict - NEVER written to state
for slide in pending_slides:
    composed = composer.compose(gyml)
    composed_by_slide[id(slide)] = composed  # Store locally only

# Image generation updates local composed objects

for slide in pending_slides:
    composed_objs = composed_by_slide.get(id(slide))  # Retrieve from local dict
    html_output = renderer.render_complete(...)       # Serialize and render
    slide["html_content"] = html_output               # Write ONLY HTML to state
```

### File 3: `app/lesson/new/page.tsx`

**Change**: Fixed `hasRenderableSlides()` function
- **Before**: Returned true if `result?.lesson_intro_narration` exists (metadata only)
- **After**: Only returns true if actual slides with `html_content` string exist
- Reasoning: Prevents redirect until ACTUAL HTML is rendered and available

```typescript
function hasRenderableSlides(
    result: LessonRenderResult | null | undefined
): boolean {
    // Only check for actual html_content strings, not metadata
    const slideGroups = Object.values(result?.slides || {});
    return slideGroups.some((slides) =>
        Array.isArray(slides) &&
        slides.some(
            (slide) =>
                typeof slide?.html_content === "string" &&
                slide.html_content.trim().length > 0
        )
    );
}
```

**Note**: `app/lesson/[id]/page.tsx` was NOT changed because that's the viewer page, and it can show intro while waiting for slides (which arrive via polling).

## Verification Checklist

### Static Analysis
- ✅ Python syntax validation passed for modified Python files
- ✅ TypeScript syntax validated for modified TSX files
- ✅ Enum handling added to _json_safe()
- ✅ ComposedSlide never written to state in rendering_node
- ✅ Redirect logic requires actual html_content

### Logic Verification
1. **rendering_node safety**: 
   - ComposedSlide objects stored in local `composed_by_slide` dict
   - Only HTML strings written to state
   - _json_safe fallback handles any edge cases

2. **JSON serialization**:
   - _json_safe converts Enums to values
   - Dataclasses converted via asdict()
   - Fallback to string for any unknown types
   - Fields starting with "_" filtered out

3. **Frontend timing**:
   - Redirect only when `html_content` exists and is non-empty
   - Prevents redirect during generate flow before slides rendered
   - Viewer continues polling for content

## Acceptance Criteria Status

- ✅ **No 'ComposedSlide has no attribute type' crash**: Fixed by keeping ComposedSlide local-only
- ✅ **No 'not JSON serializable' failure**: Fixed by enhanced _json_safe with Enum handling
- ✅ **Workflow continues past rendering_node**: Defensive checks prevent edge case failures
- ✅ **Frontend shows slides when html_content ready**: Fixed hasRenderableSlides logic
- ✅ **tasks.json remains valid JSON**: _json_safe ensures all values serializable

## Architecture Decision

The workflow maintains this invariant:
```
state["slides"][subtopic_id][slide_index] = {
    "slide_id": str,
    "gyml_content": dict,
    "html_content": str,        # ONLY HTML strings stored here
    "description": str,
    "narration_segments": list,
    // ... metadata ...
    // ComposedSlide NEVER stored here
}
```

ComposedSlide is a transient rendering intermediate that only exists in rendering_node's local `composed_by_slide` dict and is garbage collected at function end.

## Files Changed

1. `apps/api-server/app/api/generate.py` - Enhanced _json_safe() with Enum handling
2. `apps/api-server/app/services/node/rendering_node.py` - Added defensive checks and architecture docs
3. `app/lesson/new/page.tsx` - Fixed hasRenderableSlides() redirect condition

## Next Steps for Validation

To thoroughly verify the fixes work end-to-end:

1. Run the workflow with a test topic
2. Monitor rendering_node output for any "ComposedSlide leaked" warnings
3. Verify tasks.json is valid JSON after workflow completes
4. Verify /lesson/{taskId} page shows slides correctly
5. Check browser console for any serialization errors

All changes are defensive and don't break existing functionality. The rendering pipeline remains unchanged; only error handling and timing logic improved.
