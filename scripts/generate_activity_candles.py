"""
Generates a GitHub Activity SVG Chart with TradingView Candlestick Styling.

Features:
- Auto-detects display name directly from the GitHub account via GraphQL API.
- Fixed baseline rendering so candle bodies sit flush at Open = 0.
- Populated HUD (O H L C) readout.
- Vibrant Moving Average line (#8A2BE2).
"""

import os
import sys
import json
import urllib.request

GH_USERNAME = os.environ.get("GH_USERNAME")
GH_TOKEN = os.environ.get("GH_TOKEN")

DAYS = 60
OUT_PATH = os.environ.get("OUT_PATH", "../assets/activity-candles.svg")

# Palette Configuration
BULL_COLOR = "#00A6FF"      # Bright Cyan Accent
BEAR_COLOR = "#F23645"      # Red Accent
BG_DARK = "#0d1117"         # Dark Canvas
GRID_COLOR = "#21262d"      # Grid Dividers
TEXT_PRIMARY = "#c9d1d9"    # Main Text
TEXT_MUTED = "#8b949e"      # Muted Labels
MA_COLOR = "#8A2BE2"        # Purple Moving Average
FONT_FAMILY = "ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace"

GRAPHQL_URL = "https://api.github.com/graphql"

# Added 'name' and 'login' to retrieve full name automatically
QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
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


def fetch_user_data_and_contributions(login: str, token: str):
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

    user_data = data["data"]["user"]
    
    # Auto-detect display name (falls back to username if full name is empty)
    display_name = user_data.get("name") or user_data.get("login") or login

    weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append((day["date"], day["contributionCount"]))
    days.sort(key=lambda d: d[0])
    
    return display_name, days


def build_candles(days):
    """
    Constructs candle datasets:
    - hud_open/hud_low: Populated metrics for top HUD display.
    - open: Locked to 0 for SVG rendering so candles anchor on the baseline axis.
    """
    candles = []
    last_active_commits = 0

    for date, commits in days:
        if commits == 0:
            hud_open = 0
            close = 0
            high = 0
            hud_low = 0
            is_bull = True
        else:
            hud_open = last_active_commits
            close = commits

            if commits >= last_active_commits:
                # Bullish Candle
                high = max(commits, hud_open) + max(0.4, commits * 0.15)
                hud_low = min(hud_open, close)
                is_bull = True
            else:
                # Bearish Candle
                high = max(commits, hud_open) + 0.3
                hud_low = min(hud_open, close)
                is_bull = False

            last_active_commits = commits

        candles.append({
            "date": date,
            "commits": commits,
            "open": 0,  # Always 0 for rendering alignment
            "close": close,
            "high": round(high, 1),
            "low": 0,    # Always 0 for rendering alignment
            "hud_open": round(hud_open, 1),
            "hud_low": round(hud_low, 1),
            "is_bull": is_bull,
        })

    return candles[-DAYS:]


