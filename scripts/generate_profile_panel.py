"""Rebuild the joined README panel and waves: python scripts/generate_profile_panel.py.

Replace assets/profile-avatar.jpg with a new portrait to update the photo.
The portrait is embedded because SVG images cannot load external resources.
Use --github-user USERNAME to download the latest avatar (requires Pillow).
"""

import argparse
import base64
from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


ASSETS = Path(__file__).resolve().parents[1] / "assets"
# Shared by the profile and divider so future palette changes stay consistent.
GRADIENT_STOPS = '''<stop offset="0%" stop-color="#8F00FF" />
      <stop offset="25%" stop-color="#00BFFF" />
      <stop offset="50%" stop-color="#A855FF" />
      <stop offset="75%" stop-color="#00D9FF" />
      <stop offset="100%" stop-color="#8F00FF" />'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-user", help="Refresh the portrait from this GitHub account")
    args = parser.parse_args()
    if args.github_user:
        from PIL import Image, ImageOps

        request = Request(
            f"https://github.com/{quote(args.github_user, safe='')}.png?size=460",
            headers={"User-Agent": "profile-panel-workflow"},
        )
        with urlopen(request, timeout=30) as response:
            downloaded = response.read()
        # Validate and normalize before replacing the existing portrait.
        with Image.open(BytesIO(downloaded)) as photo:
            normalized = ImageOps.exif_transpose(photo).convert("RGB")
            output = BytesIO()
            normalized.save(output, format="JPEG", quality=95)
        (ASSETS / "profile-avatar.jpg").write_bytes(output.getvalue())

    portrait = base64.b64encode((ASSETS / "profile-avatar.jpg").read_bytes()).decode("ascii")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="854" height="600" viewBox="0 0 854 600">
  <title>Cheakhok Keat</title>
  <desc>Circular profile portrait with a decorative green online badge, name and software engineering roles between purple and cyan waves.</desc>
  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1" y2="0">
      {GRADIENT_STOPS}
    </linearGradient>
    <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.22" />
      <stop offset="65%" stop-color="#FFFFFF" stop-opacity="0" />
    </linearGradient>
    <filter id="text-shadow" x="-10%" y="-30%" width="120%" height="170%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#32116B" flood-opacity="0.65" />
    </filter>
    <clipPath id="portrait"><circle cx="427" cy="250" r="149.5" /></clipPath>
  </defs>
  <path fill="url(#background)" opacity="0.22" d="M0 28C130 78 220 0 360 27S640 82 854 22V569C700 516 620 600 470 571S170 527 0 575Z" />
  <path fill="url(#background)" opacity="0.45" d="M0 48C160 -5 250 79 415 45S710 10 854 48V550C690 602 570 523 415 559S140 587 0 550Z" />
  <path fill="url(#background)" d="M0 65C145 112 245 22 410 60S690 105 854 62V533C700 489 600 582 435 543S155 506 0 545Z" />
  <path fill="url(#sheen)" d="M0 65C145 112 245 22 410 60S690 105 854 62V533C700 489 600 582 435 543S155 506 0 545Z" />
  <g fill="none" stroke="#E0FCFF" stroke-width="1.5" opacity="0.6">
    <path d="M0 65C145 112 245 22 410 60S690 105 854 62" />
    <path d="M0 545C155 506 270 504 435 543S700 489 854 533" />
  </g>
  <circle cx="427" cy="250" r="156" fill="none" stroke="#E0FCFF" stroke-width="2" opacity="0.65" />
  <image x="277.5" y="100.5" width="299" height="299" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait)" xlink:href="data:image/jpeg;base64,{portrait}" />
  <!-- Decorative status badge; this does not track live GitHub presence. -->
  <g>
    <title>Online (decorative)</title>
    <circle cx="533" cy="356" r="25" fill="#050A0F" />
    <circle cx="533" cy="356" r="18" fill="#39FF14" />
    <circle cx="533" cy="356" r="18" fill="none" stroke="#39FF14" stroke-width="2" opacity="0">
      <animate attributeName="r" values="18;31" dur="2s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.6;0" dur="2s" repeatCount="indefinite" />
    </circle>
  </g>
  <g fill="#F2FFFF" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" filter="url(#text-shadow)">
    <text x="427" y="455" font-size="55" font-weight="700">Cheakhok Keat</text>
    <text x="427" y="500" font-size="15">Software Engineer (Full-Stack Web) | AI Automations | Solutions Architect</text>
    <animate attributeName="opacity" values="1;0.9;1" dur="4s" repeatCount="indefinite" />
  </g>
</svg>
'''
    (ASSETS / "profile-panel.svg").write_text(svg, encoding="utf-8")
    divider = f'''<svg xmlns="http://www.w3.org/2000/svg" width="854" height="180" viewBox="0 0 854 180">
  <title>Purple and cyan joined waves</title>
  <defs>
    <linearGradient id="wave" x1="0" y1="0" x2="1" y2="0">
      {GRADIENT_STOPS}
    </linearGradient>
  </defs>
  <!-- Each silhouette spans the center, so there is no seam between the two waves. -->
  <g fill="url(#wave)">
    <path opacity="0.22" d="M0 28C130 78 220 0 360 27S640 82 854 22V149C700 96 620 180 470 151S170 107 0 155Z" />
    <path opacity="0.45" d="M0 48C160 -5 250 79 415 45S710 10 854 48V130C690 182 570 103 415 139S140 167 0 130Z" />
    <path d="M0 65C145 112 245 22 410 60S690 105 854 62V113C700 69 600 162 435 123S155 86 0 125Z" />
  </g>
  <g fill="none" stroke="#E0FCFF" stroke-width="1.5" opacity="0.6">
    <path d="M0 65C145 112 245 22 410 60S690 105 854 62" />
    <path d="M0 125C155 86 270 84 435 123S700 69 854 113" />
  </g>
</svg>
'''
    (ASSETS / "wave-divider.svg").write_text(divider, encoding="utf-8")


if __name__ == "__main__":
    main()
