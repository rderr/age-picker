#!/usr/bin/env python3
"""Generate one SVG avatar per age (0..140) into ./avatars/.

Ages 0-110 draw a person who ages from baby to centenarian.
Ages 111-140 draw a corpse that decays into a skull and finally dust.

Run:  python3 generate-avatars.py
"""
import math
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatars")
MAX_AGE = 140
W = H = 240
CX = 120


# ---------- helpers ----------
def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(round(clamp(c, 0, 255))) for c in rgb)


def pw(age, stops):
    """Piecewise-linear interpolation. stops = [(age, value), ...] sorted by age.
    Values may be numbers or hex colors."""
    if age <= stops[0][0]:
        return stops[0][1]
    if age >= stops[-1][0]:
        return stops[-1][1]
    for (a0, v0), (a1, v1) in zip(stops, stops[1:]):
        if a0 <= age <= a1:
            t = (age - a0) / (a1 - a0) if a1 != a0 else 0
            if isinstance(v0, str):
                c0, c1 = hex_to_rgb(v0), hex_to_rgb(v1)
                return rgb_to_hex(tuple(lerp(x, y, t) for x, y in zip(c0, c1)))
            return lerp(v0, v1, t)
    return stops[-1][1]


def f(x):
    return ("%.2f" % x).rstrip("0").rstrip(".")


def darken(hexc, amt):
    """Darken by amt (0..1); a negative amt lightens toward white."""
    r, g, b = hex_to_rgb(hexc)
    if amt < 0:
        k = -amt
        return rgb_to_hex((r + (255 - r) * k, g + (255 - g) * k, b + (255 - b) * k))
    return rgb_to_hex((r * (1 - amt), g * (1 - amt), b * (1 - amt)))


