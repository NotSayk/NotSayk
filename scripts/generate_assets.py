#!/usr/bin/env python3
"""Generate the 'Port du Havre / Docker' themed SVG assets for the NotSayk profile.

Usage: python3 scripts/generate_assets.py [output_dir]   (default: assets/)
"""
import math
import sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path(__file__).resolve().parent.parent / "assets"

NAVY_0 = "#07111F"
NAVY_1 = "#0B1D33"
NAVY_2 = "#12355B"
NAVY_3 = "#1D4E89"
ORANGE = "#FF7A1A"
SAND = "#F4A261"
FOAM = "#E0E6ED"
MONO = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"
SANS = "'Segoe UI','Helvetica Neue',Roboto,Arial,sans-serif"


def wave_path(y, amp, period, width, height_to):
    """Periodic wave closed down to `height_to`, drawn from x=-period to width+period."""
    d = f"M{-period},{y} "
    x = -period
    while x < width + period:
        d += f"q{period/4},{-amp} {period/2},0 t{period/2},0 "
        x += period
    d += f"L{x},{height_to} L{-period},{height_to} Z"
    return d


def waves(y0, width, height, layers):
    out = []
    for i, (dy, amp, period, color, op, dur) in enumerate(layers):
        out.append(
            f'<g><path d="{wave_path(y0 + dy, amp, period, width, height)}" fill="{color}" opacity="{op}">'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{-period if i % 2 == 0 else period} 0" '
            f'dur="{dur}s" repeatCount="indefinite"/></path></g>'
        )
    return "\n".join(out)


def container(x, y, w, h, color, label, code, text_color="#FFFFFF", font=18):
    """Side view of a shipping container with corrugation, doors and a label."""
    ribs = "".join(
        f'<line x1="{x + i}" y1="{y + 5}" x2="{x + i}" y2="{y + h - 5}" stroke="#000" stroke-opacity=".18" stroke-width="2"/>'
        for i in range(10, int(w) - 6, 9)
    )
    bw = min(w - 8, max(w * 0.72, len(label) * font * 0.62 + 16))
    return f'''
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{color}"/>
    {ribs}
    <rect x="{x}" y="{y}" width="{w}" height="4" fill="#000" fill-opacity=".25"/>
    <rect x="{x}" y="{y + h - 4}" width="{w}" height="4" fill="#000" fill-opacity=".3"/>
    <rect x="{x + w/2 - bw/2}" y="{y + h/2 - font*0.85}" width="{bw}" height="{font*1.6}" rx="3" fill="{NAVY_1 if text_color == '#FFFFFF' else '#FFFFFF'}" fill-opacity="{'.55' if text_color == '#FFFFFF' else '.6'}"/>
    <text x="{x + w/2}" y="{y + h/2 + font*0.32}" text-anchor="middle" font-family="{MONO}" font-weight="800" font-size="{font}" fill="{text_color}" letter-spacing="1">{label}</text>
    <text x="{x + 6}" y="{y + 14}" font-family="{MONO}" font-size="8" fill="#fff" fill-opacity=".75">{code}</text>'''


