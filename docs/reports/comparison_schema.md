COMPARISON TYPES: EDUCATIONAL SLIDE SCHEMA
🎓 Design Goals

This schema is designed specifically for teaching slides, not dashboards or analytics.

Key principles:

Conceptual comparisons over numerical metrics

Clear cognitive structure for learners

Automatic layout switching

Compatible with animated slide engines

Comparisons should help students understand:

Differences between concepts

Strengths and limitations

When to use each option

How approaches relate to each other

🎯 Comparison Layout Types

Two layouts exist:

comparisonCards

Used when there are 2–3 subjects

comparisonTable

Used when there are 4+ subjects

Both layouts share the same JSON structure.
The renderer decides how to display it.

Shared Comparison Schema
{
  "type": "comparisonCards",
  "title": "Comparison Title",

  "criteria": [
    {
      "id": "c1",
      "label": "Purpose"
    },
    {
      "id": "c2",
      "label": "Strength"
    },
    {
      "id": "c3",
      "label": "Best Use"
    }
  ],

  "subjects": [
    {
      "id": "s1",
      "label": "Subject A",
      "values": [
        {
          "criterion_id": "c1",
          "value": "Explanation of the purpose"
        },
        {
          "criterion_id": "c2",
          "value": "Main strength"
        },
        {
          "criterion_id": "c3",
          "value": "Typical usage scenario"
        }
      ]
    },

    {
      "id": "s2",
      "label": "Subject B",
      "values": [
        {
          "criterion_id": "c1",
          "value": "Explanation of the purpose"
        },
        {
          "criterion_id": "c2",
          "value": "Main strength"
        },
        {
          "criterion_id": "c3",
          "value": "Typical usage scenario"
        }
      ]
    }
  ],

  "conclusion": "Short summary explaining the key difference."
}
Rendering as Comparison Cards

When subjects ≤ 3, render as cards.

Example visualization:

┌─────────────────────┐
│     Subject A       │
│---------------------│
Purpose:              │
Explanation text      │
                     │
Strength:             │
Explanation text      │
                     │
Best Use:             │
Explanation text      │
└─────────────────────┘

┌─────────────────────┐
│     Subject B       │
│---------------------│
Purpose:              │
Explanation text      │
                     │
Strength:             │
Explanation text      │
                     │
Best Use:             │
Explanation text      │
└─────────────────────┘

Cards emphasize qualitative understanding.

Rendering as Comparison Table

When subjects > 3, render as table.

Criterion        Subject A      Subject B      Subject C      Subject D
-----------------------------------------------------------------------
Purpose          Explanation    Explanation    Explanation    Explanation

Strength         Explanation    Explanation    Explanation    Explanation

Best Use         Explanation    Explanation    Explanation    Explanation

Tables support larger comparisons.

Layout Selection Logic

Generator rule:

def select_comparison_layout(num_subjects):
    if num_subjects <= 3:
        return "comparisonCards"
    return "comparisonTable"

This ensures smooth automatic layout switching.

Content Guidelines for Educational Slides

Each comparison should:

1. Focus on understanding

Not raw statistics.

Prefer:

Purpose
How it works
Strength
Limitation
Best use case

Avoid:

Efficiency %
Speed metrics
Benchmarks
Scores
2. Keep criteria limited

Recommended limits:

subjects: 2–5
criteria: 3–5

Too many rows create cognitive overload.

3. Keep explanations short

Each value should be:

6–14 words

Long paragraphs should be avoided.

Example 1 — Teaching Method Comparison
{
  "type": "comparisonCards",
  "title": "Lecture vs AI Tutor",

  "criteria": [
    {"id": "c1", "label": "Learning Style"},
    {"id": "c2", "label": "Interaction"},
    {"id": "c3", "label": "Best For"}
  ],

  "subjects": [
    {
      "id": "s1",
      "label": "Lecture",
      "values": [
        {"criterion_id": "c1", "value": "Teacher explains concepts sequentially"},
        {"criterion_id": "c2", "value": "Students mostly listen"},
        {"criterion_id": "c3", "value": "Large classroom instruction"}
      ]
    },
    {
      "id": "s2",
      "label": "AI Tutor",
      "values": [
        {"criterion_id": "c1", "value": "Concepts explained through visuals"},
        {"criterion_id": "c2", "value": "Students interact during learning"},
        {"criterion_id": "c3", "value": "Self-paced study"}
      ]
    }
  ],

  "conclusion": "AI tutors enable interactive learning while lectures scale to large groups."
}
Example 2 — Programming Approach Comparison
{
  "type": "comparisonCards",
  "title": "Rule-Based AI vs Machine Learning",

  "criteria": [
    {"id": "c1", "label": "How It Works"},
    {"id": "c2", "label": "Strength"},
    {"id": "c3", "label": "Limitation"}
  ],

  "subjects": [
    {
      "id": "s1",
      "label": "Rule-Based Systems",
      "values": [
        {"criterion_id": "c1", "value": "Follows predefined logic rules"},
        {"criterion_id": "c2", "value": "Predictable decisions"},
        {"criterion_id": "c3", "value": "Limited adaptability"}
      ]
    },
    {
      "id": "s2",
      "label": "Machine Learning",
      "values": [
        {"criterion_id": "c1", "value": "Learns patterns from data"},
        {"criterion_id": "c2", "value": "Improves with more examples"},
        {"criterion_id": "c3", "value": "Harder to interpret"}
      ]
    }
  ]
}
Animation Integration (For Your Slide Engine)

The comparison block should be treated as the primary block.

Animation behavior:

comparisonCards → animate card by card
comparisonTable → animate row by row

Example animation order:

Row 1 appears
Row 2 appears
Row 3 appears
Row 4 appears

Narration segments should match number of criteria rows.

Validation Rules
def validate_comparison(data):

    subjects = data.get("subjects", [])
    criteria = data.get("criteria", [])

    if len(subjects) < 2:
        return False

    if len(subjects) > 5:
        return False

    if len(criteria) < 2:
        return False

    if len(criteria) > 5:
        return False

    for subject in subjects:
        if len(subject.get("values", [])) != len(criteria):
            return False

    return True