#!/usr/bin/env python3
"""
Generates every image of the GitHub profile README from the design tokens of
thibautplatet.com (assets/css/tokens.css, orrery.css): colours, fonts, the orrery.

    pip install fonttools brotli
    python _build/gen.py            # run from the root of the ThibPltt/ThibPltt repository

Edit the CONTENT section below, run the script again, commit assets/ and README.md.
Fonts (SIL Open Font License, see fonts/OFL-*.txt) are subset and embedded in each SVG,
so GitHub renders them exactly, with no external request.
"""
import base64
import io
import math
import os
import random
import sys
from collections import defaultdict
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
KITS = os.path.join(ASSETS, "repos")  # cards shown at the top of the project repositories

# ---------------------------------------------------------------- design tokens (tokens.css)
LIGHT = dict(
    name="light", card="#ffffff", card_border="#dcdef6", surface="#ecedfd", text="#1f2033",
    muted="#6b6e80", accent="#3b3fd9", accent_contrast="#ffffff", highlight="#8e1b4f",
    border="#b9bbe6", tag_bg="#e6e7fb", tag_text="#3b3fd9",
)
DARK = dict(
    name="dark", card="#14172c", card_border="#2d315a", surface="#171a33", text="#eceefb",
    muted="#a9acc9", accent="#a3a7ff", accent_contrast="#0d0e1a", highlight="#f08db8",
    border="#3a3e6a", tag_bg="#23274d", tag_text="#c1c4ff",
)
# the orrery section of the site is a dark space scene in both themes (orrery.css)
SPACE = dict(bg="#04050d", text="#f1f2fb", muted="#b9bbe6", accent="#c9cbf5",
             highlight="#f0a3c4", border="#7479c2", plate="#111329", plate_edge="#5a5fa3",
             under="#06070f", under_edge="#2a2e55", label_bg="rgba(4,5,13,0.78)")
SITE_PINK, SITE_LAVENDER = "#f08db8", "#a3a7ff"

FONT_FILES = {
    ("Poppins", 500): "poppins-latin-500-normal.woff2",
    ("Poppins", 600): "poppins-latin-600-normal.woff2",
    ("TP Text", 400): "lato-latin-400-normal.woff2",
    ("TP Text", 700): "lato-latin-700-normal.woff2",
    ("Space Mono", 400): "space-mono-latin-400-normal.woff2",
    ("Space Mono", 700): "space-mono-latin-700-normal.woff2",
}
FALLBACK = {
    "Poppins": "'Poppins', 'Segoe UI', system-ui, sans-serif",
    "TP Text": "'TP Text', 'Segoe UI', system-ui, sans-serif",
    "Space Mono": "'Space Mono', Consolas, ui-monospace, monospace",
}
HEAD, BODY, MONO = "Poppins", "TP Text", "Space Mono"

# ---------------------------------------------------------------- content
SITE = "https://thibautplatet.com/en/"
LINKS = {
    "cv": "https://thibautplatet.com/assets/cv/CV_Thibaut_Platet_EN.pdf",
    "portfolio": SITE,
    "linkedin": "https://www.linkedin.com/in/thibaut-platet-547b03275/",
    "email": "mailto:contact@thibautplatet.com",
}
BANNER = dict(
    name="Thibaut Platet",
    title="XR & Simulation Software Engineer",
    stack="Unreal Engine 5 / C++ · Unity / C# · VR / AR · AI",
    avail_strong="Available immediately",
    avail_rest=" for permanent or fixed-term roles.",
    avail_line2="Based in Paris, open to relocation in France and abroad.",
    url="thibautplatet.com",
)
# orrery: same planets, order, sizes and starting angles as the site (inner = oldest)
ORRERY = [
    # label,          kind,    orbit rx, radius, angle0, period (s)
    ("Bilan Carbone", "rock", 76, 11.5, 252.6, 34),
    ("ENEDIS", "rust", 116, 13.0, 358.2, 48),
    ("SOLAS", "ice", 156, 16.0, 278.0, 64),
    ("TerraPolis", "terra", 196, 16.0, 51.0, 84),
    ("CEA-List", "gas", 238, 19.5, 90.0, 112),
]
SELECTED = "CEA-List"