# deterministic pseudo random (so holes/spots grow consistently between ages)
def prand(seed):
    x = math.sin(seed * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


# ---------- living person (0-110) ----------
def draw_person(age):
    parts = []
    # geometry
    rx = pw(age, [(0, 56), (3, 54), (18, 51), (70, 51), (110, 49)])
    ry = pw(age, [(0, 54), (3, 56), (18, 60), (70, 61), (110, 62)])
    cy = pw(age, [(0, 118), (6, 112), (18, 108), (110, 108)])
    shoulder = pw(age, [(0, 0.55), (6, 0.7), (16, 0.95), (25, 1.0), (85, 0.95), (110, 0.88)])
    stoop = pw(age, [(0, 0), (70, 0), (110, 10)])  # shoulders rise with age
    cy += stoop * 0.3

    skin = pw(age, [(0, "#fcd4c3"), (10, "#f8cba8"), (30, "#f1bf98"), (60, "#eabf9f"),
                    (90, "#e6cbb5"), (110, "#dccabd")])
    line = darken(skin, 0.42)
    hair_col = pw(age, [(0, "#5b3a21"), (36, "#5b3a21"), (58, "#a39e98"), (72, "#e4e2de"), (110, "#f4f4f2")])
    shirt = pw(age, [(0, "#b7dcc9"), (2, "#b7dcc9"), (4, "#f2b35b"), (12, "#f2b35b"), (15, "#3aa6a0"),
                     (38, "#3aa6a0"), (45, "#7a6b9c"), (62, "#7a6b9c"), (70, "#8a9a7b"), (110, "#8a9a7b")])
    bg = pw(age, [(0, "#eef3f8"), (110, "#ece9e4")])

    parts.append(f'<circle cx="{CX}" cy="{CX}" r="{CX}" fill="{bg}"/>')

    # body
    sw = 92 * shoulder
    top = 188 - stoop
    parts.append(
        f'<path d="M{f(CX - sw)} 240 C{f(CX - sw)} {f(top)} {f(CX - sw * 0.55)} {f(top - 8)} {CX} {f(top - 8)} '
        f'C{f(CX + sw * 0.55)} {f(top - 8)} {f(CX + sw)} {f(top)} {f(CX + sw)} 240 Z" fill="{shirt}"/>'
    )
    # neck
    nw = pw(age, [(0, 10), (18, 14), (110, 12)])
    parts.append(f'<rect x="{f(CX - nw)}" y="{f(cy + ry - 20)}" width="{f(nw * 2)}" height="{f(top - (cy + ry) + 24)}" '
                 f'fill="{darken(skin, 0.08)}"/>')

    # back hair (behind the head): an even, rounded cut that frames the face
    thin = pw(age, [(72, 1), (110, 0.5)])
    if age >= 1:
        bh_rx = rx + pw(age, [(1, 2), (3, 8), (10, 10), (70, 10), (110, 7)])
        bh_ry = ry * pw(age, [(1, 0.7), (3, 0.85), (110, 0.82)])
        parts.append(f'<ellipse cx="{CX}" cy="{f(cy - ry * 0.05)}" rx="{f(bh_rx)}" ry="{f(bh_ry)}" fill="{hair_col}" opacity="{f(thin)}"/>')
    # ears
    parts.append(f'<ellipse cx="{f(CX - rx - 2)}" cy="{f(cy + 4)}" rx="7" ry="11" fill="{skin}" stroke="{line}" stroke-width="0" />')
    parts.append(f'<ellipse cx="{f(CX + rx + 2)}" cy="{f(cy + 4)}" rx="7" ry="11" fill="{skin}"/>')

    # head
    parts.append(f'<clipPath id="head"><ellipse cx="{CX}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}"/></clipPath>')
    parts.append(f'<ellipse cx="{CX}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{skin}"/>')

    # jowls / sag (70+)
    jowl = clamp((age - 65) / 40)
    if jowl > 0:
        for s in (-1, 1):
            x0 = CX + s * rx * 0.75
            parts.append(f'<path d="M{f(x0)} {f(cy + ry * 0.45)} Q{f(x0 + s * 6)} {f(cy + ry * 0.75)} {f(x0 - s * 8)} {f(cy + ry * 0.85)}" '
                         f'fill="none" stroke="{line}" stroke-width="1.6" opacity="{f(jowl * 0.7)}"/>')

    # cheeks
    cheek = pw(age, [(0, 0.55), (10, 0.35), (25, 0)])
    if cheek > 0:
        for s in (-1, 1):
            parts.append(f'<circle cx="{f(CX + s * rx * 0.55)}" cy="{f(cy + ry * 0.28)}" r="{f(rx * 0.18)}" fill="#f28c8c" opacity="{f(cheek)}"/>')

    # eyes
    ey = cy - ry * 0.08
    ex = rx * 0.42
    ew = pw(age, [(0, 9), (12, 8), (30, 7), (110, 6)])
    eh = pw(age, [(0, 9), (12, 7.5), (30, 6.5), (80, 5.5), (110, 5)])
    pr = pw(age, [(0, 5), (12, 4.2), (30, 3.6), (110, 3.2)])
    iris = "#4a7fb5" if age < 2 else "#5c3f2a"
    droop = clamp((age - 55) / 55) * 0.5
    for s in (-1, 1):
        x = CX + s * ex
        parts.append(f'<ellipse cx="{f(x)}" cy="{f(ey)}" rx="{f(ew)}" ry="{f(eh)}" fill="#fff"/>')
        parts.append(f'<circle cx="{f(x)}" cy="{f(ey)}" r="{f(pr)}" fill="{iris}"/>')
        parts.append(f'<circle cx="{f(x)}" cy="{f(ey)}" r="{f(pr * 0.55)}" fill="#1a1a1a"/>')
        parts.append(f'<circle cx="{f(x - pr * 0.35)}" cy="{f(ey - pr * 0.35)}" r="{f(pr * 0.25)}" fill="#fff"/>')
        if droop > 0:  # upper eyelid
            parts.append(f'<path d="M{f(x - ew - 1)} {f(ey)} Q{f(x)} {f(ey - eh * (1 - droop * 2))} {f(x + ew + 1)} {f(ey)} '
                         f'L{f(x + ew + 1)} {f(ey - eh - 2)} L{f(x - ew - 1)} {f(ey - eh - 2)} Z" fill="{skin}"/>')
            parts.append(f'<path d="M{f(x - ew - 1)} {f(ey)} Q{f(x)} {f(ey - eh * (1 - droop * 2))} {f(x + ew + 1)} {f(ey)}" '
                         f'fill="none" stroke="{line}" stroke-width="1.2"/>')
        # eye bags
        bag = clamp((age - 40) / 50)
        if bag > 0:
            parts.append(f'<path d="M{f(x - ew * 0.9)} {f(ey + eh + 2)} Q{f(x)} {f(ey + eh + 6 + bag * 3)} {f(x + ew * 0.9)} {f(ey + eh + 2)}" '
                         f'fill="none" stroke="{line}" stroke-width="1.3" opacity="{f(bag * 0.8)}"/>')
        # crow's feet
        crow = clamp((age - 48) / 45)
        if crow > 0:
            ox = x + s * (ew + 4)
            for k, dy in enumerate((-4, 0, 4)):
                parts.append(f'<path d="M{f(ox)} {f(ey + dy * 0.4)} L{f(ox + s * 6)} {f(ey + dy)}" stroke="{line}" '
                             f'stroke-width="1.1" opacity="{f(crow * 0.8)}" stroke-linecap="round"/>')

    # eyebrows
    bw = pw(age, [(0, 1.2), (6, 1.8), (16, 2.3), (50, 2.5), (110, 2.6)])
    by = ey - eh - pw(age, [(0, 6), (18, 9), (110, 8)])
    brow_col = (hair_col if age < 50 else darken(hair_col, 0.35)) if age >= 2 else darken(skin, 0.25)
    for s in (-1, 1):
        x = CX + s * ex
        parts.append(f'<path d="M{f(x - ew)} {f(by + 1)} Q{f(x)} {f(by - 3)} {f(x + ew)} {f(by + 1)}" fill="none" '
                     f'stroke="{brow_col}" stroke-width="{f(bw)}" stroke-linecap="round"/>')

    # forehead lines
    fore = clamp((age - 38) / 45)
    if fore > 0:
        fy = by - 10
        for k in range(3):
            o = clamp(fore * 3 - k) * 0.7
            if o <= 0:
                continue
            w = rx * (0.42 - k * 0.06)
            yy = fy - k * 6
            parts.append(f'<path d="M{f(CX - w)} {f(yy + 2)} Q{CX} {f(yy - 2)} {f(CX + w)} {f(yy + 2)}" fill="none" '
                         f'stroke="{line}" stroke-width="1.2" opacity="{f(o)}"/>')

    # nose
    nl = pw(age, [(0, 5), (12, 9), (25, 13), (110, 16)])
    ny = ey + 4
    if age < 3:
        parts.append(f'<ellipse cx="{CX}" cy="{f(ny + nl)}" rx="3" ry="2" fill="{darken(skin, 0.15)}"/>')
    else:
        parts.append(f'<path d="M{f(CX + 1)} {f(ny)} Q{f(CX - 1)} {f(ny + nl)} {f(CX - 5)} {f(ny + nl)} '
                     f'Q{f(CX - 1)} {f(ny + nl + 4)} {f(CX + 4)} {f(ny + nl + 1)}" fill="none" stroke="{line}" '
                     f'stroke-width="{f(pw(age, [(3, 1.3), (60, 1.8)]))}" stroke-linecap="round"/>')

    # nasolabial lines
    naso = clamp((age - 42) / 45)
    my = cy + ry * 0.48
    if naso > 0:
        for s in (-1, 1):
            parts.append(f'<path d="M{f(CX + s * 7)} {f(ny + nl + 2)} Q{f(CX + s * 16)} {f(my - 6)} {f(CX + s * 15)} {f(my + 4)}" '
                         f'fill="none" stroke="{line}" stroke-width="1.4" opacity="{f(naso * 0.8)}"/>')

    # mouth
    mw = pw(age, [(0, 6), (2, 9), (12, 13), (25, 14), (90, 12), (110, 11)])
    curve = pw(age, [(0, 5), (12, 10), (30, 8), (70, 5), (100, 2), (110, 1)])
    if age < 2:
        # pacifier
        parts.append(f'<ellipse cx="{CX}" cy="{f(my + 2)}" rx="11" ry="8" fill="#6fb3e0"/>')
        parts.append(f'<circle cx="{CX}" cy="{f(my + 2)}" r="4" fill="#4a90c2"/>')
    else:
        parts.append(f'<path d="M{f(CX - mw)} {f(my)} Q{CX} {f(my + curve)} {f(CX + mw)} {f(my)}" fill="none" '
                     f'stroke="{darken(skin, 0.5)}" stroke-width="2" stroke-linecap="round"/>')
        if 4 <= age <= 45:
            # teeth/lip highlight
            parts.append(f'<path d="M{f(CX - mw * 0.7)} {f(my + 1)} Q{CX} {f(my + curve * 0.9)} {f(CX + mw * 0.7)} {f(my + 1)} Z" fill="#fff" opacity="0.9"/>')
    # chin line for old
    chin = clamp((age - 60) / 40)
    if chin > 0:
        parts.append(f'<path d="M{f(CX - 10)} {f(my + 14)} Q{CX} {f(my + 18)} {f(CX + 10)} {f(my + 14)}" fill="none" '
                     f'stroke="{line}" stroke-width="1.2" opacity="{f(chin * 0.7)}"/>')

    # age spots
    spot = clamp((age - 72) / 38)
    if spot > 0:
        n = int(spot * 9)
        for i in range(n):
            ax = CX + (prand(i * 3 + 1) - 0.5) * rx * 1.6
            ay = cy + (prand(i * 3 + 2) - 0.6) * ry * 1.4
            r = 1.2 + prand(i * 3 + 3) * 1.6
            parts.append(f'<circle cx="{f(ax)}" cy="{f(ay)}" r="{f(r)}" fill="{darken(skin, 0.3)}" opacity="0.75" clip-path="url(#head)"/>')

    # hair (front cap with a rounded hairline; thins evenly with age)
    if age < 1:
        for k, dx in enumerate((-8, 0, 8)):
            parts.append(f'<path d="M{f(CX + dx)} {f(cy - ry + 2)} q{f(dx * 0.4 + 2)} -10 {f(dx * 0.6 + 4)} -14" fill="none" '
                         f'stroke="{hair_col}" stroke-width="2.2" stroke-linecap="round"/>')
    else:
        hairline = cy - ry * pw(age, [(1, 0.5), (2, 0.58), (10, 0.62), (110, 0.62)])
        cap_rx = rx + pw(age, [(1, 1), (2, 5), (10, 6), (70, 6), (110, 4)])
        R = 120  # big circle gives a gently curved hairline, lower at the temples
        parts.append(f'<mask id="capmask"><rect width="{W}" height="{H}" fill="#fff"/>'
                     f'<circle cx="{CX}" cy="{f(hairline + R)}" r="{R}" fill="#000"/></mask>')
        parts.append(f'<ellipse cx="{CX}" cy="{f(cy - ry * 0.25)}" rx="{f(cap_rx)}" ry="{f(ry * 0.78 + 4)}" fill="{hair_col}" '
                     f'mask="url(#capmask)" opacity="{f(thin)}"/>')
        # soft parting highlight
        if age >= 3:
            parts.append(f'<path d="M{f(CX - 6)} {f(cy - ry - 2)} Q{f(CX - 2)} {f(cy - ry * 0.85)} {f(CX - 1)} {f(hairline - 2)}" '
                         f'fill="none" stroke="{darken(hair_col, -0.12) if age < 58 else darken(hair_col, 0.1)}" stroke-width="1.4" opacity="0.6"/>')

    # glasses (50+): light oval frames
    if age >= 50:
        grx, gry = ew + 5, eh + 4
        for s_ in (-1, 1):
            parts.append(f'<ellipse cx="{f(CX + s_ * ex)}" cy="{f(ey)}" rx="{f(grx)}" ry="{f(gry)}" fill="rgba(255,255,255,0.12)" stroke="#555" stroke-width="1.7"/>')
        parts.append(f'<path d="M{f(CX - ex + grx)} {f(ey)} Q{CX} {f(ey - 3)} {f(CX + ex - grx)} {f(ey)}" fill="none" stroke="#555" stroke-width="1.7"/>')
        parts.append(f'<path d="M{f(CX - ex - grx)} {f(ey)} L{f(CX - rx - 2)} {f(ey - 2)}" stroke="#555" stroke-width="1.7"/>')
        parts.append(f'<path d="M{f(CX + ex + grx)} {f(ey)} L{f(CX + rx + 2)} {f(ey - 2)}" stroke="#555" stroke-width="1.7"/>')

    return parts


# ---------- corpse (111-140) ----------
def draw_corpse(age):
    parts = []
    d = clamp((age - 110) / 30)          # 0..1 total decay
    fresh = clamp((age - 110) / 10)      # 111-120 fresh corpse stage
    rot = clamp((age - 120) / 10)        # 121-130 skin falling away
    bone = clamp((age - 130) / 7)        # 131-137 skull cracks
    dust = clamp((age - 136) / 4)        # 137-140 crumbles to dust

    bg = pw(age, [(111, "#e6e2db"), (125, "#d6d0c6"), (140, "#bdb5a8")])
    parts.append(f'<circle cx="{CX}" cy="{CX}" r="{CX}" fill="{bg}"/>')

    skin = pw(age, [(111, "#c9cdb6"), (118, "#aab39a"), (130, "#8b9479")])
    line = darken(skin, 0.45)
    bone_col = pw(age, [(120, "#efe9da"), (140, "#d9d0bb")])
    bone_line = "#9c9078"
    shirt = pw(age, [(111, "#7a6652"), (125, "#6a5c4d"), (140, "#5a5047")])

    # head tilt
    tilt = pw(age, [(111, 4), (120, 9), (130, 12), (140, 12)])
    cy = 110
    rx, ry = 48, 62

    body_opacity = 1 - dust
    skull_remaining = 1 - dust  # fraction of skull left

    # ---------- body ----------
    body = []
    top = 190
    sw = 80
    shirt_d = (f'M{CX - sw} 240 C{CX - sw} {top} {f(CX - sw * 0.55)} {top - 8} {CX} {top - 8} '
               f'C{f(CX + sw * 0.55)} {top - 8} {CX + sw} {top} {CX + sw} 240 Z')
    if rot > 0:
        # dark cavity, then ribs + spine, show through holes in the shirt
        body.append(f'<path d="{shirt_d}" fill="#2f2823"/>')
        for k in range(4):
            yy = top + 6 + k * 10
            body.append(f'<path d="M{CX - 34} {yy + 6} Q{CX} {yy - 4} {CX + 34} {yy + 6}" fill="none" stroke="{bone_col}" stroke-width="4"/>')
        body.append(f'<rect x="{CX - 3}" y="{top - 6}" width="6" height="60" fill="{bone_col}"/>')
        body.append('<mask id="shirtmask"><rect width="240" height="240" fill="#fff"/>')
        for i in range(6):
            hx = CX + (prand(50 + i) - 0.5) * 130
            hy = top + 10 + prand(60 + i) * 40
            body.append(f'<circle cx="{f(hx)}" cy="{f(hy)}" r="{f(3 + 12 * rot * prand(70 + i) + 8 * bone)}" fill="#000"/>')
        body.append('</mask>')
        body.append(f'<path d="{shirt_d}" fill="{shirt}" mask="url(#shirtmask)"/>')
    else:
        body.append(f'<path d="{shirt_d}" fill="{shirt}"/>')
    # neck
    neck = (f'<rect x="{CX - 12}" y="{cy + ry - 20}" width="24" height="{top - (cy + ry) + 24}" fill="{darken(skin, 0.1)}" opacity="{f(1 - rot)}"/>'
            f'<rect x="{CX - 5}" y="{cy + ry - 20}" width="10" height="{top - (cy + ry) + 24}" fill="{bone_col}" opacity="{f(rot)}"/>')
    parts.append(f'<g opacity="{f(body_opacity)}">{neck}{"".join(body)}</g>')

    # ---------- head group ----------
    head = []
    # skull (always drawn under the skin)
    srx, sry = 44, 46
    scy = cy - 8
    head.append(f'<ellipse cx="{CX}" cy="{f(scy)}" rx="{srx}" ry="{sry}" fill="{bone_col}" stroke="{bone_line}" stroke-width="1.5"/>')
    # cheekbones + jaw
    jaw_drop = pw(age, [(128, 0), (135, 10), (140, 14)])
    head.append(f'<path d="M{CX - 34} {scy + 24} L{CX - 30} {scy + 46} Q{CX} {scy + 62} {CX + 30} {scy + 46} L{CX + 34} {scy + 24} Z" '
                f'fill="{bone_col}" stroke="{bone_line}" stroke-width="1.5"/>')
    # eye sockets
    for s in (-1, 1):
        head.append(f'<ellipse cx="{CX + s * 17}" cy="{scy + 2}" rx="11" ry="12" fill="#2a2520"/>')
    # nasal cavity
    head.append(f'<path d="M{CX} {scy + 14} L{CX - 5} {scy + 28} L{CX + 5} {scy + 28} Z" fill="#2a2520"/>')
    # upper teeth
    for i in range(-3, 4):
        head.append(f'<rect x="{CX + i * 6 - 2.5}" y="{scy + 42}" width="5" height="7" rx="1" fill="#f7f3e8" stroke="{bone_line}" stroke-width="0.8"/>')
    # jaw (separate, drops with decay)
    jaw = []
    jaw.append(f'<path d="M{CX - 30} {scy + 46} Q{CX} {scy + 70} {CX + 30} {scy + 46} L{CX + 28} {scy + 50} Q{CX} {scy + 64} {CX - 28} {scy + 50} Z" '
               f'fill="{bone_col}" stroke="{bone_line}" stroke-width="1.5"/>')
    for i in range(-3, 4):
        jaw.append(f'<rect x="{CX + i * 6 - 2.5}" y="{scy + 48}" width="5" height="6" rx="1" fill="#f7f3e8" stroke="{bone_line}" stroke-width="0.8"/>')
    head.append(f'<g transform="translate(0 {f(jaw_drop)})">{"".join(jaw)}</g>')
    # cracks
    if bone > 0:
        cr = [
            f'M{CX - 10} {scy - 44} l4 10 l-5 8 l6 9',
            f'M{CX + 24} {scy - 30} l-6 8 l5 9',
            f'M{CX - 36} {scy + 10} l8 4 l-3 8',
        ]
        for i, p in enumerate(cr):
            o = clamp(bone * 3 - i)
            head.append(f'<path d="{p}" fill="none" stroke="{bone_line}" stroke-width="1.6" stroke-linecap="round" opacity="{f(o)}"/>')
    # missing skull pieces (dust phase)
    if dust > 0:
        head.append('<mask id="skullmask"><rect width="240" height="240" fill="#fff"/>')
        for i in range(10):
            hx = CX + (prand(100 + i) - 0.5) * 110
            hy = scy + (prand(110 + i) - 0.5) * 120
            r = 4 + 36 * dust * (0.4 + prand(120 + i))
            head.append(f'<circle cx="{f(hx)}" cy="{f(hy)}" r="{f(r)}" fill="#000"/>')
        head.append('</mask>')
    skull_markup = "".join(head)
    if dust > 0:
        # wrap all skull markup (minus the mask itself) in masked group
        mask_start = skull_markup.index('<mask id="skullmask">')
        mask_markup = skull_markup[mask_start:]
        skull_markup = f'{mask_markup}<g mask="url(#skullmask)">{skull_markup[:mask_start]}</g>'

    # skin layer over the skull (fresh corpse), with holes during rot
    skin_layer = []
    if rot < 1:
        skin_layer.append(f'<ellipse cx="{CX}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{skin}"/>')
        # ears
        skin_layer.append(f'<ellipse cx="{CX - rx - 2}" cy="{cy + 4}" rx="7" ry="11" fill="{skin}"/>')
        skin_layer.append(f'<ellipse cx="{CX + rx + 2}" cy="{cy + 4}" rx="7" ry="11" fill="{skin}"/>')
        # sunken cheeks shading
        for s in (-1, 1):
            skin_layer.append(f'<ellipse cx="{CX + s * 26}" cy="{cy + 18}" rx="12" ry="9" fill="{darken(skin, 0.18)}" opacity="{f(0.4 + fresh * 0.5)}"/>')
        # eyes: X marks
        ey, ex = cy - 6, 20
        for s in (-1, 1):
            x = CX + s * ex
            skin_layer.append(f'<path d="M{x - 7} {ey - 7} L{x + 7} {ey + 7} M{x + 7} {ey - 7} L{x - 7} {ey + 7}" stroke="#2b2b2b" stroke-width="3" stroke-linecap="round"/>')
            # eyebrows (sad angle)
            skin_layer.append(f'<path d="M{x - 9} {ey - 13 + (3 if s < 0 else 0)} L{x + 9} {ey - 13 + (0 if s < 0 else 3)}" stroke="#777" stroke-width="3" stroke-linecap="round"/>')
        # nose
        skin_layer.append(f'<path d="M{CX + 1} {ey + 2} Q{CX - 1} {ey + 16} {CX - 5} {ey + 16} Q{CX - 1} {ey + 20} {CX + 4} {ey + 17}" fill="none" stroke="{line}" stroke-width="1.8" stroke-linecap="round"/>')
        # mouth: open, slack
        my = cy + 30
        skin_layer.append(f'<path d="M{CX - 13} {my} Q{CX} {my + 2 + fresh * 10} {CX + 13} {my} Q{CX} {my + 1} {CX - 13} {my} Z" fill="#3a2a2a"/>')
        # a few white hair wisps remaining
        for k, dx in enumerate((-30, -18, 22, 32)):
            skin_layer.append(f'<path d="M{CX + dx} {cy - ry + 6} q{dx * 0.2} -8 {dx * 0.3} -12" fill="none" stroke="#eee" stroke-width="2" stroke-linecap="round" opacity="{f(1 - fresh * 0.8)}"/>')
        # wrinkles
        for k in range(2):
            yy = cy - 40 - k * 6
            skin_layer.append(f'<path d="M{CX - 18} {yy + 2} Q{CX} {yy - 2} {CX + 18} {yy + 2}" fill="none" stroke="{line}" stroke-width="1.2" opacity="0.7"/>')
        # mottling / dark patches
        n = int(2 + fresh * 6)
        for i in range(n):
            ax = CX + (prand(200 + i) - 0.5) * 70
            ay = cy + (prand(210 + i) - 0.5) * 90
            skin_layer.append(f'<circle cx="{f(ax)}" cy="{f(ay)}" r="{f(2 + prand(220 + i) * 5)}" fill="{darken(skin, 0.3)}" opacity="0.55"/>')
        skin_markup = "".join(skin_layer)
        if rot > 0:
            holes = ['<mask id="skinmask"><rect width="240" height="240" fill="#fff"/>']
            for i in range(9):
                hx = CX + (prand(300 + i) - 0.5) * 100
                hy = cy + (prand(310 + i) - 0.5) * 120
                r = 2 + 34 * rot * (0.5 + prand(320 + i))
                holes.append(f'<circle cx="{f(hx)}" cy="{f(hy)}" r="{f(r)}" fill="#000"/>')
            holes.append('</mask>')
            skin_markup = f'{"".join(holes)}<g mask="url(#skinmask)">{skin_markup}</g>'
    else:
        skin_markup = ""

    parts.append(f'<g transform="rotate({f(tilt)} {CX} {cy + ry})">{skull_markup}{skin_markup}</g>')

    # flies (113-130)
    fly = clamp((age - 112) / 3) * clamp((131 - age) / 4)
    if fly > 0:
        for i, (fx, fy) in enumerate(((52, 70), (182, 54), (176, 150))):
            head_fly = (f'<g opacity="{f(fly)}"><circle cx="{fx}" cy="{fy}" r="2.4" fill="#222"/>'
                        f'<path d="M{fx - 2} {fy - 2} q-4 -4 -6 -1 M{fx + 2} {fy - 2} q4 -4 6 -1" fill="none" stroke="#555" stroke-width="1"/>'
                        f'<path d="M{fx + 4} {fy + 2} q5 3 2 7 q-4 3 -3 7" fill="none" stroke="#777" stroke-width="0.8" stroke-dasharray="1.5 1.5"/></g>')
            parts.append(head_fly)

    # dust pile (137-140)
    if dust > 0:
        ph = 10 + 50 * dust
        pw_ = 60 + 60 * dust
        parts.append(f'<path d="M{f(CX - pw_)} 240 Q{CX} {f(240 - ph * 2)} {f(CX + pw_)} 240 Z" fill="#a89f8c"/>')
        parts.append(f'<path d="M{f(CX - pw_ * 0.6)} 240 Q{f(CX + 10)} {f(240 - ph * 1.4)} {f(CX + pw_ * 0.7)} 240 Z" fill="#978d7a" opacity="0.8"/>')
        # a bone fragment or two sticking out
        sy = 240 - ph * 1.55
        parts.append(f'<g opacity="{f(dust)}"><rect x="{CX - 30}" y="{f(sy)}" width="28" height="6" rx="3" fill="{bone_col}" stroke="{bone_line}" stroke-width="1" transform="rotate(-14 {CX - 16} {f(sy)})"/>'
                     f'<circle cx="{CX + 24}" cy="{f(sy + 2)}" r="7" fill="{bone_col}" stroke="{bone_line}" stroke-width="1"/>'
                     f'<circle cx="{CX + 22}" cy="{f(sy + 1)}" r="2" fill="#2a2520"/>'
                     f'<circle cx="{CX + 28}" cy="{f(sy + 1)}" r="1.5" fill="#2a2520"/></g>')
        # dust motes
        for i in range(int(dust * 12)):
            mx = CX + (prand(400 + i) - 0.5) * 160
            myy = 240 - ph * 2 - prand(410 + i) * 90
            parts.append(f'<circle cx="{f(mx)}" cy="{f(myy)}" r="{f(1 + prand(420 + i) * 1.5)}" fill="#8f8572" opacity="{f(0.3 + prand(430 + i) * 0.5)}"/>')

    return parts


def svg_for(age):
    parts = draw_person(age) if age <= 110 else draw_corpse(age)
    body = "\n  ".join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="Avatar, age {age}">\n  {body}\n</svg>\n')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for age in range(0, MAX_AGE + 1):
        with open(os.path.join(OUT_DIR, f"age-{age:03d}.svg"), "w") as fh:
            fh.write(svg_for(age))
    print(f"wrote {MAX_AGE + 1} avatars to {OUT_DIR}")


if __name__ == "__main__":
    main()