def render_svg(display_name, candles, out_path):
    width = 900
    height = 300
    pad_left = 35
    pad_right = 65
    pad_top = 55
    pad_bottom = 35
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    max_val = max((c["high"] for c in candles), default=1)
    max_val = max(max_val, 6)

    n = len(candles)
    candle_w = plot_w / max(n, 1)
    body_w = max(candle_w * 0.55, 6)

    def y_of(v):
        return pad_top + plot_h - (v / max_val) * plot_h

    total = sum(c["commits"] for c in candles)
    active_days = sum(1 for c in candles if c["commits"] > 0)

    # Dynamic HUD readout targeting latest active commit session
    active_candles = [c for c in candles if c["commits"] > 0]
    hud_c = active_candles[-1] if active_candles else candles[-1]
    hud_color = BULL_COLOR if hud_c["is_bull"] else BEAR_COLOR

    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT_FAMILY}">',
        '<defs>',
        '  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">',
        '    <feGaussianBlur stdDeviation="1.8" result="blur" />',
        '    <feComposite in="SourceGraphic" in2="blur" operator="over" />',
        '  </filter>',
        '</defs>',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="10" fill="{BG_DARK}" stroke="#30363d" stroke-width="1.5"/>',

        # --- Header with Auto-detected Display Name ---
        f'<text x="{pad_left}" y="24" fill="{TEXT_PRIMARY}" font-size="14" font-weight="600" letter-spacing="0.5">{display_name}&#39;s Activity // Last {n} Days</text>',
        f'<text x="{width - pad_right}" y="24" fill="{BULL_COLOR}" font-size="12" font-weight="600" text-anchor="end">{total} commits · {active_days} active days</text>',

        # --- Dynamic HUD Status Readout ---
        f'<text x="{pad_left}" y="42" fill="{TEXT_MUTED}" font-size="11">'
        f'<tspan fill="{TEXT_MUTED}">O </tspan><tspan fill="{TEXT_PRIMARY}">{hud_c["hud_open"]}</tspan> '
        f'<tspan fill="{TEXT_MUTED}">H </tspan><tspan fill="{TEXT_PRIMARY}">{hud_c["high"]}</tspan> '
        f'<tspan fill="{TEXT_MUTED}">L </tspan><tspan fill="{TEXT_PRIMARY}">{hud_c["hud_low"]}</tspan> '
        f'<tspan fill="{TEXT_MUTED}">C </tspan><tspan fill="{hud_color}">{hud_c["close"]}</tspan>'
        f'</text>',
    ]

    # --- Grid Lines ---
    grid_steps = 4
    for i in range(grid_steps + 1):
        frac = i / grid_steps
        gy = pad_top + plot_h - frac * plot_h
        val = frac * max_val
        svg_parts.append(
            f'<line x1="{pad_left}" y1="{gy:.1f}" x2="{width - pad_right}" y2="{gy:.1f}" stroke="{GRID_COLOR}" stroke-width="1" stroke-dasharray="2,3"/>'
        )
        if i > 0:
            svg_parts.append(
                f'<text x="{width - pad_right + 8}" y="{gy + 3.5:.1f}" fill="{TEXT_MUTED}" font-size="10" text-anchor="start">{round(val)}</text>'
            )

    # --- Smooth Purple EMA Trendline ---
    ma_points = []
    ema = candles[0]["commits"]
    k = 2 / (5 + 1)
    for i, c in enumerate(candles):
        cx = pad_left + i * candle_w + candle_w / 2
        ema = (c["commits"] * k) + (ema * (1 - k))
        ma_points.append((cx, y_of(ema)))

    # --- Render Candlesticks (Grounded at Open=0) ---
    for i, c in enumerate(candles):
        cx = pad_left + i * candle_w + candle_w / 2
        color = BULL_COLOR if c["is_bull"] else BEAR_COLOR

        if c["commits"] == 0:
            zero_y = y_of(0)
            svg_parts.append(
                f'<line x1="{cx - body_w/2:.1f}" y1="{zero_y:.1f}" x2="{cx + body_w/2:.1f}" y2="{zero_y:.1f}" stroke="{BULL_COLOR}" stroke-width="1.5" opacity="0.35"/>'
            )
        else:
            y_high = y_of(c["high"])
            y_low = y_of(0)
            y_open = y_of(0)
            y_close = y_of(c["close"])

            body_top = min(y_open, y_close)
            body_h = abs(y_close - y_open)

            # High/Low Wick
            svg_parts.append(
                f'<line x1="{cx:.1f}" y1="{y_high:.1f}" x2="{cx:.1f}" y2="{y_low:.1f}" stroke="{color}" stroke-width="1.5"/>'
            )

            # Grounded Candle Body
            svg_parts.append(
                f'<rect x="{cx - body_w/2:.1f}" y="{body_top:.1f}" width="{body_w:.1f}" height="{max(body_h, 3):.1f}" fill="{color}" rx="1"/>'
            )

    # --- Draw Trendline ---
    ma_path = " ".join([f"{'M' if idx == 0 else 'L'} {px:.1f} {py:.1f}" for idx, (px, py) in enumerate(ma_points)])
    svg_parts.append(
        f'<path d="{ma_path}" fill="none" stroke="{MA_COLOR}" stroke-width="2" opacity="0.95" filter="url(#glow)"/>'
    )

    # --- Right Side Target Badge ---
    last_c = candles[-1]
    last_cy = y_of(last_c["commits"])
    badge_bg = BULL_COLOR if last_c["is_bull"] else BEAR_COLOR
    svg_parts.append(
        f'<rect x="{width - pad_right + 2}" y="{last_cy - 9:.1f}" width="32" height="18" rx="3" fill="{badge_bg}"/>'
        f'<text x="{width - pad_right + 18}" y="{last_cy + 3.5:.1f}" fill="#FFFFFF" font-size="10" font-weight="bold" text-anchor="middle">{last_c["commits"]}</text>'
    )

    # --- X-Axis Date Labels ---
    step = max(1, n // 6)
    for i, c in enumerate(candles):
        if i % step == 0 or i == n - 1:
            cx = pad_left + i * candle_w + candle_w / 2
            label = c["date"][5:]
            svg_parts.append(
                f'<text x="{cx:.1f}" y="{height - pad_bottom + 18}" fill="{TEXT_MUTED}" font-size="10" text-anchor="middle">{label}</text>'
            )

    svg_parts.append("</svg>")
    svg = "\n".join(svg_parts)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {out_path} for user: {display_name}")


def main():
    if not GH_USERNAME or not GH_TOKEN:
        print("GH_USERNAME and GH_TOKEN env vars are required.", file=sys.stderr)
        sys.exit(1)

    display_name, days = fetch_user_data_and_contributions(GH_USERNAME, GH_TOKEN)
    if len(days) < 2:
        print("Not enough contribution data yet.", file=sys.stderr)
        sys.exit(1)

    candles = build_candles(days)
    render_svg(display_name, candles, OUT_PATH)


if __name__ == "__main__":
    main()