PROJECTS = [
    dict(
        slug="cea-list", kind="gas", title="CEA-List · VR assembly training",
        dates="Mar 2026 – Aug 2026",
        meta="R&D engineering intern · Interactive Simulation Laboratory (LSI), Palaiseau",
        summary="Unreal Engine 5 C++ visual guides for a VR industrial-assembly training app on the "
                "XDE physics engine: part ghosts replay each mechanical joint's degrees of freedom.",
        result="Visual aids, VR interaction and module documentation shipped to the lab.",
        tags=["C++", "Unreal Engine 5", "VR", "XDE physics", "Blueprints", "Agile"],
        cta="Case study", href="https://thibautplatet.com/en/projects/cea-list.html",
        alt="CEA-List, Mar 2026 to Aug 2026: Unreal Engine 5 C++ visual guides for a VR "
            "industrial-assembly training application on the XDE physics engine. Proprietary code, "
            "case study on the portfolio.",
    ),
    dict(
        slug="terrapolis", kind="terra", title="TerraPolis", dates="2025 – 2026",
        meta="augmented reality · project lead, team of 3 · ENSIM",
        summary="AR city simulation (pollution, floods) driven by Deep Reinforcement Learning: I led "
                "the team and built most of the AI (CNN, curriculum training in PyTorch).",
        result="Over 1,000 games, the AI scores 4.75× a random strategy on average.",
        tags=["AR", "Deep Reinforcement Learning", "Unity", "Python"],
        cta="Repository", href="https://github.com/ThibPltt/Terrapolis",
        alt="TerraPolis, 2025 to 2026: AR city simulation driven by Deep Reinforcement Learning. "
            "Python engine and Unity AR client.",
    ),
    dict(
        slug="solas", kind="ice", title="SOLAS", dates="2024 – 2025",
        meta="virtual reality serious game · project lead, team of 4 · ENSIM",
        summary="Teaches the solar system to young players: a planet-to-planet journey with "
                "landings on the Moon, Mars and Earth, text and voice-over at each stop.",
        result="Complete game tested on Meta Quest 3; early version shown at ENSIM open days.",
        tags=["VR", "Unity", "C#", "Blender"],
        cta="Repository", href="https://github.com/ThibPltt/SOLAS",
        alt="SOLAS, 2024 to 2025: VR serious game about the solar system, Unity and C#, "
            "tested on Meta Quest 3.",
    ),
    dict(
        slug="the-undead-clock", kind="lava", title="The Undead Clock", dates="2025 – 2026",
        meta="survival mini-game · solo project · ENSIM",
        summary="Unreal Engine 5 survival game built entirely in Blueprints: escape a zombie-infested "
                "industrial complex before time or health runs out.",
        result="Playable game: nine waves, five doors and a final keypad puzzle.",
        tags=["Unreal Engine 5", "Blueprints"],
        cta="Repository", href="https://github.com/ThibPltt/The-Undead-Clock",
        alt="The Undead Clock, 2025 to 2026: Unreal Engine 5 survival game built in Blueprints.",
    ),
    dict(
        slug="mystic-minigolf", kind="ocean", title="Mystic Minigolf", dates="2024 – 2025",
        meta="virtual reality · built as a pair · ENSIM",
        summary="VR minigolf on an island of ancient temples, where an animated mascot "
                "demonstrates the swing before you strike the ball, club in hand.",
        result="Two scenes and three courses, all playable to the end.",
        tags=["VR", "Unity", "C#", "Blender"],
        cta="Repository", href="https://github.com/ThibPltt/Mystic_MiniGolf_VR",
        alt="Mystic Minigolf, 2024 to 2025: VR minigolf on a temple island, Unity and C#.",
    ),
]
# extra cards used only at the top of project repositories
KIT_CARDS = {
    "Shepherding": dict(
        slug="shepherding", kind="pasture", title="Shepherding", dates="2026",
        meta="multi-agent reinforcement learning · solo course project · ENSIM / Le Mans Université",
        summary="A 2D continuous shepherding environment where an RL agent learns to herd sheep into "
                "a goal area, around obstacles, through a curriculum of three levels.",
        result="PPO, DQN, SAC and TD3 compared with scripted baselines over 500 test episodes.",
        tags=["Python", "PyTorch", "Stable-Baselines3", "Gym", "Pygame"],
        cta="", href="", alt="Shepherding: multi-agent reinforcement learning.",
    ),
}
KIT_CARDS.update({
    "ARmageddon": dict(
        slug="armageddon", kind="desert", title="ARmageddon", dates="2024 – 2025",
        meta="augmented reality · solo project · ENSIM",
        summary="AR battle sandbox for Android: generate a terrain on the real floor, sculpt its "
                "relief, then place troops and buildings on it.",
        result="Terrain, relief editing, nature, buildings and soldiers working on Android.",
        tags=["AR", "Unity", "C#", "AR Foundation"],
        cta="", href="", alt="ARmageddon: augmented reality battle sandbox.",
    ),
    "Vert-le-chemin": dict(
        slug="vert-le-chemin", kind="forest", title="Vert le Chemin", dates="2024 – 2025",
        meta="mobile app · course project · ENSIM",
        summary="Android app that estimates the CO2 emissions of daily trips from ADEME data and suggests "
                "greener means of transport.",
        result="Specification, mock-ups and a Kotlin prototype with routing and navigation.",
        tags=["Android", "Kotlin", "Jetpack Compose", "Firebase"],
        cta="", href="", alt="Vert le Chemin: Android app estimating the CO2 of daily trips.",
    ),
})
KIT_CARDS.update({
    "ActiveLearning": dict(
        slug="activelearning", kind="rock", title="Active Learning · gaze tracking", dates="2026",
        meta="deep learning · course project · ENSIM / Le Mans Université",
        summary="Predicts where a person looks on screen from a webcam image (ResNet-18), and uses "
                "active learning to choose which new images are worth labelling.",
        result="With half of the new domain labelled, the mixed strategy reaches 67 px mean error, against 80 px at random.",
        tags=["Python", "PyTorch", "ResNet-18", "Active learning"],
        cta="", href="", alt="Active Learning: webcam gaze tracking with ResNet-18 and active learning.",
    ),
})

KIT_REPOS = {"The-Undead-Clock": "the-undead-clock", "Mystic_MiniGolf_VR": "mystic-minigolf",
             "Terrapolis": "terrapolis", "Shepherding": "shepherding", "ARmageddon": "armageddon",
             "Vert-le-chemin": "vert-le-chemin", "SOLAS": "solas", "ActiveLearning": "activelearning"}

SKILLS = [
    ("Engines & XR", ["Unreal Engine 5", "Blueprints", "Unity", "VR", "AR",
                      "Physics simulation (XDE)", "Blender"]),
    ("Headsets", ["Meta Quest 3", "PICO 4 Ultra Enterprise", "HTC Vive Focus 3"]),
    ("Languages", ["C++", "C#", "C", "Python", "Java", "Kotlin"]),
    ("Tools & AI", ["Git / GitHub", "Deep Reinforcement Learning", "Machine & Active Learning",
                    "Power BI", "QGIS", "ArcGIS"]),
    ("Methods", ["HCI / UI-UX design", "Agile / Scrum / Kanban", "Project management",
                 "Technical documentation"]),
]
BACKGROUND = [
    ("EXPERIENCE", [
        ("R&D Engineering Intern, Virtual Reality & Physics Simulation", "Mar 2026 – Aug 2026",
         "CEA-List, Interactive Simulation Laboratory (LSI), Palaiseau", "final-year internship"),
        ("GIS Intern", "Jun 2024 – Aug 2024",
         "ENEDIS (EDF Group), Languedoc-Roussillon Mapping Department, Montpellier", "QGIS, ArcGIS, Python, Power BI"),
    ]),
    ("EDUCATION", [
        ("Master’s-level Engineering Degree in Computer Science, HCI specialization", "2023 – 2026",
         "ENSIM, Le Mans", "Interaction Personnes-Systèmes"),
        ("Bachelor’s Degree in Geography and Spatial Planning", "2023 – 2024",
         "Le Mans University", "dual-degree program"),
        ("Preparatory Classes (CPGE B/L) in literature and social sciences", "2021 – 2023",
         "Lycée Henri IV, Béziers", ""),
    ]),
]
HEADERS = {"profile": "Profile", "work": "Featured work", "more": "More on GitHub",
           "skills": "Skills", "background": "Background"}
