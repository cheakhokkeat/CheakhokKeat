import json
from pathlib import Path

DATA_PATH = Path("progress-bars.json")
OUT_DIR = Path("assets/progress")


def gradient_color(pct: int) -> str:
    stops = [
        {"p": 0, "c": (255, 23, 68)},    # Neon Red
        {"p": 25, "c": (255, 145, 0)},   # Orange
        {"p": 50, "c": (212, 255, 0)},   # Lime
        {"p": 75, "c": (77, 255, 136)},  # Light Green
        {"p": 100, "c": (0, 191, 255)},  # Deep Sky Blue
    ]

    start = stops[0]
    end = stops[-1]

    for i in range(len(stops) - 1):
        if stops[i]["p"] <= pct <= stops[i + 1]["p"]:
            start = stops[i]
            end = stops[i + 1]
            break

    if end["p"] == start["p"]:
        t = 0
    else:
        t = (pct - start["p"]) / (end["p"] - start["p"])

    r = round(start["c"][0] + t * (end["c"][0] - start["c"][0]))
    g = round(start["c"][1] + t * (end["c"][1] - start["c"][1]))
    b = round(start["c"][2] + t * (end["c"][2] - start["c"][2]))

    return f"#{r:02X}{g:02X}{b:02X}"


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )


def build_svg(label: str, percent: int, color: str = None, width: int = 410, segments: int = 24) -> str:
    pct = max(0, min(100, int(percent)))
    w = int(width)
    seg_count = int(segments)
    h = 70

    bar_color = color if color else gradient_color(pct)

    filled = round((seg_count * pct) / 100)
    seg_w = (w - 40) / seg_count
    gap = 3

    segs_svg = ""
    for i in range(seg_count):
        x = 20 + i * seg_w
        is_filled = i < filled
        fill = bar_color if is_filled else "#0A1A1F"
        stroke = bar_color if is_filled else "#123038"
        opacity = "1" if is_filled else "0.5"

        segs_svg += (
            f'<rect x="{x:.1f}" y="34" width="{(seg_w - gap):.1f}" height="14" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="0.6" opacity="{opacity}" rx="1.5"/>'
        )

    corner = 14
    safe_label = escape_xml(label.upper())

    svg = f'''<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="1.6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="6" fill="#050A0F" stroke="{bar_color}" stroke-width="1" opacity="0.55"/>

  <path d="M6 {corner} V6 H{corner}" fill="none" stroke="{bar_color}" stroke-width="2" filter="url(#glow)"/>
  <path d="M{w - corner} 6 H{w - 6} V{corner}" fill="none" stroke="{bar_color}" stroke-width="2" filter="url(#glow)"/>
  <path d="M6 {h - corner} V{h - 6} H{corner}" fill="none" stroke="{bar_color}" stroke-width="2" filter="url(#glow)"/>
  <path d="M{w - corner} {h - 6} H{w - 6} V{h - corner}" fill="none" stroke="{bar_color}" stroke-width="2" filter="url(#glow)"/>

  <text x="20" y="20" font-family="Consolas, 'Courier New', monospace" font-size="11" letter-spacing="1.5" fill="#C9D1D9">{safe_label}</text>
  <text x="{w - 20}" y="20" font-family="Consolas, 'Courier New', monospace" font-size="13" font-weight="bold" fill="{bar_color}" text-anchor="end" filter="url(#glow)">{pct}%</text>

  {segs_svg}
</svg>'''

    return svg


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} not found.")

    items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for item in items:
        file_name = item["file"].strip()
        label = item["label"].strip()
        percent = int(item["percent"])

        color = item.get("color")
        width = int(item.get("width", 410))
        segments = int(item.get("segments", 24))

        if color:
            color = f"#{str(color).replace('#', '').upper()}"

        svg = build_svg(
            label=label,
            percent=percent,
            color=color,
            width=width,
            segments=segments,
        )

        out_path = OUT_DIR / f"{file_name}.svg"
        out_path.write_text(svg, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()