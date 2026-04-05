from __future__ import annotations

from pathlib import Path


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ribbonFold Preview</title>
  <link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet" />
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      background: #ffffff;
      font-family: "Segoe UI", Arial, sans-serif;
    }
    .block {
      width: min(1100px, 100%);
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      align-items: start;
    }
    .ribbon {
      position: relative;
      min-height: 320px;
      padding: 24px 18px 64px;
      clip-path: polygon(0 0, 100% 0, 100% 84%, 50% 100%, 0 84%);
      color: #fff;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
    }
    .ribbon:nth-child(odd) { background: #d92929; }
    .ribbon:nth-child(even) { background: #36383f; }
    .ribbon:nth-child(2),
    .ribbon:nth-child(4) { margin-top: 18px; }
    .ribbon::before {
      content: "";
      position: absolute;
      top: 0;
      left: -12px;
      width: 12px;
      height: 100%;
      background: rgba(0, 0, 0, 0.22);
      clip-path: polygon(100% 0, 0 8%, 0 92%, 100% 100%);
    }
    .ribbon:first-child::before { display: none; }
    .icon {
      width: 58px;
      height: 58px;
      border-radius: 999px;
      margin-bottom: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255,255,255,0.95);
      color: #1f2937;
    }
    .icon i { font-size: 29px; }
    .title {
      margin: 0 0 12px;
      font-size: 18px;
      font-weight: 800;
      line-height: 1.15;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .text {
      margin: 0;
      font-size: 14px;
      line-height: 1.45;
      font-weight: 700;
      text-transform: uppercase;
    }
    @media (max-width: 900px) {
      .block { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 560px) {
      .block { grid-template-columns: 1fr; }
      .ribbon:nth-child(2),
      .ribbon:nth-child(4) { margin-top: 0; }
      .ribbon::before { display: none; }
    }
  </style>
</head>
<body>
  <section class="block" aria-label="Standalone ribbonFold block preview">
    <article class="ribbon">
      <div class="icon"><i class="ri-shield-star-line"></i></div>
      <h2 class="title">Input Frame</h2>
      <p class="text">Start with the first theme, fact set, or teaching pillar.</p>
    </article>
    <article class="ribbon">
      <div class="icon"><i class="ri-star-smile-line"></i></div>
      <h2 class="title">Key Value</h2>
      <p class="text">Use the second ribbon for the paired contrast or support point.</p>
    </article>
    <article class="ribbon">
      <div class="icon"><i class="ri-apps-2-line"></i></div>
      <h2 class="title">Focus Area</h2>
      <p class="text">Place the central applied idea here with concise supporting copy.</p>
    </article>
    <article class="ribbon">
      <div class="icon"><i class="ri-bar-chart-grouped-line"></i></div>
      <h2 class="title">Outcome</h2>
      <p class="text">Close with the result, metric, or takeaway learners should remember.</p>
    </article>
  </section>
</body>
</html>
"""


def main() -> None:
    output_path = Path(__file__).with_name("ribbon_fold_preview.html")
    output_path.write_text(HTML, encoding="utf-8")
    print(f"Wrote preview to: {output_path}")


if __name__ == "__main__":
    main()