# ---------------------------------------------------------------- header (day / night cycle)
def mix(a, b, t):
    """Blend two #RRGGBB colors."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


# Key moments of the day: sky gradient (top → horizon), sea layers, land, and how dark it is.
NIGHT = dict(sky=["#03070F", "#0A1830", "#11264A", "#1A3358"], sea=["#0F2744", "#16375C", "#0B1F37", "#07111F"],
             land="#040A14", dark=1.0)
SKY_KEYS = [
    (0.0, NIGHT),
    (5.0, NIGHT),
    (6.5, dict(sky=["#1B2A4E", "#4B4E7D", "#C9748F", "#F6B78C"], sea=["#3A4F7A", "#5C6F9A", "#2A3D63", "#1B2A4E"],
               land="#1C2340", dark=0.6)),
    (8.5, dict(sky=["#3E8ED0", "#6FB1E4", "#A7D3F2", "#DCEFFB"], sea=["#2E7FB8", "#4A9AD0", "#1F6597", "#154C75"],
               land="#3A5677", dark=0.0)),
    (13.0, dict(sky=["#2F7FD0", "#58A6E6", "#92CAF2", "#CBE8FB"], sea=["#2B7DB8", "#4799D0", "#1D6497", "#144B75"],
                land="#3A5677", dark=0.0)),
    (17.0, dict(sky=["#3A7CC0", "#6FA8DA", "#B6D3EA", "#F2DDB8"], sea=["#2C6FA3", "#4B8BBE", "#1E5785", "#143F66"],
                land="#33506F", dark=0.05)),
    (19.5, dict(sky=["#07111F", "#1D2F55", "#7A3E5C", "#E76F51"], sea=[NAVY_2, NAVY_3, "#0E2A4A", NAVY_1],
                land="#0A1A2E", dark=0.75)),
    (21.0, dict(sky=["#050B16", "#102040", "#2D2F5A", "#5A3E66"], sea=["#102A48", "#18385E", "#0C213A", "#08131F"],
                land="#06101D", dark=0.95)),
    (22.5, NIGHT),
    (24.0, NIGHT),
]
SUNRISE, SUNSET = 6.0, 21.0


def palette(hour):
    for (h0, a), (h1, b) in zip(SKY_KEYS, SKY_KEYS[1:]):
        if h0 <= hour <= h1:
            t = (hour - h0) / (h1 - h0)
            return dict(
                sky=[mix(x, y, t) for x, y in zip(a["sky"], b["sky"])],
                sea=[mix(x, y, t) for x, y in zip(a["sea"], b["sea"])],
                land=mix(a["land"], b["land"], t),
                dark=a["dark"] + (b["dark"] - a["dark"]) * t,
            )
    return dict(NIGHT)


def moment(hour):
    if hour < 5 or hour >= 22:
        return "de nuit"
    if hour < 8:
        return "au lever du jour"
    if hour < 17:
        return "en pleine journée"
    if hour < 20.5:
        return "au coucher du soleil"
    return "à la tombée de la nuit"


def header(hour=19.5, out=None):
    W, H = 1200, 380
    horizon = 270
    pal = palette(hour)
    dark = pal["dark"]
    land = pal["land"]
    day = 1 - dark
    lights = max(0.0, min(1.0, (dark - 0.3) / 0.5))

    stars = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff"><animate attributeName="opacity" values=".2;1;.2" dur="{d}s" begin="{b}s" repeatCount="indefinite"/></circle>'
        for cx, cy, r, d, b in [
            (90, 40, 1.2, 3, 0), (240, 22, 1, 4, 1), (380, 55, 1.4, 3.5, .5), (520, 30, 1, 5, 2),
            (640, 70, 1.1, 4, 1.5), (760, 25, 1.3, 3, .2), (880, 48, 1, 4.5, 2.5), (980, 18, 1.2, 3.8, 1),
            (1100, 60, 1, 4.2, .8), (1160, 30, 1.4, 3.2, 1.8), (700, 110, .9, 5, 3), (450, 100, .9, 4, 2.2),
            (160, 120, .9, 4.4, 1.2), (310, 140, 1, 3.6, .4), (590, 150, .8, 4.8, 2.8), (840, 130, 1, 3.9, 1.6),
        ]
    )
    stars_opacity = max(0.0, (dark - 0.45) / 0.55)

    # Sun and moon travel along an arc to the right of the title.
    def arc(t):
        return 680 + t * 480, horizon + 12 - math.sin(math.pi * t) * 215

    bodies, reflect_x, reflect_color, reflect_op = "", 0, SAND, 0.0
    if SUNRISE <= hour <= SUNSET:
        t = (hour - SUNRISE) / (SUNSET - SUNRISE)
        sx, sy = arc(t)
        alt = math.sin(math.pi * t)
        core = mix(ORANGE, "#FFF6D5", min(1, alt * 1.6))
        bodies += (
            f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{95 + 40 * alt:.0f}" fill="url(#glow)" opacity="{0.55 + 0.35 * alt:.2f}"/>'
            f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{34 - 6 * alt:.0f}" fill="{core}"/>'
        )
        if alt < 0.4:
            reflect_x, reflect_color, reflect_op = sx, SAND, 1 - alt / 0.4
    if hour >= 20.5 or hour <= 6.5:
        t = ((hour - 20.5) % 24) / 10
        mx, my = arc(t)
        fade = max(0.0, min(1.0, t * 6, (1 - t) * 6))
        bodies += f'''
    <g opacity="{fade:.2f}">
      <circle cx="{mx:.1f}" cy="{my:.1f}" r="70" fill="url(#moonglow)"/>
      <circle cx="{mx:.1f}" cy="{my:.1f}" r="22" fill="#F1F4F8"/>
      <circle cx="{mx - 7:.1f}" cy="{my - 5:.1f}" r="4" fill="#D5DCE5"/><circle cx="{mx + 6:.1f}" cy="{my + 7:.1f}" r="5" fill="#D5DCE5"/>
      <circle cx="{mx + 8:.1f}" cy="{my - 9:.1f}" r="2.5" fill="#D5DCE5"/>
    </g>'''
        if fade > 0.3 and not reflect_op:
            reflect_x, reflect_color, reflect_op = mx, "#DCE6F2", 0.55 * fade

    cloud_fill = mix("#FFFFFF", pal["sky"][2], 0.25 + 0.6 * dark)
    clouds = "".join(
        f'''
    <g opacity="{(0.1 + 0.8 * day) * o:.2f}">
      <animateTransform attributeName="transform" type="translate" from="-260 0" to="{W + 60} 0" dur="{dur}s" begin="-{beg}s" repeatCount="indefinite"/>
      <g transform="translate(0 {cy}) scale({sc})" fill="{cloud_fill}">
        <ellipse cx="60" cy="20" rx="60" ry="16"/><ellipse cx="40" cy="10" rx="28" ry="18"/><ellipse cx="80" cy="6" rx="32" ry="22"/>
      </g>
    </g>'''
        for cy, sc, o, dur, beg in [(46, 1.0, .9, 140, 30), (190, .7, .7, 110, 75), (120, .55, .6, 170, 120)]
    )
    gulls = "".join(
        f'''
    <g opacity="{day:.2f}">
      <animateTransform attributeName="transform" type="translate" from="{x0} {y0}" to="{x0 + 260} {y0 - 40}" dur="{dur}s" repeatCount="indefinite"/>
      <path d="M0,0 q6,-6 12,0 q6,-6 12,0" fill="none" stroke="{NAVY_1}" stroke-width="2" stroke-linecap="round">
        <animate attributeName="d" values="M0,0 q6,-6 12,0 q6,-6 12,0;M0,-3 q6,3 12,3 q6,0 12,-3;M0,0 q6,-6 12,0 q6,-6 12,0" dur="1.1s" repeatCount="indefinite"/>
      </path>
    </g>'''
        for x0, y0, dur in [(560, 200, 26), (600, 215, 31)]
    )

    # Le Havre skyline: Saint-Joseph tower, Niemeyer "Volcan", gantry cranes
    skyline = f'''
    <g fill="{land}">
      <!-- Église Saint-Joseph -->
      <rect x="1004" y="{horizon-70}" width="60" height="70"/>
      <polygon points="1016,{horizon-70} 1052,{horizon-70} 1046,{horizon-175} 1022,{horizon-175}"/>
      <polygon points="1022,{horizon-175} 1046,{horizon-175} 1034,{horizon-215}"/>
      <rect x="1031" y="{horizon-232}" width="6" height="20"/>
      <!-- Le Volcan -->
      <path d="M890,{horizon} C895,{horizon-40} 915,{horizon-52} 945,{horizon-52} C975,{horizon-52} 990,{horizon-40} 995,{horizon} Z"/>
      <path d="M850,{horizon} C852,{horizon-18} 862,{horizon-24} 875,{horizon-24} C888,{horizon-24} 896,{horizon-18} 898,{horizon} Z"/>
      <!-- Immeubles Perret -->
      <rect x="1075" y="{horizon-48}" width="34" height="48"/>
      <rect x="1112" y="{horizon-36}" width="28" height="36"/>
      <rect x="1142" y="{horizon-56}" width="40" height="56"/>
      <rect x="800" y="{horizon-30}" width="45" height="30"/>
    </g>
    <g fill="#FFD27A" opacity="{0.9 * lights:.2f}">
      <rect x="1080" y="{horizon-40}" width="3" height="3"/><rect x="1090" y="{horizon-30}" width="3" height="3"/>
      <rect x="1150" y="{horizon-44}" width="3" height="3"/><rect x="1165" y="{horizon-30}" width="3" height="3"/>
      <rect x="1118" y="{horizon-24}" width="3" height="3"/><rect x="812" y="{horizon-20}" width="3" height="3"/>
      <rect x="1030" y="{horizon-50}" width="3" height="5"/><rect x="1096" y="{horizon-20}" width="3" height="3"/>
      <rect x="1158" y="{horizon-20}" width="3" height="3"/><rect x="826" y="{horizon-12}" width="3" height="3"/>
    </g>'''

    def crane(x, s=1.0):
        h = 120 * s
        return f'''
      <g stroke="{land}" stroke-width="{4*s}" fill="none">
        <line x1="{x}" y1="{horizon}" x2="{x}" y2="{horizon-h}"/>
        <line x1="{x+30*s}" y1="{horizon}" x2="{x+30*s}" y2="{horizon-h}"/>
        <line x1="{x}" y1="{horizon-h*0.45}" x2="{x+30*s}" y2="{horizon-h*0.2}"/>
        <line x1="{x+30*s}" y1="{horizon-h*0.45}" x2="{x}" y2="{horizon-h*0.2}"/>
        <line x1="{x-70*s}" y1="{horizon-h}" x2="{x+60*s}" y2="{horizon-h}" stroke-width="{6*s}"/>
        <line x1="{x+15*s}" y1="{horizon-h-25*s}" x2="{x-70*s}" y2="{horizon-h}"/>
        <line x1="{x+15*s}" y1="{horizon-h-25*s}" x2="{x+60*s}" y2="{horizon-h}"/>
      </g>
      <circle cx="{x+15*s}" cy="{horizon-h-27*s}" r="{2.5*s}" fill="#FF3B3B"><animate attributeName="opacity" values="1;.1;1" dur="2s" repeatCount="indefinite"/></circle>'''

    cranes = crane(640, .8) + crane(735, 1.0)

    lighthouse = f'''
    <g>
      <path d="M0,{horizon+14} L0,{horizon-4} L95,{horizon-4} L110,{horizon+14} Z" fill="{land}"/>
      <polygon points="40,{horizon} 66,{horizon} 61,{horizon-95} 45,{horizon-95}" fill="#E8EDF2"/>
      <rect x="43" y="{horizon-70}" width="20" height="10" fill="#E63946"/>
      <rect x="44" y="{horizon-40}" width="20" height="10" fill="#E63946"/>
      <rect x="44" y="{horizon-108}" width="18" height="13" fill="{land}"/>
      <circle cx="53" cy="{horizon-101}" r="5" fill="{mix('#7A8797', '#FFE29A', lights)}"/>
      <polygon points="40,{horizon-112} 66,{horizon-112} 53,{horizon-124}" fill="{land}"/>
      <g opacity="{0.4 * lights:.2f}">
        <polygon points="53,{horizon-101} 420,{horizon-150} 420,{horizon-60}" fill="url(#beam)">
          <animateTransform attributeName="transform" type="rotate" values="-25 53 {horizon-101};20 53 {horizon-101};-25 53 {horizon-101}" dur="8s" repeatCount="indefinite"/>
        </polygon>
      </g>
    </g>'''

    window = mix(NAVY_1, "#FFD27A", lights)
    ship_colors = [ORANGE, "#2A9D8F", "#E9C46A", "#E63946", "#457B9D", SAND, "#8E44AD", "#2A9D8F", ORANGE, "#E9C46A"]
    boxes = ""
    for row in range(3):
        for i in range(7 - row):
            c = ship_colors[(i + row * 3) % len(ship_colors)]
            bx = 30 + i * 30 + row * 8
            by = -24 - row * 14
            boxes += f'<rect x="{bx}" y="{by}" width="28" height="13" fill="{c}"/><line x1="{bx+7}" y1="{by+2}" x2="{bx+7}" y2="{by+11}" stroke="#000" stroke-opacity=".2"/><line x1="{bx+14}" y1="{by+2}" x2="{bx+14}" y2="{by+11}" stroke="#000" stroke-opacity=".2"/><line x1="{bx+21}" y1="{by+2}" x2="{bx+21}" y2="{by+11}" stroke="#000" stroke-opacity=".2"/>'
    ship = f'''
    <g>
      <animateTransform attributeName="transform" type="translate" from="-320 {horizon+6}" to="{W+40} {horizon+6}" dur="38s" repeatCount="indefinite"/>
      <g>
        <animateTransform attributeName="transform" type="rotate" values="-1.2 140 0;1.2 140 0;-1.2 140 0" dur="4s" repeatCount="indefinite"/>
        {boxes}
        <!-- superstructure -->
        <rect x="245" y="-52" width="28" height="42" fill="#E8EDF2"/>
        <rect x="241" y="-58" width="36" height="8" fill="#E8EDF2"/>
        <rect x="249" y="-46" width="4" height="4" fill="{window}"/><rect x="257" y="-46" width="4" height="4" fill="{window}"/><rect x="265" y="-46" width="4" height="4" fill="{window}"/>
        <rect x="254" y="-74" width="10" height="16" fill="{ORANGE}"/>
        <circle cx="288" cy="-14" r="2.5" fill="#4ADE80" opacity="{lights:.2f}"/>
        <!-- hull -->
        <path d="M0,-12 L290,-12 L282,18 L22,18 Z" fill="#14253D"/>
        <path d="M6,8 L286,8 L282,18 L22,18 Z" fill="#B23A2E"/>
        <text x="40" y="3" font-family="{MONO}" font-size="9" font-weight="700" fill="#fff" letter-spacing="2">NOTSAYK · LE HAVRE</text>
        <!-- smoke -->
        <circle cx="259" cy="-82" r="5" fill="#9AA7B6" opacity=".6"><animate attributeName="cy" values="-82;-115" dur="3s" repeatCount="indefinite"/><animate attributeName="opacity" values=".6;0" dur="3s" repeatCount="indefinite"/><animate attributeName="r" values="5;12" dur="3s" repeatCount="indefinite"/></circle>
        <circle cx="262" cy="-82" r="5" fill="#9AA7B6" opacity=".6"><animate attributeName="cy" values="-82;-115" dur="3s" begin="1.5s" repeatCount="indefinite"/><animate attributeName="opacity" values=".6;0" dur="3s" begin="1.5s" repeatCount="indefinite"/><animate attributeName="r" values="5;12" dur="3s" begin="1.5s" repeatCount="indefinite"/></circle>
      </g>
    </g>'''

    reflection = "".join(
        f'<rect x="{reflect_x - w/2:.1f}" y="{horizon + 6 + i*9}" width="{w}" height="2.5" rx="1.25" opacity="{.75 - i*.1:.2f}">'
        f'<animate attributeName="width" values="{w};{w*.6:.0f};{w}" dur="{2.5 + i*.4:.1f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="x" values="{reflect_x - w/2:.1f};{reflect_x - w*.3:.1f};{reflect_x - w/2:.1f}" dur="{2.5 + i*.4:.1f}s" repeatCount="indefinite"/></rect>'
        for i, w in enumerate([130, 100, 110, 70, 80, 40, 50])
    )
    sea = waves(horizon, W, H, [
        (0, 3, 120, pal["sea"][0], 1, 9),
        (18, 5, 160, pal["sea"][1], .55, 7),
        (40, 6, 200, pal["sea"][2], .9, 11),
        (70, 7, 240, pal["sea"][3], 1, 8),
    ])

    # The title switches to dark ink when the sky behind it is bright.
    behind = mix(pal["sky"][0], pal["sky"][1], 0.6)
    r, g, b = (int(behind[i:i + 2], 16) / 255 for i in (1, 3, 5))
    bright = 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.42
    title = NAVY_0 if bright else "#FFFFFF"
    subtitle = "#C2410C" if bright else ORANGE
    info = NAVY_1 if bright else FOAM
    minutes = round(hour * 60) % (24 * 60)
    clock = f"{minutes // 60:02d}:{minutes % 60:02d}"
    sky = pal["sky"]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Samuel Ampeau (@NotSayk) — le port du Havre {moment(hour)}, un porte-conteneurs traverse la baie">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{sky[0]}"/>
      <stop offset=".45" stop-color="{sky[1]}"/>
      <stop offset=".8" stop-color="{sky[2]}"/>
      <stop offset="1" stop-color="{sky[3]}"/>
    </linearGradient>
    <radialGradient id="glow" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="#FFE6A0"/>
      <stop offset=".35" stop-color="{mix(ORANGE, '#FFE6A0', day)}" stop-opacity=".6"/>
      <stop offset="1" stop-color="{ORANGE}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="moonglow" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="#DCE6F2" stop-opacity=".5"/>
      <stop offset="1" stop-color="#DCE6F2" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#FFE29A" stop-opacity="1"/>
      <stop offset="1" stop-color="#FFE29A" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <clipPath id="skyclip"><rect width="{W}" height="{horizon + 2}"/></clipPath>
  </defs>
  <style>
    .fade {{ animation: fade 1.6s ease-out both; }}
    .fade2 {{ animation: fade 1.6s .5s ease-out both; }}
    .fade3 {{ animation: fade 1.6s 1s ease-out both; }}
    @keyframes fade {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: none; }} }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{horizon}" fill="url(#sky)"/>
    <g opacity="{stars_opacity:.2f}">{stars}</g>
    <g clip-path="url(#skyclip)">{bodies}</g>
    {clouds}
    {gulls}
    {lighthouse}
    {cranes}
    {skyline}
    {sea}
    <g fill="{reflect_color}" opacity="{reflect_op:.2f}">{reflection}</g>
    {ship}
    <g class="fade">
      <text x="110" y="92" font-family="{SANS}" font-weight="800" font-size="54" fill="{title}" letter-spacing="3">SAMUEL AMPEAU</text>
    </g>
    <g class="fade2">
      <text x="112" y="128" font-family="{MONO}" font-weight="700" font-size="20" fill="{subtitle}">@NotSayk · Développeur web &amp; applications</text>
    </g>
    <g class="fade3">
      <text x="112" y="158" font-family="{MONO}" font-size="14" fill="{info}" fill-opacity=".85">⚓ Port d'attache : Le Havre — 49°29′N 0°06′E · {clock}</text>
    </g>
  </g>
</svg>
'''
    (out or OUT).joinpath("header.svg").write_text(svg)


# ---------------------------------------------------------------- container stack (skills)
def stack():
    W, H = 1000, 330
    quay = 290
    cw, ch = 112, 50
    rows = [
        [("JAVA", "#E63946"), ("PYTHON", "#2A9D8F"), ("PHP", "#6C5CE7"), ("SQL", "#457B9D"), ("C", "#5A6B7D"), ("TYPESCRIPT", "#3178C6")],
        [("HTML", ORANGE), ("CSS", "#1D7FD1"), ("JS", "#E9C46A"), ("REACT", "#149ECA"), ("NODE.JS", "#5FA04E"), ("FLASK", "#3D5A80")],
        [("DOCKER", "#2496ED"), ("LINUX", "#D4A017"), ("GIT", "#F05032"), ("GITHUB", "#3A3F4B"), ("VS CODE", "#007ACC")],
    ]
    dark_text = {"JS", "LINUX"}
    groups = []
    n = 0
    for r, row in enumerate(rows):
        offset = 40 + (cw / 2 + 3 if r == 2 else 0)
        for i, (label, color) in enumerate(row):
            x = offset + i * (cw + 6)
            y = quay - (r + 1) * (ch + 4)
            delay = 0.25 + n * 0.22
            n += 1
            tc = NAVY_1 if label in dark_text else "#FFFFFF"
            groups.append(
                f'<g class="drop" style="animation-delay:{delay:.2f}s">{container(x, y, cw, ch, color, label, f"NSKU {100 + n:03d}-{n % 10}", tc, 14)}</g>'
            )

    crane_x = 790
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Stack technique empilée en conteneurs : Java, Python, PHP, SQL, C, TypeScript, HTML, CSS, JavaScript, React, Node.js, Flask, Docker, Linux, Git, GitHub, VS Code">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{NAVY_0}"/><stop offset="1" stop-color="{NAVY_1}"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .drop {{ animation: drop .9s cubic-bezier(.3,1.4,.5,1) both; }}
    @keyframes drop {{ 0% {{ transform: translateY(-360px); opacity: 0; }} 30% {{ opacity: 1; }} 100% {{ transform: none; opacity: 1; }} }}
    .hook {{ animation: sway 3.5s ease-in-out infinite alternate; transform-origin: {crane_x - 20}px 34px; }}
    @keyframes sway {{ from {{ transform: rotate(-4deg); }} to {{ transform: rotate(4deg); }} }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <g fill="{FOAM}" fill-opacity=".05" font-family="{MONO}" font-size="12">
      <text x="24" y="30">TERMINAL CONTENEURS · QUAI NOTSAYK</text>
    </g>
    <text x="24" y="30" font-family="{MONO}" font-size="12" fill="{SAND}" font-weight="700">TERMINAL CONTENEURS · QUAI NOTSAYK</text>
    <!-- gantry crane -->
    <g stroke="{SAND}" stroke-width="6" fill="none" stroke-linecap="round">
      <line x1="{crane_x+40}" y1="{quay}" x2="{crane_x+40}" y2="34"/>
      <line x1="{crane_x+110}" y1="{quay}" x2="{crane_x+110}" y2="34"/>
      <line x1="{crane_x+40}" y1="200" x2="{crane_x+110}" y2="140" stroke-width="3"/>
      <line x1="{crane_x+110}" y1="200" x2="{crane_x+40}" y2="140" stroke-width="3"/>
      <line x1="{crane_x-180}" y1="34" x2="{crane_x+190}" y2="34" stroke-width="10"/>
    </g>
    <rect x="{crane_x+130}" y="40" width="50" height="34" fill="{SAND}"/>
    <circle cx="{crane_x+75}" cy="24" r="4" fill="#FF3B3B"><animate attributeName="opacity" values="1;.1;1" dur="1.6s" repeatCount="indefinite"/></circle>
    <g class="hook">
      <rect x="{crane_x-36}" y="30" width="32" height="12" fill="{ORANGE}"/>
      <line x1="{crane_x-20}" y1="42" x2="{crane_x-20}" y2="110" stroke="{FOAM}" stroke-width="2"/>
      <path d="M{crane_x-26},110 h12 v6 a6,6 0 1 1 -12,0 Z" fill="{FOAM}"/>
      <line x1="{crane_x-20}" y1="122" x2="{crane_x-75}" y2="134" stroke="{FOAM}" stroke-width="1.5"/>
      <line x1="{crane_x-20}" y1="122" x2="{crane_x+35}" y2="134" stroke="{FOAM}" stroke-width="1.5"/>
      {container(crane_x - 85, 134, 130, 44, SAND, "ÉCOLE D'INGÉ", "NSKU 2027-?", NAVY_1, 13)}
    </g>
    {''.join(groups)}
    <!-- quay -->
    <rect x="0" y="{quay}" width="{W}" height="{H-quay}" fill="#1A2B40"/>
    <rect x="0" y="{quay}" width="{W}" height="5" fill="{SAND}"/>
    <g fill="{NAVY_0}" opacity=".6">{''.join(f'<rect x="{x}" y="{quay+5}" width="18" height="6"/>' for x in range(0, W, 44))}</g>
    <path d="{wave_path(quay + 22, 3, 80, W, H)}" fill="{NAVY_2}">
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-80 0" dur="6s" repeatCount="indefinite"/>
    </path>
  </g>
</svg>
'''
    (OUT / "stack.svg").write_text(svg)


# ---------------------------------------------------------------- project containers
def project_card(slug, title, color, code, lines, tech, dest, status=None):
    W, H = 500, 220
    tc = NAVY_1 if color in ("#E9C46A",) else "#FFFFFF"
    ribs = "".join(
        f'<rect x="{x}" y="20" width="4" height="{H-40}" fill="#000" fill-opacity=".12"/>' for x in range(28, W - 20, 16)
    )
    desc = "".join(
        f'<text x="40" y="{108 + i*20}" font-family="{SANS}" font-size="15" fill="{tc}" fill-opacity=".95">{l}</text>'
        for i, l in enumerate(lines)
    )
    light = tc != "#FFFFFF"
    green = "#166534" if light else "#4ADE80"
    lamp = (
        f'<g class="lamp"><circle cx="{W-130}" cy="50" r="5" fill="{green}"/></g>'
        f'<text x="{W-120}" y="54" font-family="{MONO}" font-size="11" font-weight="700" fill="{green}">{status}</text>'
        if status else ""
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title} — {' '.join(lines)} ({tech})">
  <style>
    .lamp {{ animation: blink 1.8s ease-in-out infinite; }}
    @keyframes blink {{ 50% {{ opacity: .25; }} }}
    .card {{ animation: in .8s ease-out both; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateY(-14px); }} to {{ opacity: 1; transform: none; }} }}
  </style>
  <g class="card">
    <rect x="6" y="6" width="{W-12}" height="{H-12}" rx="6" fill="{color}"/>
    {ribs}
    <rect x="6" y="6" width="{W-12}" height="14" rx="4" fill="#000" fill-opacity=".28"/>
    <rect x="6" y="{H-20}" width="{W-12}" height="14" rx="4" fill="#000" fill-opacity=".32"/>
    <rect x="14" y="10" width="10" height="7" fill="{NAVY_0}" opacity=".6"/><rect x="{W-24}" y="10" width="10" height="7" fill="{NAVY_0}" opacity=".6"/>
    <rect x="14" y="{H-17}" width="10" height="7" fill="{NAVY_0}" opacity=".6"/><rect x="{W-24}" y="{H-17}" width="10" height="7" fill="{NAVY_0}" opacity=".6"/>
    <rect x="26" y="30" width="{W-52}" height="{H-60}" rx="6" fill="{'#FFFFFF' if light else NAVY_0}" fill-opacity="{'.45' if light else '.5'}"/>
    <text x="40" y="54" font-family="{MONO}" font-size="11" fill="{tc}" fill-opacity=".75" letter-spacing="1">{code}</text>
    {lamp}
    <text x="40" y="84" font-family="{SANS}" font-size="26" font-weight="800" fill="{tc}">{title}</text>
    {desc}
    <text x="40" y="{H-64}" font-family="{MONO}" font-size="12" fill="{tc}" fill-opacity=".8">{tech}</text>
    <text x="40" y="{H-38}" font-family="{MONO}" font-size="12" fill="{SAND if tc == '#FFFFFF' else NAVY_1}" font-weight="700">➜ {dest}</text>
  </g>
</svg>
'''
    (OUT / f"project-{slug}.svg").write_text(svg)


# ---------------------------------------------------------------- timeline
def parcours():
    W, H = 1200, 220
    y = 105
    steps = [
        (150, "2024", "BUT Informatique", "1ʳᵉ année · IUT du Havre", "done"),
        (450, "2025", "BUT Informatique", "2ᵉ année · IUT du Havre", "done"),
        (750, "2026", "BUT Informatique", "3ᵉ année · en alternance", "now"),
        (1050, "2027", "École d'ingénieur", "prochaine escale", "next"),
    ]
    wave = "q75,-22 150,0 t150,0 "
    done_route = f"M150,{y} " + wave * 2
    next_route = f"M750,{y} " + wave
    ports = ""
    for x, year, title, sub, state in steps:
        if state == "done":
            mark = f'<circle cx="{x}" cy="{y}" r="11" fill="{ORANGE}"/><path d="M{x-5},{y} l4,4 l7,-8" stroke="{NAVY_0}" stroke-width="3" fill="none"/>'
        elif state == "now":
            mark = (
                f'<circle cx="{x}" cy="{y}" r="11" fill="none" stroke="{ORANGE}" stroke-width="3">'
                f'<animate attributeName="r" values="11;26" dur="1.8s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="1;0" dur="1.8s" repeatCount="indefinite"/></circle>'
                f'<circle cx="{x}" cy="{y}" r="13" fill="{SAND}"/><circle cx="{x}" cy="{y}" r="5" fill="{NAVY_0}"/>'
            )
        else:
            mark = f'<circle cx="{x}" cy="{y}" r="12" fill="{NAVY_1}" stroke="{FOAM}" stroke-width="3" stroke-dasharray="5 4"/>'
        tag = {"now": "ACTUELLEMENT", "next": "OBJECTIF"}.get(state, "")
        ports += f'''
    {mark}
    <text x="{x}" y="{y-44}" text-anchor="middle" font-family="{MONO}" font-size="22" font-weight="800" fill="{ORANGE if state != 'next' else FOAM}">{year}</text>
    <text x="{x}" y="{y-26}" text-anchor="middle" font-family="{MONO}" font-size="11" font-weight="700" fill="#4ADE80" letter-spacing="2">{tag}</text>
    <text x="{x}" y="{y+46}" text-anchor="middle" font-family="{SANS}" font-size="19" font-weight="800" fill="#FFFFFF">{title}</text>
    <text x="{x}" y="{y+70}" text-anchor="middle" font-family="{SANS}" font-size="15" fill="{FOAM}" fill-opacity=".85">{sub}</text>'''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Parcours : 2024 BUT Informatique 1re année, 2025 2e année, 2026 3e année en alternance, 2027 école d'ingénieur">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{NAVY_0}"/><stop offset="1" stop-color="{NAVY_1}"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <path d="{done_route}" fill="none" stroke="{ORANGE}" stroke-width="3" stroke-opacity=".7"/>
    <path d="{next_route}" fill="none" stroke="{FOAM}" stroke-opacity=".5" stroke-width="3" stroke-dasharray="10 8">
      <animate attributeName="stroke-dashoffset" from="0" to="-36" dur="1.5s" repeatCount="indefinite"/>
    </path>
    {ports}
  </g>
</svg>
'''
    (OUT / "parcours.svg").write_text(svg)


# ---------------------------------------------------------------- divider & footer
def divider():
    W, H = 1200, 46
    line = "".join("q15,-6 30,0 t30,0 " for _ in range(22))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="presentation">
  <defs>
    <clipPath id="l"><rect x="0" y="0" width="{W/2-30}" height="{H}"/></clipPath>
    <clipPath id="r"><rect x="{W/2+30}" y="0" width="{W/2-30}" height="{H}"/></clipPath>
  </defs>
  <g clip-path="url(#l)">
    <path d="M-60,26 {line}" fill="none" stroke="{NAVY_3}" stroke-width="2.5" stroke-linecap="round">
      <animateTransform attributeName="transform" type="translate" from="0 0" to="60 0" dur="4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g clip-path="url(#r)">
    <path d="M{W/2-30},26 {line}" fill="none" stroke="{NAVY_3}" stroke-width="2.5" stroke-linecap="round">
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-60 0" dur="4s" repeatCount="indefinite"/>
    </path>
  </g>
  <g>
    <animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 0" dur="2.4s" repeatCount="indefinite"/>
    <circle cx="{W/2}" cy="24" r="16" fill="none" stroke="{ORANGE}" stroke-width="5"/>
    <circle cx="{W/2}" cy="24" r="16" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-dasharray="12.57 12.57"/>
  </g>
</svg>
'''
    (OUT / "divider.svg").write_text(svg)


def footer():
    W, H = 1200, 170
    sea = waves(40, W, H, [
        (0, 6, 200, NAVY_3, .45, 10),
        (20, 7, 240, NAVY_2, .8, 8),
        (45, 8, 300, NAVY_1, 1, 12),
    ])
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Bon vent !">
  <defs><clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>
  <g clip-path="url(#frame)">
    {sea}
    <text x="{W/2}" y="135" text-anchor="middle" font-family="{SANS}" font-size="28" font-weight="800" fill="#FFFFFF" letter-spacing="4">BON VENT !</text>
  </g>
</svg>
'''
    (OUT / "footer.svg").write_text(svg)


if __name__ == "__main__" and sys.argv[1:2] == ["--sky"]:
    # Only the header, for the current hour in Le Havre (used by .github/workflows/sky.yml).
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("Europe/Paris"))
    sky_dir = Path(sys.argv[2])
    sky_dir.mkdir(parents=True, exist_ok=True)
    header(now.hour + now.minute / 60, sky_dir)
    print(f"header for {now:%H:%M} written to {sky_dir}")
elif __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    header()
    stack()
    parcours()
    project_card("pepiterush", "Pépite Rush", ORANGE, "NSKU 300001-0 · JEU MULTIJOUEUR",
                 ["Jeu de cartes « stop ou encore » en ligne,", "de 2 à 6 joueurs en temps réel, bots inclus."],
                 "TypeScript · React · Fastify · WebSocket", "github.com/NotSayk/goldmine")
    project_card("mpm", "MPM Planner", "#E63946", "NSKU 300002-1 · APPLICATION JAVA",
                 ["Planification de projet par la méthode MPM :", "dates au plus tôt / tard, marges, chemin critique."],
                 "Java · Swing · POO", "github.com/NotSayk/MPM-Planner")
    project_card("tontube", "TonTube", "#2A9D8F", "NSKU 300003-2 · SAÉ 2.03",
                 ["Site de vidéo à la demande avec comptes", "utilisateurs, conteneurisé avec Docker."],
                 "HTML · CSS · JavaScript · Docker · Apache", "github.com/NotSayk/TonTube")
    project_card("memotools", "MemoTools", "#457B9D", "NSKU 300004-3 · E-COMMERCE",
                 ["Boutique d'outils pédagogiques imprimés en 3D", "pour apprendre les structures de données."],
                 "HTML · CSS · JavaScript · JSON", "github.com/NotSayk/SchemaMemoire")
    project_card("portfolio", "Terminal Portfolio", "#6C5CE7", "NSKU 300005-4 · GITHUB PAGES",
                 ["Mon portfolio façon terminal Linux : commandes,", "autocomplétion et mini-jeu Snake intégré."],
                 "HTML · CSS · JavaScript", "notsayk.github.io/portfolio", "EN LIGNE")
    project_card("biolink", "Bio Link Page", "#3D5A80", "NSKU 300006-5 · GITHUB PAGES",
                 ["Ma page de liens : intro animée, thème", "clair / sombre et lecteur de musique."],
                 "HTML · CSS · JavaScript", "notsayk.github.io/bio-link-page", "EN LIGNE")
    project_card("minigames", "MiniGames Sayk", "#E9C46A", "NSKU 400001-0 · STUDIO",
                 ["Ma plateforme de mini-jeux en ligne,", "hébergée sur mon propre VPS."],
                 "Docker · VPS", "sayk.fr", "EN LIGNE")
    project_card("stickyclaude", "StickyClaude", "#E63946", "NSKU 400002-1 · JEU DE COMBAT",
                 ["Combat de stickmen dans le navigateur,", "de 2 à 8 joueurs, style « encre et carnet »."],
                 "TypeScript · PixiJS · Preact · WebSocket", "stickyclaude.sayk.fr", "EN LIGNE")
    divider()
    footer()
    print("ok", sorted(p.name for p in OUT.iterdir()))