BUTTONS = [("cv", "CV (PDF)", True), ("portfolio", "Portfolio", False),
           ("linkedin", "LinkedIn", False), ("email", "contact@thibautplatet.com", False)]


# ---------------------------------------------------------------- fonts
class Fonts:
    def __init__(self):
        self.tt, self.cmap, self.hmtx, self.upm = {}, {}, {}, {}
        for key, fn in FONT_FILES.items():
            f = TTFont(os.path.join(HERE, "fonts", fn))
            self.tt[key] = os.path.join(HERE, "fonts", fn)
            self.cmap[key] = f.getBestCmap()
            self.hmtx[key] = f["hmtx"].metrics
            self.upm[key] = f["head"].unitsPerEm

    def width(self, s, key, size, ls=0.0):
        cmap, hmtx = self.cmap[key], self.hmtx[key]
        w = 0
        for ch in s:
            g = cmap.get(ord(ch))
            if g is None:
                raise ValueError(f"glyph {ch!r} (U+{ord(ch):04X}) missing in {key}")
            w += hmtx[g][0]
        return w * size / self.upm[key] + ls * size * max(len(s) - 1, 0)

    def face(self, key, chars):
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt"]
        font = TTFont(self.tt[key], recalcTimestamp=False)
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(chars | {" "})))
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        fam, weight = key
        return (f"@font-face{{font-family:'{fam}';font-weight:{weight};font-style:normal;"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


FONTS = Fonts()


def wrap(text, key, size, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if FONTS.width(t, key, size) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- svg builder
class SVG:
    def __init__(self, w, h, title, desc=""):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.defs, self.body, self.css = [], [], []
        self.used = defaultdict(set)
        self._ids = set()

    def uid(self, base):
        i, n = 0, base
        while n in self._ids:
            i += 1
            n = f"{base}{i}"
        self._ids.add(n)
        return n

    def t(self, x, y, s, fam, weight, size, fill, anchor="start", ls=0.0, extra=""):
        self.used[(fam, weight)].update(s)
        ls_attr = f' letter-spacing="{ls * size:.2f}"' if ls else ""
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FALLBACK[fam]}" font-weight="{weight}" '
                f'font-size="{size}" fill="{fill}" text-anchor="{anchor}"{ls_attr}{extra}>'
                f"{escape(s)}</text>")

    def span(self, s, fam, weight, fill):
        self.used[(fam, weight)].update(s)
        return (f'<tspan font-family="{FALLBACK[fam]}" font-weight="{weight}" fill="{fill}">'
                f"{escape(s)}</tspan>")

    def add(self, *parts):
        self.body.extend(parts)

    def render(self, width_attr=True):
        faces = "".join(FONTS.face(k, v) for k, v in sorted(self.used.items()))
        css = faces + "".join(self.css)
        size = f' width="{self.w}" height="{self.h}"' if width_attr else ""
        desc = f"<desc>{escape(self.desc)}</desc>" if self.desc else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}"{size} '
                f'role="img" aria-labelledby="t"><title id="t">{escape(self.title)}</title>{desc}'
                f"<style>{css}</style><defs>{''.join(self.defs)}</defs>{''.join(self.body)}</svg>")


def stars(svg, x, y, w, h, n, seed, twinkle=0):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        sx, sy = x + rnd.random() * w, y + rnd.random() * h
        r = rnd.choice([0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5]) if rnd.random() < 0.9 else 1.9
        o = 0.25 + rnd.random() * 0.7
        if i < twinkle:
            d, dl = 2.5 + rnd.random() * 4, rnd.random() * 5
            out.append(f'<circle class="tw" cx="{sx:.1f}" cy="{sy:.1f}" r="{r}" fill="#fff" '
                       f'opacity="{o:.2f}" style="animation-duration:{d:.1f}s;animation-delay:-{dl:.1f}s"/>')
        else:
            out.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r}" fill="#fff" opacity="{o:.2f}"/>')
    return "".join(out)


