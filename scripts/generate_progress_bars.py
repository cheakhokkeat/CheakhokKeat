import json
from pathlib import Path
from html import escape

DATA_PATH = Path("progress-bars.json")
OUT_DIR = Path("assets/progress")

BG = "#050A0F"
BORDER = "#00BFFF"
TEXT = "#C9D1D9"
BAR_BG = "#123038"
BAR_FILL = "#00BFFF"

CARD_W = 320
CARD_H = 44

def make_svg(label: str, percent: int) -> str:
    percent = max(0, min(100, int(percent)))
    fill_w = int(180 * percent / 100)

    label = escape(label)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}">
  <rect x="0.5" y="0.5" width="{CARD_W-1}" height="{CARD_H-1}" rx="8" fill="{BG}" stroke="{BORDER}" stroke-opacity="0.45"/>
  <text x="12" y="18" fill="{TEXT}" font-size="12" font-family="Consolas, monospace">{label}</text>
  <text x="{CARD_W-12}" y="18" fill="{TEXT}" font-size="12" font-family="Consolas, monospace" text-anchor="end">{percent}%</text>
  <rect x="12" y="24" width="296" height="10" rx="5" fill="{BAR_BG}"/>
  <rect x="12" y="24" width="{fill_w * 296 / 180:.1f}" height="10" rx="5" fill="{BAR_FILL}"/>
</svg>'''

def main():
    items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for item in items:
        file_name = item["file"].strip()
        label = item["label"].strip()
        percent = int(item["percent"])

        svg = make_svg(label, percent)
        out_path = OUT_DIR / f"{file_name}.svg"
        out_path.write_text(svg, encoding="utf-8")
        print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()