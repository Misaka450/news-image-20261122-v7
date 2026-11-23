#!/usr/bin/env python3
"""
v7 Broadsheet News Infographic Builder — Sunday 22 November 2026
Strategy: Fewer words, bigger bold flat-fill illustrations, generous breathing room.
20 verified stories (15 illustrated cards in 3x5 + 5 single-line icon briefs),
7 regions (2-3 per region), 4 oversized 56px KPI figures, 8-event UTC strip,
10-pin minimalist world map, and calm low-edge-density bands (all <= 35).

Pure Python + Pillow deterministic 1024x1024 renderer + 300x300 preview.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# 1. Canvas, Palette & Typography Configuration
# ---------------------------------------------------------------------------

CANVAS_W = 1024
CANVAS_H = 1024
MARGIN_X = 14
INNER_W = CANVAS_W - 2 * MARGIN_X  # 996 px
SECTION_GAP = 12
COL_GAP = 12
ROW_GAP = 10
MAX_BYTES = 1_048_576  # 1 MiB limit

OUT_DIR = Path(__file__).resolve().parent
ENTRY_PATH = OUT_DIR / "entry.png"
PREVIEW_PATH = OUT_DIR / "preview-300.png"

# Warm newsprint broadsheet palette (unboxed open-paper craft)
BG_PAPER = "#F8F3E9"
DATE_CHECK_BG = "#FBF7EE"
RULE_HAIRLINE = "#DDD4C4"
RULE_SOFT = "#E7DFD1"

INK_DARK = "#121923"
INK_BODY = "#28303D"
INK_MUTED = "#5A6270"

NAVY_BAR = "#101D3D"
NAVY_UTC = "#162647"
NAVY_DIV = "#2E436F"
MAP_OCEAN = "#162647"

CRIMSON = "#9E1F28"
BRIGHT_RED = "#DC4538"
GOLD = "#EBC365"
WARM_IVORY = "#F3ECE0"
WHITE = "#FFFFFF"

REGION_ORDER = [
    "EUROPE",
    "ASIA-PACIFIC",
    "AMERICAS",
    "MIDDLE EAST",
    "AFRICA",
    "OCEANIA",
    "WORLD",
]

REGION_COLORS: Dict[str, str] = {
    "EUROPE": "#235773",
    "ASIA-PACIFIC": "#B45E1F",
    "AMERICAS": "#33548E",
    "MIDDLE EAST": "#A6232B",
    "AFRICA": "#3B7042",
    "OCEANIA": "#6E4B8A",
    "WORLD": "#4D5560",
}

ICON_BACKDROPS: Dict[str, str] = {
    "EUROPE": "#E2ECF2",
    "ASIA-PACIFIC": "#F3E6D8",
    "AMERICAS": "#E3E9F4",
    "MIDDLE EAST": "#F2E2E3",
    "AFRICA": "#E2ECE3",
    "OCEANIA": "#EBE4F1",
    "WORLD": "#E6E8EB",
}

MAP_LAND_FILL: Dict[str, str] = {
    "EUROPE": "#467794",
    "ASIA-PACIFIC": "#9E6E46",
    "AMERICAS": "#4E6D9E",
    "MIDDLE EAST": "#994A50",
    "AFRICA": "#4E8256",
    "OCEANIA": "#775B91",
    "WORLD": "#657180",
}

FONT_PATHS = {
    "serif_bold": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "serif_reg": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "serif_cond_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf",
    "sans_bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "sans_reg": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "sans_cond_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    "sans_cond_reg": "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
    "mono_bold": "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
}

_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}


def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (key, size)
    if cache_key not in _FONT_CACHE:
        path = FONT_PATHS[key]
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required font: {path}")
        _FONT_CACHE[cache_key] = ImageFont.truetype(path, size)
    return _FONT_CACHE[cache_key]


# ---------------------------------------------------------------------------
# 2. Data Model & 20 Curated Verified Stories (Sunday 22 November 2026)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Story:
    id: int
    region: str
    domain: str
    headline: str
    lead: str
    location: str
    source: str
    status: str
    coords: Optional[Tuple[float, float]] = None


STORIES: List[Story] = [
    # --- Row 1: 3 Hero Cards (324x150 top poster art + text below) ---
    Story(
        1, "WORLD", "CLIMATE",
        "COP31 collapses in Antalya",
        "Nearly 200 nations deadlock past 03:00 UTC over fossil fuels and a $120bn floor.",
        "ANTALYA", "Reuters, AFP, BBC", "Confirmed", (30.7, 36.9),
    ),
    Story(
        2, "EUROPE", "MILITARY",
        "Russia fires 186 drones; 161 downed",
        "Overnight wave of 72 jet UAVs batters Dymer flats and triggers power blackouts.",
        "KYIV", "Ukr. Air Force, BBC", "Confirmed", (30.5, 50.4),
    ),
    Story(
        3, "AFRICA", "MILITARY",
        "Warship Merkury sinks in Benghazi",
        "Russian corvette capsizes after suspected sea-drone strike off eastern Libya.",
        "BENGHAZI", "Reuters, Al Jazeera", "Confirmed", (20.1, 32.1),
    ),
    # --- Rows 2-5: 12 Featured 3-Column Cards (150x92 flat poster art + right text) ---
    Story(
        4, "MIDDLE EAST", "MILITARY",
        "Iran strike hurts 2 in Bahrain",
        "Manama cites Sitra fire; IRGC claims Patriot hit.",
        "SITRA", "MEE, Times of Israel", "Claim", (50.6, 26.2),
    ),
    Story(
        5, "ASIA-PACIFIC", "POLITICS",
        "HK polls hit 98.8% with 856",
        "Election body fills 723 seats as 5,640 vote.",
        "HONG KONG", "info.gov.hk, China Daily", "Confirmed", (114.2, 22.3),
    ),
    Story(
        6, "WORLD", "SPACE",
        "BepiColombo reaches Mercury",
        "Probe enters orbit after 8 yrs to map crust.",
        "MERCURY", "BBC, ESA", "Confirmed", None,
    ),
    Story(
        7, "AMERICAS", "SECURITY",
        "Mexico seizes cartel chief",
        "Forces nab FBI Most Wanted boss Meza Flores.",
        "SINALOA", "BBC, Reuters", "Confirmed", (-107.4, 24.8),
    ),
    Story(
        8, "OCEANIA", "SPORT",
        "India hits record 720/9",
        "Visitors set NZ Test mark before hosts draw.",
        "WELLINGTON", "ESPN, Jamaica Obs.", "Confirmed", (174.8, -41.3),
    ),
    Story(
        9, "ASIA-PACIFIC", "DISASTER",
        "Banten plant fire kills 3",
        "Rescuers comb gutted factory; 36 missing.",
        "BANTEN", "AFP, BBC", "Ongoing", (106.1, -6.1),
    ),
    Story(
        10, "EUROPE", "POLITICS",
        "Fico blocks €45bn EU loan",
        "Slovak PM vetoes EU aid package for Ukraine.",
        "BRATISLAVA", "Reuters, Kyiv Post", "Confirmed", None,
    ),
    Story(
        11, "EUROPE", "SPORT",
        "Alcaraz wins ATP Finals",
        "Spaniard tops Zverev in Turin for first title.",
        "TURIN", "Reuters, Guardian", "Confirmed", None,
    ),
    Story(
        12, "MIDDLE EAST", "CRISIS",
        "Gaza toll hits 74,742",
        "Health ministry updates toll; talks urged.",
        "GAZA", "WAFA, Anadolu", "Ongoing", None,
    ),
    Story(
        13, "AMERICAS", "SPORT",
        "Wembanyama drops 50 pts",
        "Spurs star posts 50-pt, 19-reb Texas night.",
        "SAN ANTONIO", "CBS, KSAT", "Confirmed", None,
    ),
    Story(
        14, "AFRICA", "CONFLICT",
        "Drones strike Khartoum",
        "RSF UAVs hit homes and UN site; four killed.",
        "KHARTOUM", "Al Jazeera", "Reported", None,
    ),
    Story(
        15, "AMERICAS", "SPORT",
        "Verstappen wins Vegas F1",
        "Beats both McLarens under Las Vegas lights.",
        "LAS VEGAS", "Guardian, BBC", "Confirmed", (-115.1, 36.2),
    ),
    # --- 5 Single-Line Supplementary Briefs (#16-#20) ---
    Story(
        16, "MIDDLE EAST", "POLITICS",
        "Lebanon marks 83rd Independence Day",
        "Displaced locals return for holiday",
        "Beirut", "NPR, L'Orient", "Ongoing", None,
    ),
    Story(
        17, "ASIA-PACIFIC", "TECH",
        "S. Korea education chief quits",
        "Resigns amid AI exam chaos",
        "Seoul", "AFP, BBC", "Confirmed", None,
    ),
    Story(
        18, "AFRICA", "DISASTER",
        "Boat capsize kills 24 mourners",
        "River tragedy hits southern state",
        "Bayelsa", "AllAfrica", "Confirmed", (6.1, 4.8),
    ),
    Story(
        19, "OCEANIA", "CLIMATE",
        "Pope urges aid for PNG drought",
        "Severe drought grips all 22 zones",
        "Port Moresby", "Crux, CathNews", "Ongoing", None,
    ),
    Story(
        20, "WORLD", "TRADE",
        "WTO flags $1.5tn & $5.4tn curbs",
        "Record global export & import curbs",
        "Geneva", "WTO, SunStar", "Confirmed", None,
    ),
]

UTC_TIMELINE: List[Tuple[str, str]] = [
    ("01:00", "HK polls"),
    ("01:25", "Cartel raid"),
    ("03:00", "COP31 fails"),
    ("04:00", "Vegas F1"),
    ("09:20", "Korea AI"),
    ("10:44", "Mercury"),
    ("14:05", "Banten fire"),
    ("20:43", "Alcaraz ATP"),
]

EXCLUDED_ITEMS: List[str] = [
    "Peru M6.7 quake (20 Nov)",
    "Russia 400-drone barrage (19–20 Nov)",
    "APEC Shenzhen summit (19 Nov)",
    "French Senate vote (20 Nov)",
]


def extract_verified_kpis(stories: Sequence[Story]) -> List[Tuple[str, str, int, str]]:
    """Extract the 4 hardest KPI figures directly from STORIES via regex."""
    by_id = {s.id: s for s in stories}

    def pull(sid: int, pattern: str) -> str:
        s = by_id[sid]
        blob = f"{s.headline} {s.lead}"
        m = re.search(pattern, blob)
        if not m:
            raise AssertionError(f"KPI regex {pattern!r} failed on story #{sid}: {blob!r}")
        return m.group(1)

    specs = [
        (2, r"\bfires\s+(\d+)\s+drones\b", "Drones fired at Ukraine"),
        (2, r";\s*(\d+)\s+downed\b", "Drones downed"),
        (1, r"(\$120bn)\b", "COP31 finance floor"),
        (12, r"hits\s+([\d,]+)\b", "Gaza death toll"),
    ]
    kpis: List[Tuple[str, str, int, str]] = []
    for sid, pat, label in specs:
        val = pull(sid, pat)
        kpis.append((val, label, sid, by_id[sid].region))

    expected = ["186", "161", "$120bn", "74,742"]
    got = [k[0] for k in kpis]
    assert got == expected, f"KPI mismatch: got {got}, expected {expected}"
    return kpis


def validate_dataset(stories: Sequence[Story]) -> Counter:
    assert len(stories) == 20, f"Expected 20 stories, got {len(stories)}"
    assert [s.id for s in stories] == list(range(1, 21)), "Story IDs must be 1..20"
    counts = Counter(s.region for s in stories)
    assert set(counts.keys()) == set(REGION_ORDER), f"Unexpected regions: {set(counts.keys())}"
    for r in REGION_ORDER:
        assert 2 <= counts[r] <= 3, f"Region {r} must have 2-3 stories, got {counts[r]}"
    mapped = [s for s in stories if s.coords is not None]
    assert len(mapped) == 10, f"Expected 10 mapped key pins, got {len(mapped)}"
    return counts


# ---------------------------------------------------------------------------
# 3. Typography Fitting & Collision Detection
# ---------------------------------------------------------------------------

def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_key: str,
    max_size: int,
    min_size: int,
    max_width: float,
    max_height: Optional[float] = None,
) -> Tuple[ImageFont.FreeTypeFont, int, int, int]:
    for size in range(max_size, min_size - 1, -1):
        font = get_font(font_key, size)
        w, h = measure_text(draw, text, font)
        if w <= max_width and (max_height is None or h <= max_height):
            return font, size, w, h
    raise RuntimeError(
        f"fit() overflow: {text!r} cannot fit w={max_width}, h={max_height} at min={min_size} ({font_key})"
    )


def _wrap_words(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: float,
) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    cur = words[0]
    for word in words[1:]:
        cand = f"{cur} {word}"
        if measure_text(draw, cand, font)[0] <= max_width:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def fit_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_key: str,
    max_size: int,
    min_size: int,
    max_width: float,
    max_lines: int,
    line_spacing: float = 1.12,
    max_height: Optional[float] = None,
) -> Tuple[ImageFont.FreeTypeFont, int, List[str], int]:
    for size in range(max_size, min_size - 1, -1):
        font = get_font(font_key, size)
        lines = _wrap_words(draw, text, font, max_width)
        if len(lines) > max_lines:
            continue
        if any(measure_text(draw, ln, font)[0] > max_width for ln in lines):
            continue
        line_h = max(int(round(size * line_spacing)), measure_text(draw, "Ag", font)[1])
        if max_height is not None and line_h * len(lines) > max_height:
            continue
        return font, size, lines, line_h
    raise RuntimeError(
        f"fit_multiline() overflow: {text!r} cannot fit {max_lines}L x w={max_width}, h={max_height} at min={min_size}"
    )


def draw_text_centered(
    draw: ImageDraw.ImageDraw,
    box: Tuple[float, float, float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    tb = draw.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = x0 + (x1 - x0 - tw) / 2.0 - tb[0]
    ty = y0 + (y1 - y0 - th) / 2.0 - tb[1]
    draw.text((tx, ty), text, font=font, fill=fill)
    return (tx + tb[0], ty + tb[1], tx + tb[2], ty + tb[3])


def draw_text_aligned(
    draw: ImageDraw.ImageDraw,
    box: Tuple[float, float, float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    align: str = "left",
) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    tb = draw.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = (x1 - tw - tb[0]) if align == "right" else (x0 - tb[0])
    ty = y0 + (y1 - y0 - th) / 2.0 - tb[1]
    draw.text((tx, ty), text, font=font, fill=fill)
    return (tx + tb[0], ty + tb[1], tx + tb[2], ty + tb[3])


def draw_text_baseline_centered(
    draw: ImageDraw.ImageDraw,
    x0: float,
    x1: float,
    baseline_y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> Tuple[float, float, float, float]:
    ascent, _ = font.getmetrics()
    tb = draw.textbbox((0, 0), text, font=font)
    tw = tb[2] - tb[0]
    tx = x0 + (x1 - x0 - tw) / 2.0 - tb[0]
    ty = baseline_y - ascent
    draw.text((tx, ty), text, font=font, fill=fill)
    return (tx + tb[0], ty + tb[1], tx + tb[2], ty + tb[3])


class CollisionTracker:
    def __init__(self, canvas_w: int = CANVAS_W, canvas_h: int = CANVAS_H) -> None:
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.groups: Dict[str, List[Tuple[str, Tuple[float, float, float, float]]]] = {}
        self.total_registered = 0

    def add(self, group: str, label: str, box: Tuple[float, float, float, float]) -> None:
        x0, y0, x1, y1 = box
        if x1 < x0 or y1 < y0:
            raise ValueError(f"Inverted box {group}/{label}: {box}")
        if x0 < -0.5 or y0 < -0.5 or x1 > self.canvas_w + 0.5 or y1 > self.canvas_h + 0.5:
            raise AssertionError(f"Out-of-canvas box {group}/{label}: {box}")
        self.groups.setdefault(group, []).append((label, box))
        self.total_registered += 1

    def assert_no_collisions(self, tolerance: float = 0.25) -> int:
        checked_pairs = 0
        collisions: List[str] = []
        for group, items in self.groups.items():
            n = len(items)
            for i in range(n):
                l1, (ax0, ay0, ax1, ay1) = items[i]
                for j in range(i + 1, n):
                    l2, (bx0, by0, bx1, by1) = items[j]
                    checked_pairs += 1
                    ix = min(ax1, bx1) - max(ax0, bx0)
                    iy = min(ay1, by1) - max(ay0, by0)
                    if ix > tolerance and iy > tolerance:
                        collisions.append(
                            f"[{group}] {l1} {tuple(round(v, 1) for v in items[i][1])} "
                            f"overlaps {l2} {tuple(round(v, 1) for v in items[j][1])} "
                            f"by ({ix:.1f}x{iy:.1f})"
                        )
        if collisions:
            raise AssertionError(
                f"Detected {len(collisions)} layout collision(s):\n" + "\n".join(collisions[:15])
            )
        return checked_pairs


# ---------------------------------------------------------------------------
# 4. Simplified World Map Polygons & 10-Pin Collision Resolver
# ---------------------------------------------------------------------------

WORLD_POLYGONS: List[Tuple[str, List[Tuple[float, float]]]] = [
    ("AMERICAS", [
        (-162, 65), (-132, 69), (-95, 63), (-62, 58), (-55, 48), (-74, 37),
        (-82, 26), (-97, 22), (-86, 15), (-79, 9), (-93, 15), (-112, 29),
        (-125, 46), (-148, 60),
    ]),
    ("AMERICAS", [(-52, 62), (-22, 74), (-44, 80), (-58, 72)]),
    ("AMERICAS", [
        (-78, 10), (-60, 9), (-36, -7), (-41, -23), (-55, -36),
        (-68, -53), (-74, -42), (-71, -18), (-81, -4),
    ]),
    ("EUROPE", [
        (-9, 37), (-4, 48), (8, 54), (24, 58), (44, 66), (50, 52),
        (36, 46), (24, 38), (12, 44), (-5, 36),
    ]),
    ("EUROPE", [(7, 58), (20, 62), (28, 70), (14, 68)]),
    ("AFRICA", [
        (-16, 15), (-6, 36), (12, 34), (33, 31), (48, 12), (40, -10),
        (30, -33), (17, -34), (11, -6), (5, 5), (-15, 11),
    ]),
    ("MIDDLE EAST", [
        (27, 41), (46, 40), (60, 34), (58, 22), (44, 13), (35, 29), (27, 37),
    ]),
    ("ASIA-PACIFIC", [
        (52, 54), (72, 71), (122, 72), (168, 65), (144, 52), (128, 38),
        (120, 24), (108, 12), (102, 2), (96, 18), (80, 9), (66, 24), (54, 40),
    ]),
    ("ASIA-PACIFIC", [(131, 31), (143, 38), (143, 44), (134, 36)]),
    ("ASIA-PACIFIC", [(96, 4), (114, -8), (103, -6)]),
    ("OCEANIA", [
        (114, -22), (132, -13), (148, -19), (151, -36), (134, -34), (115, -33),
    ]),
    ("OCEANIA", [(173, -36), (176, -40), (168, -45)]),
]


def project_lonlat(
    lon: float,
    lat: float,
    map_box: Tuple[float, float, float, float],
) -> Tuple[float, float]:
    x0, y0, x1, y1 = map_box
    lon_min, lon_max = -172.0, 184.0
    lat_min, lat_max = -56.0, 80.0
    px = x0 + (lon - lon_min) / (lon_max - lon_min) * (x1 - x0)
    py = y0 + (lat_max - lat) / (lat_max - lat_min) * (y1 - y0)
    return px, py


def resolve_map_pin_collisions(
    pin_stories: Sequence[Story],
    map_box: Tuple[float, float, float, float],
    pin_radius: float = 6.0,
    min_gap: float = 4.8,
) -> List[Tuple[Story, Tuple[float, float], Tuple[float, float]]]:
    x0, y0, x1, y1 = map_box
    pad = pin_radius + 4.5
    min_dist = 2.0 * pin_radius + min_gap

    anchors: List[Tuple[float, float]] = []
    pos: List[List[float]] = []
    for s in pin_stories:
        assert s.coords is not None
        ax, ay = project_lonlat(s.coords[0], s.coords[1], map_box)
        anchors.append((ax, ay))
        pos.append([
            max(x0 + pad, min(x1 - pad, ax)),
            max(y0 + pad, min(y1 - pad, ay)),
        ])

    n = len(pin_stories)
    for _ in range(300):
        moved = False
        for i in range(n):
            ax, ay = anchors[i]
            pos[i][0] += (ax - pos[i][0]) * 0.03
            pos[i][1] += (ay - pos[i][1]) * 0.03

        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[j][0] - pos[i][0]
                dy = pos[j][1] - pos[i][1]
                dist = math.hypot(dx, dy)
                if dist < min_dist:
                    if dist < 1e-4:
                        ang = ((pin_stories[i].id * 41 + pin_stories[j].id * 23) % 360) * math.pi / 180.0
                        ux, uy = math.cos(ang), math.sin(ang)
                        push = min_dist * 0.55
                    else:
                        ux, uy = dx / dist, dy / dist
                        push = (min_dist - dist) * 0.58 + 0.25
                    pos[i][0] -= ux * push
                    pos[i][1] -= uy * push
                    pos[j][0] += ux * push
                    pos[j][1] += uy * push
                    moved = True

        for i in range(n):
            pos[i][0] = max(x0 + pad, min(x1 - pad, pos[i][0]))
            pos[i][1] = max(y0 + pad, min(y1 - pad, pos[i][1]))
        if not moved:
            break

    return [(pin_stories[i], anchors[i], (pos[i][0], pos[i][1])) for i in range(n)]


# ---------------------------------------------------------------------------
# 5. 15 Bold Flat-Color Editorial Poster Illustrations (Zero Wireframe Noise)
# ---------------------------------------------------------------------------

def _draw_index_badge(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    sid: int,
    accent: str,
    big: bool = False,
) -> None:
    bw, bh = (24, 20) if big else (20, 17)
    badge = (x0, y0, x0 + bw, y0 + bh)
    draw.rectangle(badge, fill=accent)
    f_idx = get_font("sans_bold", 11 if big else 10)
    draw_text_centered(draw, badge, str(sid), f_idx, WHITE)


def draw_card_illustration(
    canvas_img: Image.Image,
    story: Story,
    box: Tuple[int, int, int, int],
    accent: str,
    is_hero: bool = False,
) -> None:
    """
    Constructivist flat-fill 2-3 tone poster art rendered on an isolated clipped
    (w, h) sub-canvas so zero geometry can ever bleed past card boundaries.
    - Hero Row 1 (#1-#3): 324x150px (height = 150px)
    - Rows 2-5 (#4-#15): 150x92px (width = 150px)
    """
    bx0, by0, bx1, by1 = box
    w = bx1 - bx0
    h = by1 - by0
    sub = Image.new("RGB", (w, h), BG_PAPER)
    draw = ImageDraw.Draw(sub)

    x0, y0, x1, y1 = 0, 0, w, h
    cx = w // 2
    cy = h // 2
    sid = story.id

    if sid == 1:
        # HERO #1 (324x150): COP31 collapse — deep teal hall + cracked globe + properly joined tilted gavel
        assert h >= 150
        draw.rectangle((x0, y0, x1, y1), fill="#193740")
        draw.rectangle((x0, y1 - 22, x1, y1), fill="#12272E")
        draw.polygon([(x0 + 18, y1), (x0 + 52, y1 - 20), (x1 - 52, y1 - 20), (x1 - 18, y1)], fill="#244B56")
        # Crisp mint-ivory globe on left-center with stylized continents
        gx, gy, gr = 112, cy + 4, 52
        draw.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill="#C7DFD4")
        draw.polygon([(gx - 38, gy - 14), (gx - 18, gy - 34), (gx - 6, gy - 20), (gx - 12, gy + 4), (gx - 28, gy + 16)], fill="#4E8377")
        draw.polygon([(gx + 8, gy - 30), (gx + 34, gy - 18), (gx + 40, gy + 4), (gx + 22, gy + 24), (gx + 6, gy + 8)], fill="#4E8377")
        draw.polygon([(gx - 24, gy + 24), (gx - 6, gy + 20), (gx - 10, gy + 42), (gx - 26, gy + 36)], fill="#4E8377")
        # Bold crimson fracture bolt splitting globe cleanly top-to-bottom
        crack = [
            (gx - 2, gy - gr - 3), (gx + 9, gy - 14), (gx - 5, gy + 4),
            (gx + 11, gy + gr + 3), (gx + 1, gy + gr + 3), (gx - 13, gy + 4),
            (gx + 1, gy - 14), (gx - 10, gy - gr - 3),
        ]
        draw.polygon(crack, fill=BRIGHT_RED)
        # Properly joined tilted wooden gavel on right side (handle joins center of mallet head)
        # Mallet center at (232, 52), tilted -28 deg: mallet axis along (-0.47, 0.88), handle axis along (0.88, 0.47)
        # Handle extending down-right from mallet center (232, 52) to (296, 88)
        draw.polygon([
            (228, 56), (294, 92), (300, 81), (234, 45),
        ], fill=GOLD)
        # Collar ring where handle meets mallet
        draw.polygon([(234, 43), (244, 49), (237, 62), (227, 56)], fill="#C79938")
        # Solid wooden mallet head centered at (226, 48), perpendicular to handle
        draw.polygon([
            (204, 62), (234, 18), (254, 31), (224, 75),
        ], fill=GOLD)
        # Ivory end-caps on both striking faces of mallet head
        draw.polygon([(201, 60), (208, 65), (228, 78), (221, 73)], fill=WARM_IVORY)
        draw.polygon([(231, 16), (238, 21), (258, 34), (251, 29)], fill=WARM_IVORY)
        # Sound block directly below striking face
        draw.rectangle((190, y1 - 36, 266, y1 - 22), fill=BRIGHT_RED)
        draw.rectangle((198, y1 - 40, 258, y1 - 36), fill=WARM_IVORY)

    elif sid == 2:
        # HERO #2 (324x150): 186 drones / 161 downed — Kyiv night + twin searchlights + gold delta UAVs + crimson bursts
        assert h >= 150
        draw.rectangle((x0, y0, x1, y1), fill="#111F3B")
        draw.polygon([(60, y1 - 24), (115, 0), (172, 0), (82, y1 - 24)], fill="#213961")
        draw.polygon([(w - 78, y1 - 24), (150, 0), (218, 0), (w - 54, y1 - 24)], fill="#274370")
        skyline = [
            (0, y1 - 28, 44, y1),
            (48, y1 - 44, 94, y1),
            (98, y1 - 30, 148, y1),
            (152, y1 - 52, 206, y1),
            (210, y1 - 34, 266, y1),
            (270, y1 - 42, w, y1),
        ]
        for sx0, sy0, sx1, sy1 in skyline:
            draw.rectangle((sx0, sy0, sx1, sy1), fill="#0A1224")
        for wx, wy in [(58, y1 - 34), (74, y1 - 24), (164, y1 - 40), (182, y1 - 26), (284, y1 - 30)]:
            draw.rectangle((wx, wy, wx + 8, wy + 8), fill=GOLD)
        drones = [
            (92, 44, 1.0),
            (168, 36, 1.15),
            (242, 54, 1.05),
            (202, 82, 0.9),
        ]
        for dx, dy, sc in drones:
            s = int(20 * sc)
            pts = [
                (dx - s, dy + int(4 * sc)),
                (dx + int(16 * sc), dy - int(11 * sc)),
                (dx + int(9 * sc), dy + int(4 * sc)),
                (dx + int(16 * sc), dy + int(14 * sc)),
            ]
            draw.polygon(pts, fill=GOLD)
        for ix, iy, r in [(168, 36, 20), (202, 82, 16)]:
            star = []
            for k in range(12):
                ang = k * math.pi / 6.0
                rad = r if k % 2 == 0 else int(r * 0.48)
                star.append((ix + math.cos(ang) * rad, iy + math.sin(ang) * rad))
            draw.polygon(star, fill=BRIGHT_RED)
            draw.ellipse((ix - 6, iy - 6, ix + 6, iy + 6), fill=WARM_IVORY)

    elif sid == 3:
        # HERO #3 (324x150): Warship Merkury sinks — dusk sky + teal sea + capsizing hull + connected smoke + clipped waves
        assert h >= 150
        sea_y = 96
        draw.rectangle((0, 0, w, sea_y), fill="#1E2F44")
        draw.rectangle((0, sea_y, w, h), fill="#265E6B")
        # Connected organic billowing smoke plume rising up-right from midship blaze
        draw.polygon([(164, 52), (192, 12), (262, 0), (304, 18), (270, 56), (210, 68)], fill="#2D3E52")
        draw.ellipse((158, 18, 224, 72), fill="#35485D")
        draw.ellipse((196, 4, 274, 56), fill="#2B3D51")
        draw.ellipse((242, 0, 312, 42), fill="#25364A")
        # Towering solid layered fire plume
        draw.polygon([
            (148, sea_y + 2), (164, 28), (182, 54),
            (198, 20), (216, 58), (224, sea_y + 6),
        ], fill=BRIGHT_RED)
        draw.polygon([
            (164, sea_y + 2), (180, 44), (196, 62),
            (206, 40), (210, sea_y + 2),
        ], fill=GOLD)
        # Massive tilted warship hull pitching sharply into the sea
        hull = [
            (46, sea_y - 34), (236, sea_y + 10),
            (218, sea_y + 28), (62, sea_y - 8),
        ]
        draw.polygon(hull, fill="#9DB0BE")
        bridge = [
            (104, sea_y - 22), (152, sea_y - 11),
            (158, sea_y - 36), (114, sea_y - 45),
        ]
        draw.polygon(bridge, fill="#D4DEE6")
        draw.polygon([
            (128, sea_y - 42), (136, sea_y - 40),
            (146, sea_y - 74), (139, sea_y - 76),
        ], fill=WARM_IVORY)
        # Strictly clipped stylized sea wave bands (isolated sub-canvas guarantees zero right bleed!)
        wave1 = [(0, h), (0, sea_y + 18)]
        for k in range(0, w + 36, 36):
            wave1.append((min(w, k + 18), sea_y + 10))
            wave1.append((min(w, k + 36), sea_y + 20))
        wave1.append((w, h))
        draw.polygon(wave1, fill="#1B4652")
        draw.rectangle((0, h - 12, w, h), fill="#143741")

    elif sid == 4:
        # #4 (150x92): Bahrain refinery strike — ivory storage tanks + fire + diagonal Patriot missile intercept
        draw.rectangle((0, 0, w, h), fill="#2A1F2B")
        base_y = h - 10
        draw.rectangle((0, base_y, w, h), fill="#1A131B")
        # Smoke plume over Sitra tank
        draw.ellipse((24, 6, 74, 40), fill="#443643")
        # Solid fire plume from tank
        draw.polygon([
            (24, base_y - 28), (34, 14), (46, 30),
            (56, 12), (66, base_y - 28),
        ], fill=BRIGHT_RED)
        draw.polygon([(34, base_y - 28), (46, 24), (58, base_y - 28)], fill=GOLD)
        # Solid Sitra refinery tanks
        draw.rectangle((14, base_y - 28, 64, base_y), fill=WARM_IVORY)
        draw.ellipse((14, base_y - 36, 64, base_y - 20), fill="#DCD1BE")
        draw.rectangle((68, base_y - 18, 90, base_y), fill="#B5A89D")
        # Crisp diagonal Patriot interceptor contrail + dart + burst on right
        draw.polygon([(94, base_y), (124, 30), (130, 34), (102, base_y)], fill="#584C3B")
        draw.polygon([(98, base_y), (125, 32), (128, 34), (102, base_y)], fill=GOLD)
        # Starburst intercept impact upper-right
        ix, iy, r = 128, 26, 13
        star = []
        for k in range(10):
            ang = k * math.pi / 5.0
            rad = r if k % 2 == 0 else int(r * 0.45)
            star.append((ix + math.cos(ang) * rad, iy + math.sin(ang) * rad))
        draw.polygon(star, fill=BRIGHT_RED)
        draw.ellipse((ix - 4, iy - 4, ix + 4, iy + 4), fill=WARM_IVORY)

    elif sid == 5:
        # #5 (150x92): HK polls 98.8% — calm slate-blue + ivory ballot box + white ballot + bold crimson check
        draw.rectangle((0, 0, w, h), fill="#2A3C54")
        draw.rectangle((30, 44, w - 30, h - 8), fill=WARM_IVORY)
        draw.rectangle((24, 38, w - 24, 48), fill="#DFD4C0")
        draw.rectangle((cx - 24, 41, cx + 24, 45), fill="#1D2B3E")
        draw.rectangle((cx - 22, 10, cx + 22, 42), fill=WHITE)
        draw.polygon([
            (cx - 12, 24), (cx - 4, 33), (cx + 14, 16),
            (cx + 10, 12), (cx - 4, 26), (cx - 8, 20),
        ], fill=CRIMSON)
        draw.rectangle((44, h - 24, w - 44, h - 16), fill=CRIMSON)

    elif sid == 6:
        # #6 (150x92): BepiColombo reaches Mercury — probe shifted cleanly clear of #6 badge!
        draw.rectangle((0, 0, w, h), fill="#152138")
        # Oversized Mercury sphere bleeding off lower right
        draw.ellipse((62, 26, 182, 146), fill="#D8C29D")
        draw.ellipse((88, 48, 110, 70), fill="#B79E77")
        draw.ellipse((118, 68, 134, 84), fill="#B79E77")
        # Clean gold orbital sweep well clear of badge
        draw.arc((24, 14, 142, 110), 195, 315, fill=GOLD, width=3)
        # Bold twin-wing solar probe shifted right & down so both arrays clear the #6 badge
        sx, sy = 68, 34
        draw.rectangle((sx - 28, sy - 5, sx - 9, sy + 5), fill="#5B9BD5")
        draw.rectangle((sx + 9, sy - 5, sx + 28, sy + 5), fill="#5B9BD5")
        draw.rectangle((sx - 8, sy - 8, sx + 8, sy + 8), fill=WARM_IVORY)
        draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=GOLD)

    elif sid == 7:
        # #7 (150x92): Mexico cartel raid — indigo night + peaks + sleek chopper + spotlight illuminating compound
        draw.rectangle((0, 0, w, h), fill="#1C2C46")
        # Bold warm searchlight beam onto valley compound
        draw.polygon([(cx + 6, 28), (34, h), (124, h)], fill="#4A5448")
        # Solid Sierra Madre peaks
        draw.polygon([
            (0, h), (26, h - 38), (54, h - 18),
            (108, h - 42), (w, h - 20), (w, h),
        ], fill="#0E1728")
        # Small lit cartel compound silhouette inside the spotlight beam
        draw.rectangle((62, h - 22, 98, h), fill="#1B2230")
        draw.polygon([(58, h - 22), (80, h - 32), (102, h - 22)], fill="#273244")
        draw.rectangle((70, h - 14, 78, h - 7), fill=GOLD)
        draw.rectangle((84, h - 14, 92, h - 7), fill=GOLD)
        # Sleeker tactical helicopter silhouette + tail rotor
        hx, hy = cx + 6, 22
        draw.rectangle((hx - 30, hy - 11, hx + 26, hy - 8), fill=WARM_IVORY)
        draw.rectangle((hx - 2, hy - 8, hx + 2, hy - 3), fill=WARM_IVORY)
        draw.polygon([
            (hx - 18, hy + 2), (hx - 8, hy - 5), (hx + 10, hy - 4),
            (hx + 14, hy + 5), (hx - 12, hy + 8),
        ], fill=GOLD)
        draw.polygon([(hx + 10, hy - 1), (hx + 36, hy - 4), (hx + 36, hy + 1), (hx + 10, hy + 4)], fill=WARM_IVORY)
        draw.ellipse((hx + 31, hy - 9, hx + 41, hy + 1), outline=WARM_IVORY, width=2)

    elif sid == 8:
        # #8 (150x92): India 720/9 cricket — rich emerald pitch + solid cream stumps + angled wood bat + crimson ball
        draw.rectangle((0, 0, w, h), fill="#1F4D3B")
        draw.rectangle((0, h - 16, w, h), fill="#2F6B50")
        for sx in (98, 112, 126):
            draw.rectangle((sx - 3, 24, sx + 3, h - 14), fill=WARM_IVORY)
        draw.rectangle((95, 20, 111, 24), fill=GOLD)
        draw.rectangle((113, 20, 129, 24), fill=GOLD)
        draw.polygon([(28, h - 18), (66, 22), (78, 34), (40, h - 8)], fill="#DFBF82")
        draw.polygon([(70, 24), (84, 10), (89, 15), (75, 29)], fill=WARM_IVORY)
        draw.ellipse((26, 16, 48, 38), fill=BRIGHT_RED)

    elif sid == 9:
        # #9 (150x92): Banten plant fire — organic peaked flames inside frame + smoke plume + sawtooth factory
        draw.rectangle((0, 0, w, h), fill="#2A1F21")
        base_y = h - 8
        draw.rectangle((0, base_y, w, h), fill="#161012")
        # Smokestack on left + billowing dark smoke clouds
        draw.rectangle((22, 20, 32, base_y - 26), fill="#3F3435")
        draw.ellipse((32, 4, 82, 34), fill="#443739")
        draw.ellipse((68, 2, 118, 30), fill="#3B2F31")
        # Organic peaked multi-layer flames staying strictly below top border (zero flat crop)
        draw.polygon([
            (46, base_y - 30), (52, 22), (64, 34), (78, 14),
            (92, 32), (104, 20), (114, base_y - 30),
        ], fill=BRIGHT_RED)
        draw.polygon([
            (58, base_y - 30), (66, 30), (78, 24), (90, 34), (98, 28), (102, base_y - 30),
        ], fill=GOLD)
        factory = [
            (14, base_y), (14, base_y - 26),
            (44, base_y - 38), (44, base_y - 26),
            (74, base_y - 38), (74, base_y - 26),
            (104, base_y - 38), (104, base_y - 26),
            (134, base_y - 38), (134, base_y),
        ]
        draw.polygon(factory, fill="#493E3D")
        for wx in (28, 58, 88, 114):
            draw.rectangle((wx, base_y - 18, wx + 14, base_y - 9), fill=GOLD)

    elif sid == 10:
        # #10 (150x92): Fico blocks €45bn EU loan — EU cobalt + 12 solid gold stars + giant white € + bold red veto bar
        draw.rectangle((0, 0, w, h), fill="#173A6E")
        sr = 36
        for k in range(12):
            ang = k * (2 * math.pi / 12)
            sx = cx + math.cos(ang) * sr
            sy = cy + math.sin(ang) * sr
            draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=GOLD)
        f_eu = get_font("serif_bold", 46)
        draw_text_centered(draw, (cx - 26, cy - 26, cx + 26, cy + 26), "€", f_eu, WHITE)
        draw.polygon([
            (cx - 28, cy + 24), (cx + 22, cy - 28),
            (cx + 29, cy - 21), (cx - 21, cy + 31),
        ], fill=BRIGHT_RED)

    elif sid == 11:
        # #11 (150x92): Alcaraz wins ATP Finals — Turin indoor blue court + solid gold chalice + chartreuse tennis ball
        draw.rectangle((0, 0, w, h), fill="#1B4876")
        draw.rectangle((0, h - 24, w, h), fill="#265E94")
        draw.rectangle((0, h - 24, w, h - 21), fill=WARM_IVORY)
        tx = 62
        draw.ellipse((tx - 26, 18, tx - 8, 40), fill=GOLD)
        draw.ellipse((tx - 21, 23, tx - 11, 35), fill="#1B4876")
        draw.ellipse((tx + 8, 18, tx + 26, 40), fill=GOLD)
        draw.ellipse((tx + 11, 23, tx + 21, 35), fill="#1B4876")
        draw.polygon([(tx - 18, 14), (tx + 18, 14), (tx + 11, 48), (tx - 11, 48)], fill=GOLD)
        draw.rectangle((tx - 5, 48, tx + 5, 62), fill=GOLD)
        draw.rectangle((tx - 17, 62, tx + 17, 70), fill="#C99E3D")
        bx, by, br = 116, 38, 16
        draw.ellipse((bx - br, by - br, bx + br, by + br), fill="#D4E34B")
        draw.arc((bx - br - 6, by - br + 2, bx + 2, by + br - 2), 300, 60, fill=WHITE, width=2)

    elif sid == 12:
        # #12 (150x92): Gaza toll 74,742 — dignified dusk horizon layers + subtle mid-ground ridge + skyline + moon
        draw.rectangle((0, 0, w, h), fill="#2D232E")
        draw.rectangle((0, 34, w, h), fill="#6D4343")
        draw.rectangle((0, 52, w, h), fill="#9A5F52")
        draw.ellipse((w - 36, 10, w - 14, 32), fill=WARM_IVORY)
        draw.ellipse((w - 30, 8, w - 10, 28), fill="#2D232E")
        # Mid-ground muted silhouettes for depth
        for sx0, sy0, sx1, sy1 in [(12, h - 38, 42, h), (68, h - 42, 104, h)]:
            draw.rectangle((sx0, sy0, sx1, sy1), fill="#3E2A2E")
        skyline = [
            (0, h - 24, 24, h),
            (26, h - 38, 54, h),
            (56, h - 22, 82, h),
            (84, h - 34, 114, h),
            (116, h - 26, w, h),
        ]
        for sx0, sy0, sx1, sy1 in skyline:
            draw.rectangle((sx0, sy0, sx1, sy1), fill="#171318")

    elif sid == 13:
        # #13 (150x92): Wembanyama 50 pts — backboard + tapered net + basketball arcing cleanly INTO the rim!
        draw.rectangle((0, 0, w, h), fill="#1E2532")
        # Solid backboard centered-left
        draw.rectangle((28, 12, 104, 52), fill="#E9EEF5")
        draw.rectangle((50, 26, 82, 48), fill="#1E2532")
        draw.rectangle((54, 30, 78, 44), fill="#E9EEF5")
        # Classic tapered basketball net below rim
        draw.polygon([(50, 52), (82, 52), (73, 78), (59, 78)], fill="#CBD5E1")
        draw.line((56, 52, 62, 78), fill="#7A8798", width=1)
        draw.line((66, 52, 66, 78), fill="#7A8798", width=1)
        draw.line((76, 52, 70, 78), fill="#7A8798", width=1)
        # Basketball raised high right over rim (clean swish arc!)
        bx, by, br = 94, 34, 18
        draw.arc((bx - 2, by - 20, w - 6, h - 18), 210, 340, fill=GOLD, width=2)
        draw.ellipse((bx - br, by - br, bx + br, by + br), fill="#E6742E")
        draw.rectangle((bx - br + 1, by - 1, bx + br - 1, by + 1), fill="#1E2532")
        draw.rectangle((bx - 1, by - br + 1, bx + 1, by + br - 1), fill="#1E2532")
        # Orange rim drawn in front for depth
        draw.rectangle((46, 49, 86, 55), fill="#E85A2A")

    elif sid == 14:
        # #14 (150x92): Khartoum drones — warm sand dusk sky + distinct sandstone skyline + UN blue roof + UAV
        draw.rectangle((0, 0, w, h), fill="#262A3E")
        draw.rectangle((0, 48, w, h), fill="#3E3543")
        # Impact blast glow behind buildings
        draw.ellipse((78, h - 54, 130, h - 8), fill=BRIGHT_RED)
        draw.ellipse((90, h - 44, 118, h - 16), fill=GOLD)
        # Distinct warm sandstone Khartoum compounds with higher contrast
        draw.rectangle((0, h - 24, 42, h), fill="#6B5948")
        draw.rectangle((46, h - 32, 92, h), fill="#7D6854")
        # Subtle UN-blue compound roof stripe on center building
        draw.rectangle((46, h - 34, 92, h - 29), fill="#4A90C8")
        draw.rectangle((96, h - 26, w, h), fill="#5A4A3D")
        # Crisp white delta UAV banking overhead left
        dx, dy = 52, 24
        draw.polygon([(dx - 20, dy + 4), (dx + 16, dy - 10), (dx + 8, dy + 4), (dx + 16, dy + 14)], fill=WARM_IVORY)

    elif sid == 15:
        # #15 (150x92): Verstappen wins Vegas F1 — sleek Red Bull royal-blue F1 car + yellow nose + Vegas neon + checkered flag
        draw.rectangle((0, 0, w, h), fill="#141828")
        # Neon Vegas strip horizon bars
        draw.rectangle((0, 14, w, 20), fill=BRIGHT_RED)
        draw.rectangle((0, 20, w, 24), fill=GOLD)
        # Lighter dark-slate asphalt track strip so the royal-blue Red Bull F1 pops crisply
        draw.rectangle((0, 42, w, h), fill="#2E3548")
        draw.rectangle((0, 42, w, 44), fill="#4E5870")
        # Bold checkered finish band on right edge
        sq = 8
        for r in range(6):
            for c in range(2):
                col = WARM_IVORY if (r + c) % 2 == 0 else "#141828"
                draw.rectangle((w - 18 + c * sq, 44 + r * sq, w - 18 + (c + 1) * sq, 44 + (r + 1) * sq), fill=col)
        # Sleek low-nose Red Bull Racing F1 car side profile streaking right
        cy_car = 68
        # Rear wing (royal blue + red endplate)
        draw.rectangle((8, cy_car - 20, 22, cy_car - 12), fill=BRIGHT_RED)
        draw.rectangle((14, cy_car - 12, 20, cy_car - 2), fill="#1E4B9E")
        # Long sleek royal-blue chassis + engine cover + low tapered nose
        draw.polygon([
            (14, cy_car - 4), (44, cy_car - 15), (68, cy_car - 11),
            (122, cy_car + 1), (124, cy_car + 7), (14, cy_car + 7),
        ], fill="#1E4B9E")
        # Signature Red Bull yellow airbox & nosecone tip
        draw.polygon([(46, cy_car - 15), (62, cy_car - 13), (66, cy_car - 5), (44, cy_car - 5)], fill=GOLD)
        draw.polygon([(106, cy_car - 2), (124, cy_car + 2), (124, cy_car + 7), (104, cy_car + 7)], fill=GOLD)
        # Red sidepod accent stripe
        draw.polygon([(38, cy_car - 3), (84, cy_car - 1), (82, cy_car + 4), (36, cy_car + 3)], fill=BRIGHT_RED)
        # Solid wide F1 tires with gold rims
        draw.ellipse((18, cy_car - 1, 38, cy_car + 19), fill="#0B0E18")
        draw.ellipse((24, cy_car + 5, 32, cy_car + 13), fill=GOLD)
        draw.ellipse((86, cy_car - 1, 106, cy_car + 19), fill="#0B0E18")
        draw.ellipse((92, cy_car + 5, 100, cy_car + 13), fill=GOLD)

    _draw_index_badge(draw, 0, 0, sid, accent, big=is_hero)
    canvas_img.paste(sub, (bx0, by0))


# ---------------------------------------------------------------------------
# 6. 5 Solid 2-Tone Brief Icons (18x18px, crisp at 300px, low edge noise)
# ---------------------------------------------------------------------------

def draw_brief_icon(
    draw: ImageDraw.ImageDraw,
    story: Story,
    box: Tuple[int, int, int, int],
    accent: str,
) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    draw.rounded_rectangle(box, radius=3, fill=ICON_BACKDROPS[story.region])

    sid = story.id
    if sid == 16:  # Lebanon Independence: solid green cedar + crimson base
        draw.polygon([(cx, y0 + 2), (x0 + 3, y1 - 5), (x1 - 3, y1 - 5)], fill="#2E6B40")
        draw.rectangle((cx - 1, y1 - 5, cx + 1, y1 - 2), fill=CRIMSON)
    elif sid == 17:  # S. Korea AI exam: crisp white exam paper + red X mark
        draw.rectangle((x0 + 3, y0 + 2, x1 - 3, y1 - 2), fill=WHITE, outline="#2C3E58", width=1)
        draw.line((x0 + 6, y0 + 6, x1 - 6, y1 - 6), fill=CRIMSON, width=2)
        draw.line((x1 - 6, y0 + 6, x0 + 6, y1 - 6), fill=CRIMSON, width=2)
    elif sid == 18:  # Nigeria boat capsize: tilted dark hull + solid teal wave
        draw.polygon([(x0 + 3, y0 + 9), (x1 - 3, y0 + 5), (x1 - 5, y0 + 11), (x0 + 5, y0 + 12)], fill=INK_DARK)
        draw.rectangle((x0 + 2, y1 - 5, x1 - 2, y1 - 2), fill="#286B78")
    elif sid == 19:  # PNG drought: warm gold sun + blue droplet
        draw.ellipse((x0 + 2, y0 + 2, x0 + 10, y0 + 10), fill=GOLD)
        draw.polygon([(cx + 3, y0 + 6), (x1 - 2, y1 - 4), (cx - 1, y1 - 4)], fill="#2B678A")
        draw.ellipse((cx - 1, y1 - 7, x1 - 2, y1 - 2), fill="#2B678A")
    elif sid == 20:  # WTO curbs: steel container + bold crimson bar
        draw.rectangle((x0 + 3, y0 + 5, x1 - 3, y1 - 4), fill="#3F5166")
        draw.line((x0 + 3, y1 - 4, x1 - 3, y0 + 5), fill=CRIMSON, width=3)


# ---------------------------------------------------------------------------
# 7. Band Renderers (Bands 1 to 8)
# ---------------------------------------------------------------------------

def draw_band1_topbar(
    draw: ImageDraw.ImageDraw,
    story_count: int,
    region_count: int,
    tracker: CollisionTracker,
) -> None:
    box = (0, 0, CANVAS_W, 16)
    draw.rectangle(box, fill=NAVY_BAR)
    tracker.add("bands", "band1_topbar", box)

    left_txt = "THE WORLD IN ONE DAY"
    right_txt = f"{story_count} STORIES · {region_count} REGIONS · EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    f_l, _, _, _ = fit(draw, left_txt, "sans_bold", 10, 8, 220, 14)
    f_r, _, _, _ = fit(draw, right_txt, "sans_bold", 9, 8, 740, 14)

    lb = draw_text_aligned(draw, (MARGIN_X, 0, 240, 16), left_txt, f_l, GOLD, align="left")
    rb = draw_text_aligned(draw, (240, 0, CANVAS_W - MARGIN_X, 16), right_txt, f_r, WHITE, align="right")
    tracker.add("band1_text", "left", lb)
    tracker.add("band1_text", "right", rb)


def draw_band2_masthead(draw: ImageDraw.ImageDraw, tracker: CollisionTracker) -> None:
    """Oversized crimson bold serif date masthead on open cream paper + single crisp rule."""
    title = "Sunday 22 November 2026"
    mast_box = (MARGIN_X, 18, CANVAS_W - MARGIN_X, 62)
    tracker.add("bands", "band2_masthead", mast_box)

    f_title, _, _, _ = fit(draw, title, "serif_bold", 54, 44, INNER_W - 40, 44)
    tb = draw_text_centered(draw, mast_box, title, f_title, CRIMSON)
    tracker.add("band2_text", "date_title", tb)

    draw.line((MARGIN_X, 65, CANVAS_W - MARGIN_X, 65), fill=CRIMSON, width=1)
    tracker.add("bands", "band2_rule", (MARGIN_X, 65, CANVAS_W - MARGIN_X, 66))


def draw_band3_kpi_strip(
    draw: ImageDraw.ImageDraw,
    kpis: Sequence[Tuple[str, str, int, str]],
    tracker: CollisionTracker,
) -> None:
    """Open, borderless 4-column KPI strip with 56px dark-navy serif numerals + 11px labels."""
    assert len(kpis) == 4
    y0, y1 = 68, 134
    tracker.add("bands", "band3_kpi", (MARGIN_X, y0, CANVAS_W - MARGIN_X, y1))

    cell_w = INNER_W / 4.0
    baseline_y = y0 + 42.0

    for idx, (val, label, _sid, _region) in enumerate(kpis):
        cx0 = MARGIN_X + idx * cell_w
        cx1 = MARGIN_X + (idx + 1) * cell_w
        if idx > 0:
            draw.line((cx0, y0 + 8, cx0, y1 - 8), fill=RULE_HAIRLINE, width=1)
        tracker.add("kpi_cells", f"kpi_{idx}", (cx0 + 1, y0, cx1 - 1, y1))

        f_val = get_font("serif_bold", 56)
        vw, _ = measure_text(draw, val, f_val)
        assert vw <= (cx1 - cx0) - 12, f"56px KPI {val!r} overflows cell width"
        vb = draw_text_baseline_centered(draw, cx0 + 4, cx1 - 4, baseline_y, val, f_val, NAVY_BAR)

        f_lbl, _, _, _ = fit(draw, label, "sans_bold", 11, 10, (cx1 - cx0) - 12, 14)
        lb = draw_text_centered(draw, (cx0 + 4, y0 + 47, cx1 - 4, y1 - 4), label, f_lbl, "#3C4452")

        tracker.add(f"kpi_inner_{idx}", "val", vb)
        tracker.add(f"kpi_inner_{idx}", "lbl", lb)


def draw_band4_region_bar(
    draw: ImageDraw.ImageDraw,
    counts: Counter,
    tracker: CollisionTracker,
) -> None:
    y0, y1 = 138, 154
    tracker.add("bands", "band4_regions", (MARGIN_X, y0, CANVAS_W - MARGIN_X, y1))
    total = sum(counts.values())

    raw = [counts[r] / total * INNER_W for r in REGION_ORDER]
    widths = [int(math.floor(v)) for v in raw]
    rem = INNER_W - sum(widths)
    for i in sorted(range(len(raw)), key=lambda idx: raw[idx] - widths[idx], reverse=True)[:rem]:
        widths[i] += 1

    cx = MARGIN_X
    for r, w in zip(REGION_ORDER, widths):
        seg_box = (cx, y0, cx + w, y1)
        draw.rectangle(seg_box, fill=REGION_COLORS[r])
        if cx > MARGIN_X:
            draw.line((cx, y0, cx, y1), fill=BG_PAPER, width=1)
        tracker.add("region_bar", r, (cx + 0.5, y0, cx + w - 0.5, y1))

        lbl = f"{r} {counts[r]}"
        f_r, _, _, _ = fit(draw, lbl, "sans_cond_bold", 10, 8, w - 6, 13)
        draw_text_centered(draw, seg_box, lbl, f_r, WHITE)
        cx += w


def draw_band5_utc_timeline(draw: ImageDraw.ImageDraw, tracker: CollisionTracker) -> None:
    """Clean single-line navy DAY IN UTC strip with 8 key timestamps."""
    y0, y1 = 158, 176
    bar_box = (MARGIN_X, y0, CANVAS_W - MARGIN_X, y1)
    draw.rectangle(bar_box, fill=NAVY_UTC)
    tracker.add("bands", "band5_utc", bar_box)

    lead_w = 80
    draw.rectangle((MARGIN_X, y0, MARGIN_X + 3, y1), fill=GOLD)
    f_t, _, _, _ = fit(draw, "DAY IN UTC", "sans_bold", 10, 8, lead_w - 8, 14)
    draw_text_centered(draw, (MARGIN_X + 4, y0, MARGIN_X + lead_w, y1), "DAY IN UTC", f_t, GOLD)
    draw.line((MARGIN_X + lead_w + 1, y0 + 3, MARGIN_X + lead_w + 1, y1 - 3), fill=NAVY_DIV, width=1)

    slots_x0 = MARGIN_X + lead_w + 4
    slots_w = (CANVAS_W - MARGIN_X) - slots_x0
    n = len(UTC_TIMELINE)
    slot_w = slots_w / n

    for idx, (tm, desc) in enumerate(UTC_TIMELINE):
        sx0 = slots_x0 + idx * slot_w
        sx1 = slots_x0 + (idx + 1) * slot_w
        if idx > 0:
            draw.line((sx0, y0 + 4, sx0, y1 - 4), fill=NAVY_DIV, width=1)
        tracker.add("utc_slots", f"utc_{idx}", (sx0 + 0.5, y0 + 0.5, sx1 - 0.5, y1 - 0.5))

        f_tm = get_font("mono_bold", 9)
        tm_w, _ = measure_text(draw, tm, f_tm)
        avail_desc = slot_w - tm_w - 10
        f_ds, _, ds_w, _ = fit(draw, desc, "sans_cond_bold", 9, 8, avail_desc, 13)

        total_w = tm_w + 4 + ds_w
        start_x = sx0 + (slot_w - total_w) / 2.0
        draw_text_aligned(draw, (start_x, y0, start_x + tm_w + 2, y1), tm, f_tm, GOLD, align="left")
        draw_text_aligned(draw, (start_x + tm_w + 4, y0, sx1 - 2, y1), desc, f_ds, WHITE, align="left")


def draw_band6_main_cards(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    card_stories: Sequence[Story],
    tracker: CollisionTracker,
) -> Tuple[int, int]:
    """
    Band 6 (y=188..824): 15 unboxed broadsheet cards in strict 3 cols x 5 rows.
    - Row 1 (#1-#3): 324x218px hero cards with 324x150px (height=150px, 68.8%) top art + text below.
    - Rows 2-5 (#4-#15): 324x94px featured cards with 150x92px (width=150px, 97.9% height) left art + right text.
    Returns (total_card_art_count, hero_art_height).
    """
    assert len(card_stories) == 15
    ncols = 3
    card_w = (INNER_W - (ncols - 1) * COL_GAP) // ncols  # 324 px
    assert card_w == 324

    art_count = 0

    # --- Row 1: 3 Hero Cards (y=188..406, h=218px, art=324x150px) ---
    hero_y0 = 188
    hero_art_h = 150
    hero_h = 218
    hero_y1 = hero_y0 + hero_h  # 406
    tracker.add("bands", "band6_hero_row", (MARGIN_X, hero_y0, CANVAS_W - MARGIN_X, hero_y1))

    for c_idx, s in enumerate(card_stories[:3]):
        x0 = MARGIN_X + c_idx * (card_w + COL_GAP)
        x1 = x0 + card_w
        accent = REGION_COLORS[s.region]

        tracker.add("cards", f"card_{s.id}", (x0, hero_y0, x1, hero_y1))

        art_box = (x0, hero_y0, x1, hero_y0 + hero_art_h)
        draw_card_illustration(img, s, art_box, accent, is_hero=True)
        art_count += 1
        tracker.add(f"card_{s.id}_inner", "art", art_box)

        # Text below art (y=342..406, h=64px, full 324px width)
        ty0 = hero_y0 + hero_art_h + 5  # 343
        f_hl, _, hl_lines, hl_lh = fit_multiline(
            draw, s.headline, "serif_bold", 20, 17, card_w - 2,
            max_lines=1, line_spacing=1.05, max_height=24,
        )
        hy = ty0
        hl_bot = hy
        for ln in hl_lines:
            tb = draw.textbbox((0, 0), ln, font=f_hl)
            draw.text((x0 - tb[0], hy - tb[1]), ln, font=f_hl, fill=INK_DARK)
            hl_bot = hy + (tb[3] - tb[1])
            hy += hl_lh
        tracker.add(f"card_{s.id}_inner", "headline", (x0, ty0, x1, hl_bot))

        ld_y0 = hl_bot + 4
        f_ld, _, ld_lines, ld_lh = fit_multiline(
            draw, s.lead, "sans_reg", 13, 11, card_w - 2,
            max_lines=2, line_spacing=1.15, max_height=31,
        )
        ly = ld_y0
        ld_bot = ly
        for ln in ld_lines:
            tb = draw.textbbox((0, 0), ln, font=f_ld)
            draw.text((x0 - tb[0], ly - tb[1]), ln, font=f_ld, fill=INK_BODY)
            ld_bot = ly + (tb[3] - tb[1])
            ly += ld_lh
        tracker.add(f"card_{s.id}_inner", "lead", (x0, ld_y0, x1, ld_bot))

        src_y0 = hero_y1 - 11
        src_txt = f"{s.region} · {s.location} · {s.source}"
        f_src, _, _, _ = fit(draw, src_txt, "sans_cond_bold", 9, 8, card_w - 2, 11)
        sb = draw_text_aligned(draw, (x0, src_y0, x1, hero_y1), src_txt, f_src, INK_MUTED, align="left")
        tracker.add(f"card_{s.id}_inner", "source", sb)

    # Subtle hairline divider between Hero Row 1 and Rows 2-5
    draw.line((MARGIN_X, hero_y1 + 6, CANVAS_W - MARGIN_X, hero_y1 + 6), fill=RULE_HAIRLINE, width=1)

    # --- Rows 2-5: 12 Featured Cards (y=418..824, 4 rows x 94px + 3 x 10px = 406px) ---
    grid_y0 = 418
    card_h = 94
    art_w = 150
    art_h = 92
    grid_y1 = grid_y0 + 4 * card_h + 3 * ROW_GAP  # 824
    tracker.add("bands", "band6_grid_rows", (MARGIN_X, grid_y0, CANVAS_W - MARGIN_X, grid_y1))

    for idx, s in enumerate(card_stories[3:]):
        r_idx = idx // ncols
        c_idx = idx % ncols
        x0 = MARGIN_X + c_idx * (card_w + COL_GAP)
        x1 = x0 + card_w
        y0 = grid_y0 + r_idx * (card_h + ROW_GAP)
        y1 = y0 + card_h
        accent = REGION_COLORS[s.region]

        if r_idx > 0 and c_idx == 0:
            draw.line((MARGIN_X, y0 - ROW_GAP // 2, CANVAS_W - MARGIN_X, y0 - ROW_GAP // 2), fill=RULE_SOFT, width=1)

        tracker.add("cards", f"card_{s.id}", (x0, y0, x1, y1))

        # Left 150x92px bold flat illustration (strictly clipped sub-canvas)
        art_box = (x0, y0 + 1, x0 + art_w, y0 + 1 + art_h)
        draw_card_illustration(img, s, art_box, accent, is_hero=False)
        art_count += 1
        tracker.add(f"card_{s.id}_inner", "art", art_box)

        # Right text column (160px wide with crisp 4px right breathing gutter)
        tx0 = art_box[2] + 10
        tx1 = x1 - 4
        tw = tx1 - tx0

        # 1) Headline: 18-20px bold serif (<=2 lines)
        try:
            f_hl, _, hl_lines, hl_lh = fit_multiline(
                draw, s.headline, "serif_bold", 20, 17, tw,
                max_lines=2, line_spacing=1.05, max_height=42,
            )
        except RuntimeError:
            f_hl, _, hl_lines, hl_lh = fit_multiline(
                draw, s.headline, "serif_cond_bold", 19, 16, tw,
                max_lines=2, line_spacing=1.05, max_height=42,
            )
        hy = y0 + 1
        hl_bot = hy
        for ln in hl_lines:
            tb = draw.textbbox((0, 0), ln, font=f_hl)
            draw.text((tx0 - tb[0], hy - tb[1]), ln, font=f_hl, fill=INK_DARK)
            hl_bot = hy + (tb[3] - tb[1])
            hy += hl_lh
        tracker.add(f"card_{s.id}_inner", "headline", (tx0, y0 + 1, tx1, hl_bot))

        # 2) Lead: 12-13px regular sans (<=2 lines)
        ld_y0 = max(hl_bot + 5, y0 + 44)
        f_ld, _, ld_lines, ld_lh = fit_multiline(
            draw, s.lead, "sans_reg", 13, 11, tw,
            max_lines=2, line_spacing=1.14, max_height=31,
        )
        ly = ld_y0
        ld_bot = ly
        for ln in ld_lines:
            tb = draw.textbbox((0, 0), ln, font=f_ld)
            draw.text((tx0 - tb[0], ly - tb[1]), ln, font=f_ld, fill=INK_BODY)
            ld_bot = ly + (tb[3] - tb[1])
            ly += ld_lh
        tracker.add(f"card_{s.id}_inner", "lead", (tx0, ld_y0, tx1, ld_bot))

        # 3) Source: 9px muted sans (1 line)
        src_y0 = y1 - 12
        src_txt = f"{s.location} · {s.source}"
        f_src, _, _, _ = fit(draw, src_txt, "sans_cond_bold", 9, 8, tw, 11)
        sb = draw_text_aligned(draw, (tx0, src_y0, tx1, y1), src_txt, f_src, INK_MUTED, align="left")
        tracker.add(f"card_{s.id}_inner", "source", sb)

    return art_count, hero_art_h


def draw_band7_map_and_briefs(
    draw: ImageDraw.ImageDraw,
    all_stories: Sequence[Story],
    brief_stories: Sequence[Story],
    tracker: CollisionTracker,
) -> Tuple[int, int]:
    """
    Band 7 (y=836..952, h=116):
      - Left: 300x116 minimalist world map with 10 key pins spanning all 7 regions.
      - Right: 684x116 clean single-column list of 5 briefs (#16-#20), each 1 line + 18x18 icon.
    """
    assert len(brief_stories) == 5
    y0, y1 = 836, 952
    tracker.add("bands", "band7_lower", (MARGIN_X, y0, CANVAS_W - MARGIN_X, y1))

    # --- Left World Map (x=14..314, w=300, h=116) ---
    mx0, mx1 = MARGIN_X, MARGIN_X + 300
    tracker.add("band7_panes", "map", (mx0, y0, mx1, y1))

    hdr_h = 14
    f_sec = get_font("sans_bold", 10)
    f_sub = get_font("sans_cond_reg", 9)
    draw_text_aligned(draw, (mx0, y0, mx0 + 160, y0 + hdr_h), "WHERE IT HAPPENED", f_sec, CRIMSON, align="left")
    draw_text_aligned(draw, (mx0 + 160, y0, mx1, y0 + hdr_h), "10 KEY LOCATIONS", f_sub, INK_MUTED, align="right")

    map_vp = (mx0, y0 + hdr_h + 2, mx1, y1)  # 300 x 100 px
    draw.rectangle(map_vp, fill=MAP_OCEAN)

    for reg, poly in WORLD_POLYGONS:
        pts = [project_lonlat(lon, lat, map_vp) for lon, lat in poly]
        draw.polygon(pts, fill=MAP_LAND_FILL[reg])

    mapped_stories = [s for s in all_stories if s.coords is not None]
    pin_r = 6.0
    resolved = resolve_map_pin_collisions(mapped_stories, map_vp, pin_radius=pin_r, min_gap=4.8)
    displaced = 0
    for s, (ax, ay), (px, py) in resolved:
        if math.hypot(px - ax, py - ay) > 2.5:
            displaced += 1
            draw.line((ax, ay, px, py), fill="#C8D7EC", width=1)
            draw.ellipse((ax - 1.5, ay - 1.5, ax + 1.5, ay + 1.5), fill=GOLD)

    f_pin = get_font("sans_bold", 8)
    for s, _, (px, py) in resolved:
        pbox = (px - pin_r, py - pin_r, px + pin_r, py + pin_r)
        draw.ellipse(pbox, fill=CRIMSON, outline=WHITE, width=1)
        draw_text_centered(draw, pbox, str(s.id), f_pin, WHITE)
        tracker.add("map_pins", f"pin_{s.id}", pbox)

    # --- Right 5 Single-Line Briefs (x=326..1010, w=684, h=116) ---
    bx0, bx1 = mx1 + SECTION_GAP, CANVAS_W - MARGIN_X
    tracker.add("band7_panes", "briefs", (bx0, y0, bx1, y1))

    draw_text_aligned(
        draw, (bx0, y0, bx0 + 420, y0 + hdr_h),
        "ALSO ON SUNDAY 22 NOVEMBER · 5 BRIEFS", f_sec, CRIMSON, align="left",
    )
    draw_text_aligned(
        draw, (bx1 - 220, y0, bx1, y0 + hdr_h),
        "STORIES #16–#20 · ALL VERIFIED", f_sub, INK_MUTED, align="right",
    )
    draw.line((bx0, y0 + hdr_h + 1, bx1, y0 + hdr_h + 1), fill=RULE_HAIRLINE, width=1)

    body_y0 = y0 + hdr_h + 2  # 852
    body_h = y1 - body_y0     # 100 px -> 20 px per brief
    row_h = body_h / 5.0

    icons_drawn = 0
    for idx, s in enumerate(brief_stories):
        ry0 = body_y0 + idx * row_h
        ry1 = ry0 + row_h
        accent = REGION_COLORS[s.region]

        if idx > 0:
            draw.line((bx0, ry0, bx1, ry0), fill=RULE_SOFT, width=1)
        tracker.add("brief_rows", f"brief_{s.id}", (bx0, ry0 + 0.5, bx1, ry1 - 0.5))

        # 18x18px solid 2-tone icon
        ic_y0 = int(round(ry0 + (row_h - 18) / 2.0))
        ic_box = (bx0, ic_y0, bx0 + 18, ic_y0 + 18)
        draw_brief_icon(draw, s, ic_box, accent)
        icons_drawn += 1

        tx = ic_box[2] + 8
        num_txt = f"{s.id}"
        f_num = get_font("sans_bold", 11)
        num_w, _ = measure_text(draw, num_txt, f_num)
        nb = draw_text_aligned(draw, (tx, ry0, tx + num_w + 4, ry1), num_txt, f_num, accent, align="left")

        hl_x = tx + num_w + 8
        f_hl = get_font("serif_bold", 13)
        hl_w, _ = measure_text(draw, s.headline, f_hl)
        hb = draw_text_aligned(draw, (hl_x, ry0, hl_x + hl_w + 4, ry1), s.headline, f_hl, INK_DARK, align="left")

        detail_x = hl_x + hl_w + 10
        detail_txt = f"— {s.location}: {s.lead} ({s.source})"
        f_dt, _, _, _ = fit(draw, detail_txt, "sans_reg", 11, 9, bx1 - detail_x, 15)
        db = draw_text_aligned(draw, (detail_x, ry0, bx1, ry1), detail_txt, f_dt, INK_MUTED, align="left")

        tracker.add(f"brief_inner_{s.id}", "icon", ic_box)
        tracker.add(f"brief_inner_{s.id}", "num", nb)
        tracker.add(f"brief_inner_{s.id}", "headline", hb)
        tracker.add(f"brief_inner_{s.id}", "detail", db)

    return icons_drawn, displaced


def draw_band8_quiet_bottom(draw: ImageDraw.ImageDraw, tracker: CollisionTracker) -> None:
    """
    Band 8 (y=964..1024):
      - DATE CHECK (y=964..992, 28px, <=2 lines, soft fill + 3px crimson left accent)
      - Open whitespace (y=992..1010, 18px)
      - Single-line footer (y=1010..1022, 12px)
    """
    dx0, dy0, dx1, dy1 = MARGIN_X, 964, CANVAS_W - MARGIN_X, 992
    dc_box = (dx0, dy0, dx1, dy1)
    draw.rectangle(dc_box, fill=DATE_CHECK_BG)
    draw.rectangle((dx0, dy0, dx0 + 3, dy1), fill=CRIMSON)
    tracker.add("bands", "band8_date_check", dc_box)

    p1 = "DATE CHECK — READ THIS FIRST"
    f_p1 = get_font("sans_bold", 9)
    p1w, _ = measure_text(draw, p1, f_p1)
    r1_b1 = draw_text_aligned(draw, (dx0 + 9, dy0 + 2, dx0 + 9 + p1w + 4, dy0 + 13), p1, f_p1, CRIMSON, align="left")

    c1 = "· Cutoff Sun 22 Nov 2026 23:59 UTC. Every story verified to this date; prior-day news excluded."
    f_c1, _, _, _ = fit(draw, c1, "sans_reg", 9, 8, dx1 - 8 - (r1_b1[2] + 4), 12)
    r1_b2 = draw_text_aligned(draw, (r1_b1[2] + 4, dy0 + 2, dx1 - 8, dy0 + 13), c1, f_c1, INK_DARK, align="left")
    tracker.add("band8_row1", "title", r1_b1)
    tracker.add("band8_row1", "cutoff", r1_b2)

    p2 = "EXCLUDED:"
    p2w, _ = measure_text(draw, p2, f_p1)
    r2_b1 = draw_text_aligned(draw, (dx0 + 9, dy0 + 15, dx0 + 9 + p2w + 4, dy1 - 2), p2, f_p1, CRIMSON, align="left")

    ex_txt = " · ".join(EXCLUDED_ITEMS)
    f_ex, _, _, _ = fit(draw, ex_txt, "sans_reg", 9, 8, dx1 - 8 - (r2_b1[2] + 4), 12)
    r2_b2 = draw_text_aligned(draw, (r2_b1[2] + 4, dy0 + 15, dx1 - 8, dy1 - 2), ex_txt, f_ex, INK_MUTED, align="left")
    tracker.add("band8_row2", "label", r2_b1)
    tracker.add("band8_row2", "items", r2_b2)

    # Pure open paper breathing room y=992..1009, then single-line editorial footer y=1010..1022
    fy0, fy1 = 1010, 1022
    draw.line((MARGIN_X, fy0 - 3, CANVAS_W - MARGIN_X, fy0 - 3), fill=RULE_HAIRLINE, width=1)
    foot_l = "SUNDAY 22 NOVEMBER 2026 · 20 VERIFIED STORIES · 7 REGIONS · 20 ORIGINAL ILLUSTRATIONS"
    foot_r = "PROGRAMMATICALLY RENDERED · PYTHON / PILLOW"
    f_fl, _, _, _ = fit(draw, foot_l, "sans_cond_bold", 9, 8, 660, 12)
    f_fr, _, _, _ = fit(draw, foot_r, "sans_cond_bold", 9, 8, 310, 12)
    flb = draw_text_aligned(draw, (MARGIN_X, fy0, MARGIN_X + 670, fy1), foot_l, f_fl, INK_MUTED, align="left")
    frb = draw_text_aligned(draw, (CANVAS_W - MARGIN_X - 320, fy0, CANVAS_W - MARGIN_X, fy1), foot_r, f_fr, INK_MUTED, align="right")
    tracker.add("bands", "band8_footer", (MARGIN_X, fy0, CANVAS_W - MARGIN_X, fy1))
    tracker.add("band8_foot_txt", "left", flb)
    tracker.add("band8_foot_txt", "right", frb)


# ---------------------------------------------------------------------------
# 8. Quantitative Self-Audit & Deterministic Pipeline
# ---------------------------------------------------------------------------

def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def measure_visual_metrics(img: Image.Image) -> Dict[str, object]:
    gray = img.convert("L")
    edges = np.array(gray.filter(ImageFilter.FIND_EDGES), dtype=np.float64)
    band_edges = [float(edges[i * 128:(i + 1) * 128].mean()) for i in range(8)]

    arr = np.array(img.convert("RGB"), dtype=np.float64)
    bg_rgb = np.array([248.0, 243.0, 233.0])
    non_paper = np.linalg.norm(arr - bg_rgb, axis=2) > 5.0

    blocks = arr.reshape(64, 16, 64, 16, 3)
    block_occ = (blocks.max(axis=(1, 3)) - blocks.min(axis=(1, 3))).max(axis=2) > 10.0

    return {
        "band_edges": [round(b, 2) for b in band_edges],
        "max_band_edge": round(max(band_edges), 2),
        "content_all_px": round(float(non_paper.mean()) * 100.0, 1),
        "content_top_px": round(float(non_paper[:512].mean()) * 100.0, 1),
        "content_bot_px": round(float(non_paper[512:].mean()) * 100.0, 1),
        "content_bot_blk16": round(float(block_occ[32:].mean()) * 100.0, 1),
    }


def build() -> None:
    region_counts = validate_dataset(STORIES)
    kpis = extract_verified_kpis(STORIES)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_PAPER)
    draw = ImageDraw.Draw(img)
    tracker = CollisionTracker(CANVAS_W, CANVAS_H)

    draw_band1_topbar(draw, len(STORIES), len(region_counts), tracker)
    draw_band2_masthead(draw, tracker)
    draw_band3_kpi_strip(draw, kpis, tracker)
    draw_band4_region_bar(draw, region_counts, tracker)
    draw_band5_utc_timeline(draw, tracker)
    main_art_count, hero_art_h = draw_band6_main_cards(img, draw, STORIES[:15], tracker)
    brief_icon_count, displaced = draw_band7_map_and_briefs(draw, STORIES, STORIES[15:20], tracker)
    draw_band8_quiet_bottom(draw, tracker)

    total_illustrations = main_art_count + brief_icon_count
    assert main_art_count == 15, f"Expected 15 main illustrations, got {main_art_count}"
    assert brief_icon_count == 5, f"Expected 5 brief icons, got {brief_icon_count}"
    assert total_illustrations >= 20, f"Expected >=20 illustrations, got {total_illustrations}"

    checked_pairs = tracker.assert_no_collisions()

    img.save(ENTRY_PATH, format="PNG", optimize=True, compress_level=9)
    size_bytes = ENTRY_PATH.stat().st_size
    assert img.size == (CANVAS_W, CANVAS_H), f"Bad size: {img.size}"
    assert size_bytes <= MAX_BYTES, f"entry.png exceeds 1 MiB: {size_bytes}"

    preview = img.resize((300, 300), Image.Resampling.LANCZOS)
    preview.save(PREVIEW_PATH, format="PNG", optimize=True, compress_level=9)

    metrics = measure_visual_metrics(img)
    digest = md5_file(ENTRY_PATH)

    print(f"OK | stories={len(STORIES)} | regions={dict((r, region_counts[r]) for r in REGION_ORDER)}")
    print(f"OK | kpis={[k[0] for k in kpis]}")
    print(f"OK | illustrations={total_illustrations} (main={main_art_count}, hero_h={hero_art_h}px, brief_icons={brief_icon_count})")
    print(f"OK | collision_boxes={tracker.total_registered} | checked_pairs={checked_pairs} | map_leaders={displaced}")
    print(f"OK | band_edges={metrics['band_edges']} | max={metrics['max_band_edge']}")
    print(
        f"OK | content_px: all={metrics['content_all_px']}% "
        f"top={metrics['content_top_px']}% bot={metrics['content_bot_px']}% "
        f"| bot_blk16={metrics['content_bot_blk16']}%"
    )
    print(f"OK | entry.png: {img.size[0]}x{img.size[1]}, {size_bytes:,} bytes (<= {MAX_BYTES:,}), md5={digest}")
    print(f"OK | preview-300.png: {preview.size[0]}x{preview.size[1]}, {PREVIEW_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    build()