# ---------------------------------------------------------------- planets (unit radius, scaled)
def planet_defs(svg, kinds):
    """Gradients shared by every planet of a kind; planets are drawn at radius 1 then scaled."""
    d = svg.defs
    d.append('<clipPath id="pc"><circle r="1"/></clipPath>')
    d.append('<radialGradient id="shade" cx="0.36" cy="0.3" r="0.78">'
             '<stop offset="0" stop-color="#fff" stop-opacity="0.22"/>'
             '<stop offset="0.42" stop-color="#fff" stop-opacity="0"/>'
             '<stop offset="0.78" stop-color="#02030a" stop-opacity="0.45"/>'
             '<stop offset="1" stop-color="#02030a" stop-opacity="0.82"/></radialGradient>')
    grads = {
        "rock": [("0", "#c4c4cf"), ("0.6", "#8b8b97"), ("1", "#5e5e6b")],
        "rust": [("0", "#f0a070"), ("0.55", "#c8653a"), ("1", "#86391f")],
        "ice": [("0", "#f4fbff"), ("0.55", "#bcdcf2"), ("1", "#7fa9cf")],
        "terra": [("0", "#5aa6e6"), ("0.6", "#2f6fb5"), ("1", "#1a4683")],
        "lava": [("0", "#4a1f1c"), ("0.6", "#2a1214"), ("1", "#140909")],
        "ocean": [("0", "#7ee0dc"), ("0.55", "#36aeb9"), ("1", "#1a6a86")],
        "pasture": [("0", "#c9e27d"), ("0.55", "#86b84a"), ("1", "#4f7d2b")],
        "desert": [("0", "#f6d58e"), ("0.55", "#d39a4e"), ("1", "#8a5224")],
        "forest": [("0", "#8fd98a"), ("0.55", "#3f9a55"), ("1", "#1d5a33")],
    }
    for k in sorted(kinds):
        if k in grads:
            stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in grads[k])
            d.append(f'<radialGradient id="g-{k}" cx="0.4" cy="0.35" r="0.75">{stops}</radialGradient>')
    if "gas" in kinds:
        bands = ["#d8cdf3", "#a796dc", "#c4b4ec", "#8676c6", "#e4d7f5", "#9a88d2",
                 "#b9a7e6", "#7d6cbf", "#d2c3f0", "#a08fd8"]
        n = len(bands)
        stops = "".join(f'<stop offset="{i / (n - 1):.3f}" stop-color="{c}"/>' for i, c in enumerate(bands))
        d.append(f'<linearGradient id="g-gas" x1="0" y1="0" x2="0.18" y2="1">{stops}</linearGradient>')
        d.append('<linearGradient id="g-ring" x1="0" y1="0" x2="1" y2="0">'
                 '<stop offset="0" stop-color="#cfc8f2" stop-opacity="0.35"/>'
                 '<stop offset="0.5" stop-color="#f1edff" stop-opacity="0.95"/>'
                 '<stop offset="1" stop-color="#cfc8f2" stop-opacity="0.35"/></linearGradient>')
    if "lava" in kinds:
        d.append('<radialGradient id="g-lavaglow" r="0.5"><stop offset="0.55" stop-color="#ff5a36" '
                 'stop-opacity="0.35"/><stop offset="1" stop-color="#ff5a36" stop-opacity="0"/></radialGradient>')


def planet(kind, r, ring_front=True):
    """Return markup of a planet of radius r centred on (0,0)."""
    body = []
    if kind == "gas":
        back = '<path d="M -2 0 A 2 0.5 0 0 1 2 0" fill="none" stroke="url(#g-ring)" stroke-width="0.16" transform="rotate(-14)"/>'
        front = '<path d="M -2 0 A 2 0.5 0 0 0 2 0" fill="none" stroke="url(#g-ring)" stroke-width="0.16" transform="rotate(-14)"/>'
        body.append(back)
        body.append('<circle r="1" fill="url(#g-gas)" transform="rotate(-14)"/>')
    elif kind == "lava":
        body.append('<circle r="1.55" fill="url(#g-lavaglow)"/>')
        body.append('<circle r="1" fill="url(#g-lava)"/>')
    else:
        body.append(f'<circle r="1" fill="url(#g-{kind})"/>')
    deco = []
    if kind == "rock":
        for (x, y, cr) in [(-0.35, -0.2, 0.22), (0.3, 0.35, 0.16), (0.42, -0.42, 0.11), (-0.1, 0.55, 0.12)]:
            deco.append(f'<circle cx="{x}" cy="{y}" r="{cr}" fill="#4f4f5c" opacity="0.55"/>'
                        f'<circle cx="{x - 0.03}" cy="{y - 0.03}" r="{cr * 0.8}" fill="none" stroke="#e2e2ea" stroke-width="0.03" opacity="0.4"/>')
    elif kind == "rust":
        deco.append('<path d="M-1 -0.1 C -0.5 -0.35 0 0.05 0.4 -0.15 S 1 -0.1 1 0.05 L 1 0.25 C 0.5 0.2 0 0.45 -0.6 0.2 Z" fill="#7a2f1a" opacity="0.5"/>')
        deco.append('<circle cx="0.35" cy="0.45" r="0.13" fill="#6c2a18" opacity="0.6"/>')
        deco.append('<ellipse cx="0" cy="-0.93" rx="0.35" ry="0.12" fill="#fbe9de" opacity="0.8"/>')
    elif kind == "ice":
        deco.append('<path d="M-1 -0.2 C -0.4 -0.05 0.4 -0.3 1 -0.15" stroke="#ffffff" stroke-width="0.12" fill="none" opacity="0.45"/>')
        deco.append('<path d="M-1 0.3 C -0.3 0.45 0.4 0.2 1 0.35" stroke="#6d98c2" stroke-width="0.1" fill="none" opacity="0.45"/>')
        deco.append('<ellipse cx="0" cy="-0.9" rx="0.5" ry="0.2" fill="#ffffff" opacity="0.9"/>')
    elif kind == "terra":
        deco.append('<path d="M-0.75 -0.55 C -0.4 -0.75 -0.05 -0.6 -0.1 -0.3 C -0.15 0 -0.5 0.05 -0.55 0.35 C -0.7 0.5 -0.95 0.2 -0.95 -0.1 Z" fill="#4f9f5c"/>')
        deco.append('<path d="M0.2 -0.1 C 0.45 -0.35 0.85 -0.25 0.9 0.05 C 0.95 0.4 0.6 0.7 0.3 0.6 C 0.1 0.5 0.0 0.15 0.2 -0.1 Z" fill="#3f8c4f"/>')
        deco.append('<path d="M0.3 0.15 C 0.45 0.05 0.6 0.15 0.55 0.3 C 0.45 0.4 0.3 0.3 0.3 0.15 Z" fill="#c9b27a" opacity="0.9"/>')
        deco.append('<path d="M-1 -0.05 C -0.5 0.1 0 -0.12 0.6 -0.5" stroke="#fff" stroke-width="0.09" fill="none" opacity="0.65" stroke-linecap="round"/>')
        deco.append('<path d="M-0.4 0.75 C 0 0.6 0.4 0.85 0.9 0.6" stroke="#fff" stroke-width="0.08" fill="none" opacity="0.55" stroke-linecap="round"/>')
    elif kind == "lava":
        cracks = ["M-0.8 -0.3 L -0.35 -0.1 L -0.1 -0.45 L 0.3 -0.3 L 0.7 -0.55",
                  "M-0.35 -0.1 L -0.2 0.3 L 0.25 0.35 L 0.55 0.1 L 0.9 0.2",
                  "M-0.2 0.3 L -0.55 0.65", "M0.25 0.35 L 0.35 0.8", "M0.3 -0.3 L 0.55 0.1"]
        for c in cracks:
            deco.append(f'<path d="{c}" stroke="#ff5a36" stroke-width="0.16" fill="none" opacity="0.35" stroke-linejoin="round"/>')
            deco.append(f'<path d="{c}" stroke="#ffb45c" stroke-width="0.05" fill="none" stroke-linejoin="round"/>')
    elif kind == "ocean":
        deco.append('<path d="M-0.3 -0.05 C -0.15 -0.3 0.25 -0.3 0.35 -0.05 C 0.42 0.15 0.1 0.3 -0.12 0.22 C -0.3 0.16 -0.38 0.05 -0.3 -0.05 Z" fill="#e8d6a2"/>')
        deco.append('<path d="M-0.22 -0.05 C -0.1 -0.22 0.18 -0.22 0.26 -0.05 C 0.3 0.08 0.08 0.18 -0.08 0.14 C -0.2 0.1 -0.27 0.03 -0.22 -0.05 Z" fill="#4aa866"/>')
        deco.append('<path d="M-0.02 -0.14 L 0.05 -0.28 L 0.12 -0.14 Z" fill="#c0563f"/>')
        deco.append('<circle cx="0.55" cy="0.45" r="0.07" fill="#e8d6a2"/><circle cx="-0.6" cy="0.4" r="0.05" fill="#e8d6a2"/>')
        deco.append('<path d="M-0.9 -0.45 C -0.4 -0.6 0.2 -0.5 0.8 -0.62" stroke="#fff" stroke-width="0.08" fill="none" opacity="0.6" stroke-linecap="round"/>')
    elif kind == "desert":
        for (y, w, o) in [(-0.45, 0.1, 0.5), (-0.1, 0.12, 0.45), (0.25, 0.1, 0.5), (0.6, 0.09, 0.4)]:
            deco.append(f'<path d="M-1 {y} C -0.5 {y - 0.12} 0 {y + 0.1} 1 {y - 0.05}" stroke="#7a4520" stroke-width="{w}" fill="none" opacity="{o}"/>')
        deco.append('<circle cx="0.35" cy="-0.2" r="0.12" fill="#6e3d1c" opacity="0.55"/>')
    elif kind == "forest":
        for (x, y, cr) in [(-0.45, -0.35, 0.28), (0.1, -0.5, 0.22), (0.4, 0.05, 0.3), (-0.2, 0.3, 0.26), (0.15, 0.6, 0.18)]:
            deco.append(f'<circle cx="{x}" cy="{y}" r="{cr}" fill="#1f6b35" opacity="0.75"/>')
        deco.append('<path d="M-1 0.05 C -0.5 0.2 0 -0.05 1 0.15" stroke="#6fc3e8" stroke-width="0.08" fill="none" opacity="0.8"/>')
    elif kind == "pasture":
        deco.append('<path d="M-1 0.25 C -0.4 0.05 0.3 0.4 1 0.15 L 1 1 L -1 1 Z" fill="#5f9637" opacity="0.6"/>')
        for (x, y) in [(-0.3, -0.25), (0.05, -0.38), (0.3, -0.15), (-0.05, -0.05), (0.45, 0.4)]:
            deco.append(f'<ellipse cx="{x}" cy="{y}" rx="0.09" ry="0.065" fill="#ffffff"/>')
        deco.append('<circle cx="-0.45" cy="0.3" r="0.08" fill="#2c2a2a"/>')
    inner = "".join(body) + f'<g clip-path="url(#pc)">{"".join(deco)}</g><circle r="1" fill="url(#shade)"/>'
    if kind == "gas" and ring_front:
        inner += ('<path d="M -2 0 A 2 0.5 0 0 0 2 0" fill="none" stroke="url(#g-ring)" '
                  'stroke-width="0.16" transform="rotate(-14)"/>')
    if kind == "terra":
        inner += '<circle r="1.04" fill="none" stroke="#8cc8ff" stroke-opacity="0.35" stroke-width="0.06"/>'
    return f'<g transform="scale({r})">{inner}</g>'


