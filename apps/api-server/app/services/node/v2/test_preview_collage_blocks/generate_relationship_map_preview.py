from __future__ import annotations

from pathlib import Path


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>relationshipMap Preview</title>
  <link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet" />
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      background: #ffffff;
      color: #15202b;
    }
    .page {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
    }
    .block {
      position: relative;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      align-items: center;
      width: min(1220px, 100%);
      margin: 0 auto;
      padding: 8px 20px;
    }
    .circle {
      position: relative;
      aspect-ratio: 1 / 1;
      border-radius: 999px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 34px;
      text-align: center;
      text-transform: uppercase;
    }
    .circle--side {
      background: #7f858d;
      color: #ffffff;
    }
    .circle--center {
      background: rgba(255, 255, 255, 0.94);
      color: #1f2937;
      border: 1px solid rgba(148, 163, 184, 0.32);
    }
    .circle__inner {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      max-width: 18ch;
    }
    .circle__title {
      margin: 0;
      font-size: 16px;
      font-weight: 800;
      letter-spacing: 0.08em;
      line-height: 1.2;
    }
    .circle__text {
      margin: 0;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.45;
      letter-spacing: 0.04em;
    }
    .connector {
      position: absolute;
      right: -8px;
      width: 66px;
      height: 66px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #d73939;
      color: #ffffff;
      border: 4px solid rgba(255, 255, 255, 0.92);
      box-shadow: 0 12px 28px rgba(215, 57, 57, 0.22);
      z-index: 4;
    }
    .connector i { font-size: 32px; }
    .connector--low {
      top: 66%;
      transform: translate(50%, -50%);
    }
    .connector--high {
      top: 32%;
      transform: translate(50%, -50%);
    }
    @media (max-width: 960px) {
      .block {
        grid-template-columns: 1fr;
        gap: 28px;
        padding: 12px;
      }
      .circle {
        max-width: 340px;
        margin: 0 auto;
      }
      .connector {
        right: 50%;
        top: auto;
        bottom: -24px;
        transform: translateX(50%);
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <section aria-label="Standalone relationshipMap block preview">
      <div class="block">
        <article class="circle circle--side">
          <div class="circle__inner">
            <h2 class="circle__title">Input Layer</h2>
            <p class="circle__text">Raw signals enter the lesson flow and establish the first learning anchor.</p>
          </div>
          <div class="connector connector--low" aria-hidden="true">
            <i class="ri-computer-line"></i>
          </div>
        </article>

        <article class="circle circle--center">
          <div class="circle__inner">
            <h2 class="circle__title">Core Concept</h2>
            <p class="circle__text">The central idea connects both sides and carries the main teaching message.</p>
          </div>
          <div class="connector connector--high" aria-hidden="true">
            <i class="ri-bar-chart-box-line"></i>
          </div>
        </article>

        <article class="circle circle--side">
          <div class="circle__inner">
            <h2 class="circle__title">Outcome Layer</h2>
            <p class="circle__text">The final node shows the result, comparison point, or applied takeaway.</p>
          </div>
        </article>
      </div>
    </section>
  </div>
</body>
</html>
"""


def main() -> None:
    output_path = Path(__file__).with_name("relationship_map_preview.html")
    output_path.write_text(HTML, encoding="utf-8")
    print(f"Wrote preview to: {output_path}")


if __name__ == "__main__":
    main()
