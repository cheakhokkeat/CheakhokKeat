"""Rebuild the README panel: python scripts/generate_profile_panel.py.

Replace assets/profile-avatar.jpg with a new portrait to update the photo.
The portrait is embedded because SVG images cannot load external resources.
"""

import base64
from pathlib import Path


ASSETS = Path(__file__).resolve().parents[1] / "assets"


def main():
    portrait = base64.b64encode((ASSETS / "profile-avatar.jpg").read_bytes()).decode("ascii")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="854" height="340" viewBox="0 0 854 340">
  <title>Cheakhok Keat</title>
  <desc>Circular profile portrait on a purple and cyan gradient.</desc>
  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#5B00FF" />
      <stop offset="20%" stop-color="#7A00FF" />
      <stop offset="40%" stop-color="#00BFFF" />
      <stop offset="50%" stop-color="#00D9FF" />
      <stop offset="60%" stop-color="#4169E1" />
      <stop offset="80%" stop-color="#8A2BE2" />
      <stop offset="100%" stop-color="#5B00FF" />
    </linearGradient>
    <clipPath id="portrait"><circle cx="427" cy="190" r="149.5" /></clipPath>
  </defs>
  <path fill="url(#background)" d="M0 0h854v340H0z" />
  <path fill="#000000" fill-opacity="0.316" d="M0 0h854v340H0z" />
  <image x="277.5" y="40.5" width="299" height="299" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait)" xlink:href="data:image/jpeg;base64,{portrait}" />
</svg>
'''
    (ASSETS / "profile-panel.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
