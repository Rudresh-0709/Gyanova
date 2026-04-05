from __future__ import annotations

from pathlib import Path


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>statsBadgeGrid Preview</title>
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
      width: min(760px, 100%);
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      overflow: visible;
    }
    .tile {
      position: relative;
      min-height: 170px;
      padding: 18px 18px 16px;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
    }
    .tile:nth-child(1) {
      clip-path: polygon(0 0, calc(100% - 16px) 0, 100% 50%, calc(100% - 16px) 100%, 0 100%, 0 62%, 12px 50%, 0 38%);
    }
    .tile:nth-child(2) {
      clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 16px), 50% 100%, 0 calc(100% - 16px), 0 0);
    }
    .tile:nth-child(3) {
      clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 62%, 12px 50%, 0 38%);
    }
    .tile:nth-child(4) {
      clip-path: polygon(16px 0, 100% 0, 100% 62%, calc(100% - 12px) 50%, 100% 38%, 100% 100%, 0 100%, 0 0);
    }
    .tile:nth-child(1),
    .tile:nth-child(4) { background: #dc2a2a; }
    .tile:nth-child(2),
    .tile:nth-child(3) { background: #484b52; }
    .inner {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
    }
    .metric {
      margin: 0;
      font-size: 54px;
      font-weight: 900;
      line-height: 0.95;
      letter-spacing: -0.04em;
    }
    .text {
      margin: 0;
      max-width: 18ch;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.3;
      text-transform: uppercase;
    }
    .tile:nth-child(1)::after,
    .tile:nth-child(4)::after {
      content: "";
      position: absolute;
      top: 50%;
      width: 14px;
      height: 6px;
      background: #7c828b;
      transform: translateY(-50%);
    }
    .tile:nth-child(1)::after { right: -14px; }
    .tile:nth-child(4)::after { left: -14px; }
    .tile:nth-child(1)::before,
    .tile:nth-child(2)::before,
    .tile:nth-child(4)::before {
      content: "";
      position: absolute;
      z-index: 3;
    }
    .tile:nth-child(1)::before {
      top: 50%;
      right: -24px;
      transform: translateY(-50%);
      border-top: 6px solid transparent;
      border-bottom: 6px solid transparent;
      border-left: 12px solid #7c828b;
    }
    .tile:nth-child(2)::after {
      content: "";
      position: absolute;
      left: 50%;
      bottom: -14px;
      width: 6px;
      height: 14px;
      background: #7c828b;
      transform: translateX(-50%);
    }
    .tile:nth-child(2)::before {
      left: 50%;
      bottom: -24px;
      transform: translateX(-50%);
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-top: 12px solid #7c828b;
    }
    .tile:nth-child(4)::before {
      top: 50%;
      left: -24px;
      transform: translateY(-50%);
      border-top: 6px solid transparent;
      border-bottom: 6px solid transparent;
      border-right: 12px solid #7c828b;
    }
    @media (max-width: 560px) {
      .block { grid-template-columns: 1fr; }
      .tile::before,
      .tile::after { display: none; }
    }
  </style>
</head>
<body>
  <section class="block" aria-label="Standalone statsBadgeGrid block preview">
    <article class="tile"><div class="inner"><h2 class="metric">65%</h2><p class="text">Lesson completion increased after the guided revision step.</p></div></article>
    <article class="tile"><div class="inner"><h2 class="metric">89%</h2><p class="text">Learners retained the core definition after the recap checkpoint.</p></div></article>
    <article class="tile"><div class="inner"><h2 class="metric">37%</h2><p class="text">Initial baseline confidence before scaffolded examples were shown.</p></div></article>
    <article class="tile"><div class="inner"><h2 class="metric">46%</h2><p class="text">Applied problem accuracy gained after comparing both methods.</p></div></article>
  </section>
</body>
</html>
"""


def main() -> None:
    output_path = Path(__file__).with_name("stats_badge_grid_preview.html")
    output_path.write_text(HTML, encoding="utf-8")
    print(f"Wrote preview to: {output_path}")


if __name__ == "__main__":
    main()