def arrow(x, y, color, size=10, w=1.8):
    s = size
    return (f'<path d="M {x:.1f} {y + s:.1f} L {x + s:.1f} {y:.1f} M {x + s * 0.3:.1f} {y:.1f} '
            f'L {x + s:.1f} {y:.1f} L {x + s:.1f} {y + s * 0.7:.1f}" fill="none" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


# ---------------------------------------------------------------- banner
def banner():
    W, H = 1280, 440
    svg = SVG(W, H, f"{BANNER['name']} — {BANNER['title']}",
              f"{BANNER['stack']}. {BANNER['avail_strong']}{BANNER['avail_rest']} {BANNER['avail_line2']} "
              "An animated orrery shows experience and projects as planets: "
              + ", ".join(p[0] for p in ORRERY) + ".")
    planet_defs(svg, {p[1] for p in ORRERY})
    svg.defs.append(f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>')
    svg.defs.append('<radialGradient id="glowb" r="0.5"><stop offset="0" stop-color="#787eff" stop-opacity="0.22"/>'
                    '<stop offset="1" stop-color="#787eff" stop-opacity="0"/></radialGradient>')
    svg.defs.append('<radialGradient id="glowp" r="0.5"><stop offset="0" stop-color="#f08db8" stop-opacity="0.16"/>'
                    '<stop offset="1" stop-color="#f08db8" stop-opacity="0"/></radialGradient>')
    svg.defs.append('<radialGradient id="plate" r="0.5"><stop offset="0" stop-color="#1b1e3c"/>'
                    '<stop offset="1" stop-color="#101228"/></radialGradient>')
    svg.defs.append('<radialGradient id="base" r="0.5"><stop offset="0" stop-color="#2a2e58"/>'
                    '<stop offset="0.6" stop-color="#101228"/><stop offset="1" stop-color="#1b1e3c"/></radialGradient>')
    svg.defs.append('<linearGradient id="col" x1="0" x2="1"><stop offset="0" stop-color="#151834"/>'
                    '<stop offset="0.45" stop-color="#3a3f74"/><stop offset="1" stop-color="#121430"/></linearGradient>')
    svg.defs.append('<radialGradient id="sun" cx="0.42" cy="0.38" r="0.62"><stop offset="0" stop-color="#fff3dc"/>'
                    '<stop offset="0.35" stop-color="#ffc39a"/><stop offset="0.72" stop-color="#f4878d"/>'
                    '<stop offset="1" stop-color="#d44b78"/></radialGradient>')
    svg.defs.append('<radialGradient id="sunglow" r="0.5"><stop offset="0.3" stop-color="#f08296" stop-opacity="0.5"/>'
                    '<stop offset="1" stop-color="#f08296" stop-opacity="0"/></radialGradient>')
    svg.css.append(".tw{animation:tw 4s ease-in-out infinite}"
                   "@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}")

    g = ['<g clip-path="url(#frame)">', f'<rect width="{W}" height="{H}" fill="{SPACE["bg"]}"/>',
         '<ellipse cx="260" cy="70" rx="560" ry="360" fill="url(#glowb)"/>',
         '<ellipse cx="1120" cy="430" rx="520" ry="300" fill="url(#glowp)"/>',
         stars(svg, 0, 0, W, H, 190, 7, twinkle=34),
         f'<rect width="10" height="{H}" fill="{SITE_LAVENDER}"/>']

    # text block (hero of the site)
    x = 76
    g.append(svg.t(x, 172, BANNER["name"], HEAD, 600, 66, SITE_PINK))
    g.append(svg.t(x, 222, BANNER["title"], HEAD, 500, 31, SITE_LAVENDER))
    g.append(svg.t(x, 266, BANNER["stack"], MONO, 400, 18.5, SPACE["accent"]))
    line1 = (f'<text x="{x}" y="314" font-size="20.5">'
             + svg.span(BANNER["avail_strong"], BODY, 700, SITE_PINK)
             + svg.span(BANNER["avail_rest"], BODY, 400, "#eceefb") + "</text>")
    g.append(line1)
    g.append(svg.t(x, 342, BANNER["avail_line2"], BODY, 400, 20.5, "#eceefb"))
    uw = FONTS.width(BANNER["url"], (MONO, 400), 17) + 56
    g.append(f'<rect x="{x}" y="364" width="{uw:.1f}" height="42" rx="8" fill="rgba(4,5,13,0.6)" '
             f'stroke="{SPACE["border"]}" stroke-width="1.5"/>')
    g.append(svg.t(x + 16, 391, BANNER["url"], MONO, 400, 17, SPACE["text"]))
    g.append(arrow(x + uw - 30, 380, SITE_PINK, 10, 2.2))

    # orrery
    cx, cy, k = 996, 196, 0.33
    prx = 262
    g.append(f'<rect x="{cx - 20}" y="{cy + 60}" width="40" height="{388 - cy - 60}" fill="url(#col)"/>')
    g.append(f'<ellipse cx="{cx}" cy="392" rx="96" ry="22" fill="{SPACE["under"]}" stroke="{SPACE["under_edge"]}" stroke-width="2"/>')
    g.append(f'<ellipse cx="{cx}" cy="386" rx="96" ry="22" fill="url(#base)" stroke="{SPACE["plate_edge"]}" stroke-width="2.5"/>')
    g.append(f'<ellipse cx="{cx}" cy="{cy + 14}" rx="{prx}" ry="{prx * k:.1f}" fill="{SPACE["under"]}" stroke="{SPACE["under_edge"]}" stroke-width="2"/>')
    g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{prx}" ry="{prx * k:.1f}" fill="url(#plate)" stroke="{SPACE["plate_edge"]}" stroke-width="3"/>')
    for rr in range(14, prx - 6, 9):
        g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rr}" ry="{rr * k:.1f}" fill="none" stroke="#fff" stroke-opacity="0.035"/>')
    for (_, _, orx, *_rest) in ORRERY:
        g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{orx}" ry="{orx * k:.1f}" fill="none" stroke="{SPACE["border"]}" '
                 'stroke-opacity="0.7" stroke-width="2" stroke-dasharray="0.1 7" stroke-linecap="round"/>')

    def label_markup(name, r, selected):
        lw = FONTS.width(name, (MONO, 400), 12.5) + 14
        col = SPACE["highlight"] if selected else SPACE["text"]
        y = -r - 12 - (8 if name == "CEA-List" else 0)
        return (f'<rect x="{-lw / 2:.1f}" y="{y - 13:.1f}" width="{lw:.1f}" height="19" rx="4" fill="{SPACE["label_bg"]}"/>'
                + svg.t(0, y + 1, name, MONO, 400, 12.5, col, "middle"))

    backs, fronts, css = [], [], []
    N = 72
    for idx, (name, kind, orx, r, a0, period) in enumerate(ORRERY):
        ory = orx * k
        frames = []
        for i in range(N + 1):
            th = math.radians(a0 + 360 * i / N)
            px, py, s = cx + orx * math.cos(th), cy + ory * math.sin(th), 1 + 0.12 * math.sin(th)
            frames.append(f"{100 * i / N:.3f}%{{transform:translate({px:.2f}px,{py:.2f}px) scale({s:.3f})}}")
        css.append(f"@keyframes m{idx}{{{''.join(frames)}}}")
        # front copy visible while sin(theta) >= 0 ; crossing angles 0 and 180 degrees
        def frac(target):
            return ((target - a0) % 360) / 360 * 100
        f0, f180 = frac(360), frac(180)  # front -> back at 360/0, back -> front at 180
        eps = 0.01
        def opacity_kf(name_, front):
            pts = []
            th0 = math.sin(math.radians(a0))
            start = 1 if (th0 >= 0) == front else 0
            cuts = sorted([(f0, "to_back"), (f180, "to_front")])
            val = start
            pts.append(f"0%{{opacity:{val}}}")
            for fcut, kind_ in cuts:
                pts.append(f"{fcut:.3f}%{{opacity:{val}}}")
                val = (1 if front else 0) if kind_ == "to_front" else (0 if front else 1)
                pts.append(f"{min(fcut + eps, 100):.3f}%{{opacity:{val}}}")
            pts.append(f"100%{{opacity:{val}}}")
            return f"@keyframes {name_}{{{''.join(pts)}}}"
        css.append(opacity_kf(f"of{idx}", True))
        css.append(opacity_kf(f"ob{idx}", False))
        th = math.radians(a0)
        px, py, s = cx + orx * math.cos(th), cy + ory * math.sin(th), 1 + 0.12 * math.sin(th)
        selected = name == SELECTED
        sel = (f'<circle r="{r + 5}" fill="none" stroke="#ffffff" stroke-width="2.2"/>' if selected else "")
        inner = planet(kind, r) + sel + label_markup(name, r, selected)
        is_front = math.sin(th) >= 0
        for copy, lst, an in (("f", fronts, f"of{idx}"), ("b", backs, f"ob{idx}")):
            vis = 1 if (copy == "f") == is_front else 0
            lst.append(f'<g class="orb" transform="translate({px:.2f} {py:.2f}) scale({s:.3f})" opacity="{vis}" '
                       f'style="animation:m{idx} {period}s linear infinite,{an} {period}s linear infinite">{inner}</g>')
    svg.css.extend(css)
    svg.css.append("@media (prefers-reduced-motion: reduce){.orb,.tw{animation:none!important}}")
    g.extend(reversed(backs))  # farthest (outer) first
    g.append(f'<circle cx="{cx}" cy="{cy}" r="66" fill="url(#sunglow)"/>')
    g.append(f'<circle cx="{cx}" cy="{cy}" r="33" fill="url(#sun)"/>')
    g.append(svg.t(cx, cy + 8.5, "TP", HEAD, 600, 23, "#ffffff", "middle"))
    g.extend(fronts)
    g.append("</g>")
    svg.add(*g)
    return svg.render(width_attr=False)


# ---------------------------------------------------------------- section header
def header(text, th):
    s = text.upper()
    size, ls = 19, 0.08
    w = 22 + FONTS.width(s, (HEAD, 600), size, ls) + 6
    svg = SVG(round(w), 36, text)
    svg.add(f'<rect x="0" y="6" width="5" height="24" rx="2.5" fill="{th["highlight"]}"/>',
            svg.t(20, 26, s, HEAD, 600, size, th["text"], ls=ls))
    return svg.render()


# ---------------------------------------------------------------- buttons
def button(label, primary, th):
    size = 15.5
    w = FONTS.width(label, (BODY, 700), size) + 40
    svg = SVG(round(w), 42, label)
    if primary:
        svg.add(f'<rect x="1" y="1" width="{w - 2:.1f}" height="40" rx="8" fill="{th["accent"]}"/>',
                svg.t(w / 2, 26.5, label, BODY, 700, size, th["accent_contrast"], "middle"))
    else:
        svg.add(f'<rect x="1" y="1" width="{w - 2:.1f}" height="40" rx="8" fill="{th["card"]}" '
                f'stroke="{th["accent"]}" stroke-opacity="0.55" stroke-width="1.5"/>',
                svg.t(w / 2, 26.5, label, BODY, 700, size, th["text"], "middle"))
    return svg.render()


# ---------------------------------------------------------------- chips
def chips(svg, items, x0, y0, max_x, th, size=13.5, h=28, gap=8, row_gap=10, pad=11):
    out, x, y = [], x0, y0
    for it in items:
        w = FONTS.width(it, (MONO, 400), size) + 2 * pad
        if x + w > max_x and x > x0:
            x, y = x0, y + h + row_gap
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="5" fill="{th["tag_bg"]}"/>')
        out.append(svg.t(x + pad, y + h / 2 + size * 0.34, it, MONO, 400, size, th["tag_text"]))
        x += w + gap
    return out, y + h


# ---------------------------------------------------------------- project card
CARD_W, MEDIA_W = 1000, 246


def card_layout(p):
    tx0, tx1 = 20 + MEDIA_W + 30, CARD_W - 32
    tw = tx1 - tx0
    summ = wrap(p["summary"], (BODY, 400), 17, tw)
    lab_w = FONTS.width("Result", (BODY, 700), 16) + 12
    res = wrap(p["result"], (BODY, 400), 16, tw - lab_w)
    return tx0, tx1, summ, res, lab_w


def card_height(p):
    _, _, summ, res, _ = card_layout(p)
    return 104 + 25 * len(summ) + 8 + 23 * len(res) + 4 + 28 + 26


def card(p, th, H):
    svg = SVG(CARD_W, H, f"{p['title']} ({p['dates']})", p["alt"])
    planet_defs(svg, {p["kind"]})
    mid = svg.uid("media")
    svg.defs.append(f'<clipPath id="{mid}"><rect x="20" y="20" width="{MEDIA_W}" height="{H - 40}" rx="12"/></clipPath>')
    svg.defs.append('<radialGradient id="mglow" r="0.5"><stop offset="0" stop-color="#787eff" stop-opacity="0.25"/>'
                    '<stop offset="1" stop-color="#787eff" stop-opacity="0"/></radialGradient>')
    tx0, tx1, summ, res, lab_w = card_layout(p)
    b = [f'<rect x="1" y="1" width="{CARD_W - 2}" height="{H - 2}" rx="16" fill="{th["card"]}" '
         f'stroke="{th["card_border"]}" stroke-width="1.5"/>']
    # media tile: the project as a planet
    mcx, mcy = 20 + MEDIA_W / 2, H / 2
    pr = min(58, (H - 40) * 0.3)
    b.append(f'<g clip-path="url(#{mid})"><rect x="20" y="20" width="{MEDIA_W}" height="{H - 40}" fill="{SPACE["bg"]}"/>'
             f'<ellipse cx="{mcx}" cy="{mcy}" rx="150" ry="110" fill="url(#mglow)"/>'
             + stars(svg, 20, 20, MEDIA_W, H - 40, 46, sum(map(ord, p["slug"])))
             + f'<ellipse cx="{mcx}" cy="{mcy + 6}" rx="{MEDIA_W * 0.44:.1f}" ry="{pr * 0.55:.1f}" fill="none" '
               f'stroke="{SPACE["border"]}" stroke-opacity="0.6" stroke-width="1.6" stroke-dasharray="0.1 6" stroke-linecap="round"/>'
             + f'<g transform="translate({mcx} {mcy})">{planet(p["kind"], pr)}</g></g>')
    # title, leader, dates
    ty = 58
    b.append(svg.t(tx0, ty, p["title"], HEAD, 600, 23, th["text"]))
    tw_ = FONTS.width(p["title"], (HEAD, 600), 23)
    dw = FONTS.width(p["dates"], (MONO, 700), 14.5)
    lx0, lx1 = tx0 + tw_ + 14, tx1 - dw - 14
    if lx1 > lx0:
        b.append(f'<line x1="{lx0:.1f}" y1="{ty - 5}" x2="{lx1:.1f}" y2="{ty - 5}" stroke="{th["border"]}" '
                 'stroke-width="2" stroke-dasharray="0.1 6" stroke-linecap="round"/>')
    b.append(svg.t(tx1, ty, p["dates"], MONO, 700, 14.5, th["text"], "end"))
    b.append(svg.t(tx0, 86, p["meta"], BODY, 400, 15.5, th["muted"]))
    y = 118
    for ln in summ:
        b.append(svg.t(tx0, y, ln, BODY, 400, 17, th["text"]))
        y += 25
    y += 6
    b.append(svg.t(tx0, y, "Result", BODY, 700, 16, th["highlight"]))
    for ln in res:
        b.append(svg.t(tx0 + lab_w, y, ln, BODY, 400, 16, th["text"]))
        y += 23
    # tags + call to action on the last row
    cta_w = (FONTS.width(p["cta"], (BODY, 700), 15) + 26) if p["cta"] else 0
    ty2 = H - 20 - 28 - 4
    out, _ = chips(svg, p["tags"], tx0, ty2, tx1 - cta_w - 16, th)
    b.extend(out)
    if p["cta"]:
        b.append(svg.t(tx1 - 20, ty2 + 19, p["cta"], BODY, 700, 15, th["accent"], "end"))
        b.append(arrow(tx1 - 12, ty2 + 9, th["accent"], 9, 2))
    svg.add(*b)
    return svg.render(width_attr=False)


# ---------------------------------------------------------------- skills
def skills(th):
    W = 1000
    svg = SVG(W, 10, "Skills", "; ".join(f"{g}: {', '.join(i)}" for g, i in SKILLS))
    b, y = [], 4
    for group, items in SKILLS:
        b.append(svg.t(0, y + 19, group, HEAD, 600, 15.5, th["highlight"]))
        out, bottom = chips(svg, items, 190, y, W, th, size=14, h=30)
        b.extend(out)
        y = bottom + 14
    svg.h = y
    svg.add(*b)
    return svg.render(width_attr=False)


# ---------------------------------------------------------------- background (timeline)
def background(th):
    W = 1000
    desc = "; ".join(f"{t} ({d}), {o}" for _, items in BACKGROUND for (t, d, o, _x) in items)
    svg = SVG(W, 10, "Background", desc)
    b, y = [], 0
    for gi, (group, items) in enumerate(BACKGROUND):
        y += 18 if gi == 0 else 30
        b.append(svg.t(0, y, group, MONO, 700, 12.5, th["muted"], ls=0.12))
        y += 12
        for (title, dates, org, detail) in items:
            y += 26
            b.append(svg.t(0, y, title, HEAD, 600, 17, th["text"]))
            tw_ = FONTS.width(title, (HEAD, 600), 17)
            dw = FONTS.width(dates, (MONO, 700), 14)
            if W - dw - 14 > tw_ + 14:
                b.append(f'<line x1="{tw_ + 14:.1f}" y1="{y - 5}" x2="{W - dw - 14:.1f}" y2="{y - 5}" '
                         f'stroke="{th["border"]}" stroke-width="2" stroke-dasharray="0.1 6" stroke-linecap="round"/>')
            b.append(svg.t(W, y, dates, MONO, 700, 14, th["text"], "end"))
            y += 24
            line = (f'<text x="0" y="{y}" font-size="15.5">' + svg.span(org, BODY, 400, th["accent"])
                    + (svg.span(" · " + detail, BODY, 400, th["muted"]) if detail else "") + "</text>")
            b.append(line)
            y += 8
    svg.h = y + 10
    svg.add(*b)
    return svg.render(width_attr=False)


# ---------------------------------------------------------------- README
def picture(name, alt, extra=""):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'<img src="assets/{name}-light.svg" alt="{escape(alt, {chr(34): "&quot;"})}"{extra}></picture>')


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    write(os.path.join(ASSETS, "banner.svg"), banner())
    H = max(card_height(p) for p in PROJECTS + list(KIT_CARDS.values()))
    for th in (LIGHT, DARK):
        n = th["name"]
        for key, text in HEADERS.items():
            write(os.path.join(ASSETS, f"h-{key}-{n}.svg"), header(text, th))
        for key, label, primary in BUTTONS:
            write(os.path.join(ASSETS, f"btn-{key}-{n}.svg"), button(label, primary, th))
        for p in PROJECTS:
            write(os.path.join(ASSETS, f"card-{p['slug']}-{n}.svg"), card(p, th, H))
        write(os.path.join(ASSETS, f"skills-{n}.svg"), skills(th))
        write(os.path.join(ASSETS, f"background-{n}.svg"), background(th))
        # cards for the project repositories (copied to docs/readme/ in each repo)
        all_cards = {p["slug"]: p for p in PROJECTS}
        all_cards.update({v["slug"]: v for v in KIT_CARDS.values()})
        for repo, slug in KIT_REPOS.items():
            kit = dict(all_cards[slug], cta="Case study" if all_cards[slug]["cta"] else "")
            write(os.path.join(KITS, f"{repo}-{n}.svg"), card(kit, th, H))
    print("assets written to", ASSETS)


if __name__ == "__main__":
    sys.exit(main())
