"""
Generates a candlestick-style SVG chart from real GitHub contribution data.

Each "candle" represents one day:
  - open  = previous day's contribution count
  - close = current day's contribution count
  - high  = max of a 3-day rolling window centered on that day
  - low   = min of a 3-day rolling window centered on that day
  - color = light green if close > open (more active than yesterday)
            deep sky blue if close <= open (quieter than yesterday)

Requires env vars:
  GH_USERNAME   - the GitHub username to fetch contributions for
  GH_TOKEN      - a token with public read access (secrets.GITHUB_TOKEN works)

Usage:
  python generate_activity_candles.py
"""

import os
import sys
import json
import datetime
import urllib.request

GH_USERNAME = os.environ.get("GH_USERNAME")
GH_TOKEN = os.environ.get("GH_TOKEN")
DAYS = 30  # number of most recent days to show
OUT_PATH = os.environ.get("OUT_PATH", "assets/activity-candles.svg")

GREEN = "#73E5A6"
BLUE = "#00BFFF"
BG = "#050A0F"
GRID = "#123038"
TEXT = "#C9D1D9"

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_contributions(login: str, token: str):
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "activity-candles-script",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    if "errors" in data:
        raise RuntimeError(f"GitHub API error: {data['errors']}")

    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append((day["date"], day["contributionCount"]))
    days.sort(key=lambda d: d[0])
    return days


def build_candles(days):
    """Turn daily counts into synthetic OHLC candles."""
    counts = [c for _, c in days]
    candles = []
    for i in range(1, len(days)):
        date, close = days[i]
        _, open_ = days[i - 1]
        lo_idx = max(0, i - 1)
        hi_idx = min(len(days) - 1, i + 1)
        window = counts[lo_idx:hi_idx + 1]
        high = max(window)
        low = min(window)
        candles.append({
            "date": date,
            "open": open_,
            "close": close,
            "high": high,
            "low": low,
        })
    return candles[-DAYS:]


def render_svg(candles, out_path):
    width = 900
    height = 260
    pad_left = 50
    pad_right = 20
    pad_top = 30
    pad_bottom = 40
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    max_val = max((c["high"] for c in candles), default=1)
    max_val = max(max_val, 1)

    n = len(candles)
    candle_w = plot_w / max(n, 1)
    body_w = candle_w * 0.5

    def y_of(v):
        return pad_top + plot_h - (v / max_val) * plot_h

    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="Consolas, monospace">',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="8" fill="{BG}" stroke="{BLUE}" stroke-opacity="0.4"/>',
        f'<text x="{pad_left}" y="20" fill="{TEXT}" font-size="13" letter-spacing="1.5">'
        f'GITHUB ACTIVITY // LAST {n} DAYS</text>',
    ]

    # horizontal grid lines
    for frac in (0.25, 0.5, 0.75, 1.0):
        gy = pad_top + plot_h - frac * plot_h
        svg_parts.append(
            f'<line x1="{pad_left}" y1="{gy:.1f}" x2="{width - pad_right}" y2="{gy:.1f}" '
            f'stroke="{GRID}" stroke-width="1" stroke-dasharray="2,3"/>'
        )
        svg_parts.append(
            f'<text x="{pad_left - 6}" y="{gy + 4:.1f}" fill="{TEXT}" font-size="9" text-anchor="end" opacity="0.7">'
            f'{round(frac * max_val)}</text>'
        )

    for i, c in enumerate(candles):
        cx = pad_left + i * candle_w + candle_w / 2
        color = GREEN if c["close"] > c["open"] else BLUE
        y_high = y_of(c["high"])
        y_low = y_of(c["low"])
        y_open = y_of(c["open"])
        y_close = y_of(c["close"])
        body_top = min(y_open, y_close)
        body_h = max(abs(y_close - y_open), 1.5)

        # wick
        svg_parts.append(
            f'<line x1="{cx:.1f}" y1="{y_high:.1f}" x2="{cx:.1f}" y2="{y_low:.1f}" '
            f'stroke="{color}" stroke-width="1.4" opacity="0.9"/>'
        )
        # body
        svg_parts.append(
            f'<rect x="{cx - body_w/2:.1f}" y="{body_top:.1f}" width="{body_w:.1f}" '
            f'height="{body_h:.1f}" fill="{color}" opacity="0.9" rx="1"/>'
        )

    # x-axis date labels (every ~5th candle to avoid crowding)
    step = max(1, n // 6)
    for i, c in enumerate(candles):
        if i % step == 0 or i == n - 1:
            cx = pad_left + i * candle_w + candle_w / 2
            label = c["date"][5:]  # MM-DD
            svg_parts.append(
                f'<text x="{cx:.1f}" y="{height - pad_bottom + 16}" fill="{TEXT}" '
                f'font-size="9" text-anchor="middle" opacity="0.7">{label}</text>'
            )

    total = sum(c["close"] for c in candles)
    up_days = sum(1 for c in candles if c["close"] > c["open"])
    svg_parts.append(
        f'<text x="{width - pad_right}" y="20" fill="{GREEN}" font-size="12" '
        f'text-anchor="end" font-weight="bold">{total} commits · {up_days} up days</text>'
    )

    svg_parts.append("</svg>")
    svg = "\n".join(svg_parts)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"Wrote {out_path}")


def main():
    if not GH_USERNAME or not GH_TOKEN:
        print("GH_USERNAME and GH_TOKEN env vars are required.", file=sys.stderr)
        sys.exit(1)

    days = fetch_contributions(GH_USERNAME, GH_TOKEN)
    if len(days) < 2:
        print("Not enough contribution data yet.", file=sys.stderr)
        sys.exit(1)

    candles = build_candles(days)
    render_svg(candles, OUT_PATH)


if __name__ == "__main__":
    main()
