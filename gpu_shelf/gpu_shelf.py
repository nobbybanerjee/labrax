"""3U Lab Rax shelf for the EVGA RTX 3090 Ti FTW3 Ultra (24G-P5-4985-KR).

CadQuery source of truth -> print/*.stl -> checks -> print/*.png, in one run:

    python gpu_shelf.py

Frame (mm): X across the rack (0 = centre, + = right seen from the front),
Y depth (0 = front face of the front posts, + toward the rear), Z up
(0 = bottom of the 3U block). The card lies flat, fans DOWN, I/O bracket
against the faceplate, 16-pin out the rear end.

Card envelope from TechPowerUp (300 x 140 mm, 2157 g, takes 4 slots) and the
PCB photo (PCIe fingers on the left when fans are down, 16-pin on the END near
the right-hand edge). Rack from the-diy-life Lab Rax spec: M6, 236.525 hole
spacing, 222 clear, 44.45 per U. Frame depth from the Lab Rax planner's own part
models (ref/rail-height-3u.stl, ref/rail-depth.stl): L-section posts 30 x 35 with a
6 mm hole flange, 170 mm depth rail -> 240 mm outside, rear flange inner face at 234.
"""
import math
import os
import struct
import sys

import cadquery as cq
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "print")

# ---- rack ----
U = 44.45
UNITS = 3
HOLE_X = 236.525 / 2
CLEAR_X = 222.0 / 2
POST_W, POST_D = 30.0, 35.0  # L-section post, measured from the Lab Rax part model
FLANGE_T, WEB_T = 6.0, 6.5   # hole flange (front/back face) and side web
RACK_OUT = 2 * POST_D + 170.0              # 240: front face to back face of the frame
RACK_D = RACK_OUT - FLANGE_T               # 234: inner face of the rear flange = rear ear seat
EIA = (6.35, 22.225, 38.1)   # hole centres within each U
FIT = 0.4                    # extra clearance per side on every mating feature: PETG prints ~0.5 mm off
M6_SLOT = (9.0 + 2 * FIT, 6.6 + 2 * FIT)   # slot length (x) x width

# ---- card (fans down) ----
CARD_L, CARD_W, CARD_T = 300.0, 127.0, 81.3   # W: real shroud is 126.5 from the finger edge
CARD_X0 = -21.5              # shroud finger-side edge: card pushed right until the right rear ear (x 106.5) is the limit
FINGER_OUT = 6.0             # PCIe fingers stand proud of the shroud edge
PLUG = dict(x=(55.0, 95.0), y=(CARD_L, CARD_L + 35.0), z=(60.0, 0.0))  # z top set below
CLR = 0.5

# ---- shelf ----
SHELF_Z0 = 0.4               # same 0.4 mm relief as the faceplate bottom
SHELF_T = 5.0
SHELF_HALF = CLEAR_X - 0.5
SHELF_L = CARD_L + 6.0
EAR_T = 5.0                  # rear ear plate, on the OUTER face of the rear posts
STANDOFF = 20.0
RIM_H, RIM_T = 14.0, 4.0
CARD_Z0 = SHELF_Z0 + SHELF_T + STANDOFF
CARD_Z1 = CARD_Z0 + CARD_T
PLUG["z"] = (CARD_Z1 - 45.0, CARD_Z1)

# ---- faceplate ----
FP_T = 5.0
FP_H = UNITS * U - 0.8 - 2 * FIT   # gap to the neighbouring units
FP_HALF = 126.5
# ---- the real card (fans down, so the PCB edge -- and the ports -- are at the TOP) ----
# From GrabCAD's EVGA RTX 3090 FTW3 IGES (ref/card/), placed by card_model.py with only its
# thickness stretched 3.5/2.75 slots to the Ti. Bracket length checks against Keystone's PCI
# drawing (ref/bracket/m65p122.pdf): 120 overall, 112.8 body, 11.5 tab, 4.4 hole, 10.2 tongue.
# CARD_T above stays the 4-slot CLEARANCE envelope; these are where the parts really are.
CARD_T_REAL = 66.2                       # 52.0 raw x 3.5/2.75
CARD_Z1_REAL = CARD_Z0 + CARD_T_REAL     # backplate top
PCB_Z = CARD_Z1_REAL - 5.5               # PCB mid-plane, 5.5 below the backplate top
BR_T = 0.9
BR_W = 18.42 + 2 * 20.32                 # Ti FTW3: 3-slot bracket (the 2.75-slot FTW3 uses a 2-slot)
BR_Z1 = CARD_Z1_REAL - 2.5               # PCB-side edge of the bracket
BR_Z0 = BR_Z1 - BR_W
BR_FL_X = 56.9                           # tab bend (IGES); tab folds OUTWARD, toward the front
BR_FL_L = 11.6
BR_TAB_T = 1.7                           # tab incl. its bend radius, measured on the IGES (sheet is 0.9)
BR_LEN, BR_BODY = 119.3, 112.8           # tongue tip at -62.4 in the IGES
BR_TONGUE = (BR_FL_X - BR_LEN, BR_FL_X - BR_BODY)
BR_TONGUE_W, BR_TONGUE_OFF = 10.2, 2.6
TONGUE_Z = (BR_Z1 - BR_TONGUE_OFF - BR_TONGUE_W, BR_Z1 - BR_TONGUE_OFF)
BR_FL_HOLE_D, BR_FL_HOLE_Y = 4.4, -6.0          # tab screw holes, 6 mm in front of the bracket face
# port openings measured in the IGES bracket: (x centre, w, h) -- HDMI nearest the fingers, 3x DP
PORT_CUTS = [(-24.7, 15.2, 6.0), (-4.65, 17.3, 6.0), (16.45, 17.3, 6.0), (37.55, 17.3, 6.0)]
PORT_ZC = CARD_Z1_REAL - 9.3             # 6.3..12.3 below the backplate top
# ---- override with landmarks measured on the detailed Ti model (card_ti.py) ----
_LM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "print", "card_landmarks.json")
if os.path.exists(_LM):
    import json as _json
    _L = _json.load(open(_LM))
    CARD_L = _L["tail_y"]                                   # 287.6: bracket face to shroud tail
    CARD_T_REAL = _L["card_top_z"] - CARD_Z0
    CARD_Z1_REAL = _L["card_top_z"]
    PCB_Z = _L["pcb_z"]
    BR_Z0, BR_Z1 = _L["bracket"]["z"]
    BR_W = BR_Z1 - BR_Z0
    BR_FL_X = _L["tab"]["x"][0]
    BR_TAB_T = _L["tab"]["x"][1] - _L["tab"]["x"][0]
    BR_FL_L = -_L["tab"]["y_min"]
    if "tongue" in _L:                                      # absent until card_ti.py has run once
        BR_TONGUE = tuple(_L["tongue"]["x"])
        TONGUE_Z = tuple(_L["tongue"]["z"])
    BR_FL_HOLE_Y = _L["tab_holes_yz"][0][0]
    PORT_CUTS = [((p_["x"][0] + p_["x"][1]) / 2, p_["x"][1] - p_["x"][0], p_["z"][1] - p_["z"][0]) for p_ in _L["ports"]]
    PORT_ZC = sum((p_["z"][0] + p_["z"][1]) / 2 for p_ in _L["ports"]) / len(_L["ports"])
    _S = _L["sixteen_pin"]
    PLUG = dict(x=(_S["x"][0] - 3.0, _S["x"][1] + 3.0), y=(_S["y"][1], _S["y"][1] + 35.0),
                z=(_S["z"][0] - 3.0, _S["z"][1] + 3.0))
    SHELF_L = CARD_L + 6.0
SHROUD_SET = 6.0                         # shroud starts this far behind the bracket face
# cable zone in front of the ports: each opening + 6 mm round for the plug overmold
# Test print 1 (2026-10-06): the window edge sat flush on the PCB side of every port, so no plug
# went in. Rev 3b: nabaru wants no see-through sliver, so the window edge sits on the bracket's
# PCB-side edge (WIN adds 1.0 + FIT back on). Below test print 1's 90.6 -- plugs may not fit.
PORTS = dict(x=(PORT_CUTS[0][0] - PORT_CUTS[0][1] / 2 - 6.0, PORT_CUTS[-1][0] + PORT_CUTS[-1][1] / 2 + 6.0),
             z=(PORT_ZC - 3.0 - 6.0, BR_Z1 - 1.0 - FIT))
# faceplate opening: whole bracket face less a 2 mm lip it bears on, so the ports are fully open
# Window clears the cable zone (plug overmolds stand ~1 mm above the bracket's PCB edge), so the
# bracket bears on the faceplate along its bottom and finger-side borders, plus the tab screws.
WIN = dict(x=(PORTS["x"][0] - 1.0, BR_FL_X - 0.4), z=(BR_Z0 + 2.0, PORTS["z"][1] + 1.0))
FL_POST_W = 10.0
# tab screw holes: exactly the ones measured on the model's tab (the Ti's 2-slot bracket has one)
FL_SCREW_Z = ([h[1] for h in _L["tab_holes_yz"]] if os.path.exists(_LM)
              else [BR_Z0 + 18.42 / 2 + i * 20.32 for i in (0, 1)])
# Test print 1: the bent tab reaches ~5 mm past the shroud-side end of the bracket and had to be
# cut free there, so the slot gets that much more length (width was fine). Rev 3: +6 mm at the
# top (PCB-side) end as well, at nabaru's request.
NOTCH_EXTRA_Z0, NOTCH_EXTRA_Z1, NOTCH_EXTRA_W = 6.0, 6.0, 0.0
# Test print 1: a screw driven into the plate from behind, its head clamping the bracket's tongue
# end. The plate stays solid round it (no honeycomb) so a self-tapper bites; no hole is modelled.
TONGUE_SCREW = (BR_TONGUE[0] - 1.8, (TONGUE_Z[0] + TONGUE_Z[1]) / 2)
TONGUE_PAD_R = 9.0
LIP_D, LIP_H = 8.0, 16.0
LIP_SCREWS_X = (-90.0, -30.0, 30.0, 90.0)
LIP_SCREW_Z = SHELF_Z0 + SHELF_T + 5.5

HEX_D, HEX_WALL = 11.0, 2.4    # corner-to-corner, web

# ---- riser wall (left of the card, where the PCIe fingers point) ----
RISER_X = CARD_X0 - FINGER_OUT - 22.0 - 4.0   # 22 mm for the riser's slot + board
RISER_T = 4.0
RISER_Y = (40.0, 150.0)
RISER_Z1 = PCB_Z + 16.0
# Riser slot, with ~5 mm extra all round for the ribbon, its connector and print tolerance. The +x
# end stops 2 mm short of the PCB edge so it keeps clear of the front-left pad's lip (x -17.7).
RISER_SLIT_X = (RISER_X - 5.0, CARD_X0 + 2.0)   # bay side to 2 mm past the PCB edge: open under the fingers
RISER_SLIT_Y = (40.0, 150.0)              # fingers run y 50..139; ribbons are ~65-75 mm wide
# real shroud footprint, measured on the detailed Ti mesh (CARD_X0/CARD_W stay the clearance box)
SHROUD_X = (-14.2, 103.7)
PAD_STEP, PAD_GAP = 0.75, 0.2             # pad profile sampling step; air left under the shroud


def shroud_underside():
    """(x, y) -> lowest z of the detailed Ti mesh (GrabCAD-derived) straight above that point.
    Not the photo-built STEP: its shroud bottom is one flat face at the card's lowest point."""
    paths = [p for p in [os.path.join(OUT, "_ref_card_3090ti.stl")] if os.path.exists(p)]
    if not paths:
        return lambda x, y: math.inf
    T = np.concatenate([read_stl(p).reshape(-1, 3, 3) for p in paths])
    T = T[T[:, :, 2].min(1) < CARD_Z0 + 40.0]            # underside features only
    bx0, bx1, by0, by1 = T[:, :, 0].min(1), T[:, :, 0].max(1), T[:, :, 1].min(1), T[:, :, 1].max(1)

    def f(px, py):
        t = T[(bx0 <= px) & (bx1 >= px) & (by0 <= py) & (by1 >= py)]
        if not len(t):
            return math.inf
        a, b, c = t[:, 0], t[:, 1], t[:, 2]
        v0, v1 = b[:, :2] - a[:, :2], c[:, :2] - a[:, :2]
        v2 = np.array([px, py]) - a[:, :2]
        d = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
        ok = np.abs(d) > 1e-12
        d = np.where(ok, d, 1.0)
        u = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / d
        w = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / d
        inside = ok & (u >= -1e-6) & (w >= -1e-6) & (u + w <= 1 + 1e-6)
        if not inside.any():
            return math.inf
        z = a[:, 2] + u * (b[:, 2] - a[:, 2]) + w * (c[:, 2] - a[:, 2])
        return float(z[inside].min())
    return f


def smooth_pad(x_edge, sx, yc, top, under, size=12.0, depth=12.0):
    """Flat-topped card pad just inside the real shroud edge (no locating lip since rev 3c).
    Its height is sampled off the detailed Ti mesh's underside over the whole pad footprint."""
    flat, inside = top + STANDOFF, -sx                    # +1 means card material lies at larger x
    xc = x_edge - sx * (size / 2 + 1.0)                   # pad centred just inside the shroud edge
    pad_in = xc + inside * size / 2                       # innermost x of the pad footprint

    def h(x):
        xs = x + inside * max(0.0, (x_edge - x) * inside + 0.5)   # clamp samples into the shroud
        z = min(under(xs, yc + dy) for dy in np.linspace(-depth / 2, depth / 2, 9))
        return (z - PAD_GAP if z < flat + 15.0 else flat) - top

    # Contoured top, ramp up the edge chamfer then flat inward (running minimum from the edge, so it
    # only ever drops going inward and never pokes into the card). Rev 3c: the locating lip no
    # longer stands up as a separate taller block -- it carries the contour's edge height straight
    # out, so pad + lip have ONE continuous top.
    lip_out = x_edge + sx * (CLR + 3.0)
    a, b = min(pad_in, x_edge), max(pad_in, x_edge)
    xs = np.arange(a, b + PAD_STEP / 2, PAD_STEP)
    hs = np.array([h(float(x)) for x in xs])
    edge_first = sx < 0                                   # left pads: xs ascends from the edge
    hs = np.minimum.accumulate(hs if edge_first else hs[::-1])
    hs = hs if edge_first else hs[::-1]
    pts = [(float(x), top + float(z)) for x, z in zip(xs, hs)]
    edge_z = pts[0][1] if edge_first else pts[-1][1]
    pts = ([(lip_out, edge_z)] + pts) if edge_first else (pts + [(lip_out, edge_z)])
    lo, hi = pts[0][0], pts[-1][0]
    return (cq.Workplane("XZ").polyline([(lo, top)] + pts + [(hi, top)]).close()
            .extrude(-depth).translate((0, yc - depth / 2, 0)))


def hex_points(x0, x1, y0, y1, d=HEX_D, wall=HEX_WALL):
    """Centres of a true honeycomb for CadQuery's polygon(6, d), which is FLAT top and bottom
    (a vertex on +x): columns 1.5 R' apart, rows sqrt(3) R' apart, odd columns offset half a row,
    with R' = R + wall / sqrt(3) so every web is exactly `wall` thick. Cells stay inside the box.
    (The old grid used pointy-top spacing for flat-top cells, which left triangles between them.)"""
    r = d / 2
    half_h = r * math.sqrt(3) / 2
    rp = r + wall / math.sqrt(3)
    dx, dy = 1.5 * rp, math.sqrt(3) * rp
    pts, col, x = [], 0, x0 + r
    while x <= x1 - r:
        y = y0 + half_h + (dy / 2 if col % 2 else 0)
        while y <= y1 - half_h:
            pts.append((x, y))
            y += dy
        x += dx
        col += 1
    return pts


def slot(wp, pts, length, width):
    return wp.pushPoints(pts).slot2D(length, width, 0)


# --------------------------------------------------------------------------
def build_faceplate():
    # XZ normal is -Y, so a negative extrude grows toward +Y; shift the plate to y = [-FP_T, 0]
    fp = (cq.Workplane("XZ").center(0, SHELF_Z0 + FP_H / 2).rect(2 * FP_HALF, FP_H)
          .extrude(-FP_T).translate((0, -FP_T, 0)))
    ear_pts = [(sx * HOLE_X, k * U + z) for sx in (-1, 1) for k in range(UNITS) for z in (EIA[0], EIA[2])]
    holes = slot(cq.Workplane("XZ").workplane(offset=10), ear_pts, *M6_SLOT).extrude(-30)
    fp = fp.cut(holes)
    win = (cq.Workplane("XY").box(WIN["x"][1] - WIN["x"][0] + 2 * FIT, 40, WIN["z"][1] - WIN["z"][0] + 2 * FIT,
                                  centered=False).translate((WIN["x"][0] - FIT, -20, WIN["z"][0] - FIT)))
    fp = fp.cut(win)
    # slot the bent flange passes through, and a post in front for its M3 screws
    # tab slot runs to 1 mm above the card top: on the real card the tab's bend reaches the backplate
    nz0, nz1 = BR_Z0 - 0.5 - NOTCH_EXTRA_Z0, CARD_Z1_REAL + 1.0 + NOTCH_EXTRA_Z1
    notch = cq.Workplane("XY").box(BR_TAB_T + 1.6 + NOTCH_EXTRA_W + 2 * FIT, 20, nz1 - nz0 + 2 * FIT, centered=False)         .translate((BR_FL_X - 0.8 - NOTCH_EXTRA_W - FIT, -15, nz0 - FIT))
    fp = fp.cut(notch)
    post = cq.Workplane("XY").box(FL_POST_W, BR_FL_L - FP_T + 1.0, BR_W, centered=False)         .translate((BR_FL_X + BR_TAB_T + 0.8 + FIT, -BR_FL_L - 1.0, BR_Z0))
    # solid post: self-tapping screws go through the tab holes, drilled where they land (rev 3)
    fp = fp.union(post)
    # 1 mm relief behind the tongue: on the real bracket its tip leans ~0.4 mm forward
    relief = cq.Workplane("XY").box(BR_TONGUE[1] - BR_TONGUE[0] + 3.0, 1.5, TONGUE_Z[1] - TONGUE_Z[0] + 3.0, centered=False)         .translate((BR_TONGUE[0] - 1.5, -1.5, TONGUE_Z[0] - 1.5))
    fp = fp.cut(relief)
    # hex intake over the riser bay on the left
    hp = hex_points(-106.0, WIN["x"][0] - FIT - 6.0, SHELF_Z0 + LIP_H + 4.0, SHELF_Z0 + FP_H - 6.0)  # intake left of the card
    tx, tz = TONGUE_SCREW   # leave the cells round the tongue screw solid
    hp = [p for p in hp if math.hypot(p[0] - tx, p[1] - tz) > TONGUE_PAD_R + HEX_D / 2]
    hx = (cq.Workplane("XZ").workplane(offset=10).pushPoints(hp).polygon(6, HEX_D).extrude(-30))
    fp = fp.cut(hx)
    screws = (cq.Workplane("XZ").workplane(offset=10)
              .pushPoints([(x, LIP_SCREW_Z) for x in LIP_SCREWS_X]).circle(1.7 + FIT / 2).extrude(-30))
    fp = fp.cut(screws)
    return fp


def build_shelf():
    s = cq.Workplane("XY").box(2 * SHELF_HALF, SHELF_L, SHELF_T, centered=(True, False, False)) \
        .translate((0, 0, SHELF_Z0))
    # vents under the three fans
    hp = hex_points(CARD_X0 + 10, CARD_X0 + CARD_W - 10, 14.0, CARD_L - 14.0)
    hx = cq.Workplane("XY").pushPoints(hp).polygon(6, HEX_D).extrude(50).translate((0, 0, -10))
    s = s.cut(hx)
    top = SHELF_Z0 + SHELF_T
    # side rims = the two beams that carry the span
    for sx in (-1, 1):
        x = sx * (SHELF_HALF - RIM_T / 2)
        s = s.union(cq.Workplane("XY").box(RIM_T, SHELF_L, RIM_H, centered=(True, False, False))
                    .translate((x, 0, top)))
    # front lip with M3 heat-set inserts for the faceplate
    lip = cq.Workplane("XY").box(2 * SHELF_HALF, LIP_D, LIP_H - SHELF_T, centered=(True, False, False)) \
        .translate((0, 0, top))
    ins = (cq.Workplane("XZ").pushPoints([(x, LIP_SCREW_Z) for x in LIP_SCREWS_X])
           .circle(2.1).extrude(-7.0))
    lip = lip.cut(ins)
    s = s.union(lip)
    # standoffs on the shroud rim: pad + locating lip in one smooth solid, its top a spline fitted
    # to the REAL shroud underside (detailed Ti mesh) so it beds along the whole curve
    under = shroud_underside()
    for x_edge, sx in ((SHROUD_X[0], -1), (SHROUD_X[1], 1)):
        for y in (LIP_D + 10.0, CARD_L / 2, CARD_L - 12.0):
            s = s.union(smooth_pad(x_edge, sx, y, top, under))
    # Rev 3c: no rear stop -- the faceplate tab screw and the strap hold the card fore-and-aft
    # strap slots, one each side of the card, front and rear third
    for x in [CARD_X0 - 6.0] + ([CARD_X0 + CARD_W + 4.0] if CARD_X0 + CARD_W + 6.0 < SHELF_HALF - RIM_T else []):
        for y in (CARD_L * 0.3, CARD_L * 0.7):
            s = s.cut(cq.Workplane("XY").box(4.0, 22.0, 50).translate((x, y, 0)))
    # riser wall: the riser's slot board bolts here, facing the PCIe fingers.
    # Rows of M3 slots so any riser's hole pattern lands on one; drill final holes once it's bought.
    # Rev 3b: no riser wall or gussets -- nabaru's riser socket latches onto the card, so nothing
    # has to be bolted upright. Instead one wide floor slot, running from the riser bay to UNDER the
    # card's PCIe fingers, so the ribbon drops straight down to the board's PCIE1 below.
    s = s.cut(cq.Workplane("XY").box(RISER_SLIT_X[1] - RISER_SLIT_X[0], RISER_SLIT_Y[1] - RISER_SLIT_Y[0],
                                     50, centered=False).translate((RISER_SLIT_X[0], RISER_SLIT_Y[0], -10)))
    # rear ears onto the rear posts (1U tall, M6 slots at EIA 1 and 3). Rev 3b: on the OUTER face of
    # the rear flange (y 240..245), the way the faceplate sits on the front posts and every rack ear
    # does -- they used to be on the inner face, so the bolts had to go on from inside the rack.
    for sx in (-1, 1):
        x0 = -FP_HALF if sx < 0 else SHELF_HALF - 4
        ear = cq.Workplane("XY").box(FP_HALF - SHELF_HALF + 4, EAR_T, U - 0.8, centered=False) \
            .translate((x0, RACK_OUT, SHELF_Z0))
        holes = (cq.Workplane("XZ").pushPoints([(sx * HOLE_X, EIA[0]), (sx * HOLE_X, EIA[2])])
                 .slot2D(*M6_SLOT, 0).extrude(-400).translate((0, 100, 0)))
        ear = ear.cut(holes)
        s = s.union(ear)
        # arm reaching past the flange to the ear, plus a gusset tying it into the rim
        s = s.union(cq.Workplane("XY").box(RIM_T, RACK_OUT - (RACK_D - 20.0), RIM_H + SHELF_T, centered=False)
                    .translate((sx * (SHELF_HALF - RIM_T / 2) - RIM_T / 2, RACK_D - 20.0, SHELF_Z0)))
        g = (cq.Workplane("YZ").polyline([(RACK_D - 35, 0), (RACK_OUT, 0), (RACK_OUT, 30)]).close()
             .extrude(RIM_T).translate((sx * (SHELF_HALF - RIM_T / 2) - RIM_T / 2, 0, SHELF_Z0 + SHELF_T)))
        s = s.union(g)
    return s


def build_bracket():
    """The card's own 4-slot I/O bracket, simplified but to the PCI drawing: plate, bent tab with
    its two screw holes, tongue, and the HDMI/DP cutouts. Bracket face at y = 0, tab folds to -y."""
    body = cq.Workplane("XY").box(BR_BODY + BR_T, BR_T, BR_W, centered=False)         .translate((BR_TONGUE[1], 0, BR_Z0))
    tongue = cq.Workplane("XY").box(BR_TONGUE[1] - BR_TONGUE[0], BR_T, BR_TONGUE_W, centered=False)         .translate((BR_TONGUE[0], 0, BR_Z1 - BR_TONGUE_OFF - BR_TONGUE_W))
    tab = cq.Workplane("XY").box(BR_T, BR_FL_L, BR_W, centered=False)         .translate((BR_FL_X, -BR_FL_L + BR_T, BR_Z0))
    holes = cq.Workplane("YZ").pushPoints([(BR_FL_HOLE_Y, z) for z in FL_SCREW_Z])         .circle(BR_FL_HOLE_D / 2).extrude(10).translate((BR_FL_X - 5, 0, 0))
    br = body.union(tongue).union(tab.cut(holes))
    for hc, w, tt in PORT_CUTS:
        br = br.cut(cq.Workplane("XY").box(w, 10, tt).translate((hc, 0, PORT_ZC)))
    return br


def card_envelope(clr=CLR):
    """Card as the parts it is made of: shroud, PCIe fingers, I/O bracket with its bent flange
    and tongue, the 16-pin plug, and the zone in front of the ports where cables plug in."""
    # no clearance under the shroud: it is meant to sit on the standoffs
    c = cq.Workplane("XY").box(CARD_W + 2 * clr, CARD_L - SHROUD_SET + clr, CARD_T + clr, centered=False)         .translate((CARD_X0 - clr, SHROUD_SET, CARD_Z0 + 1e-3))
    fingers = cq.Workplane("XY").box(FINGER_OUT, 89.0, 6.0, centered=False)         .translate((CARD_X0 - FINGER_OUT, 50.0, PCB_Z - 3.0))
    plug = cq.Workplane("XY").box(PLUG["x"][1] - PLUG["x"][0], PLUG["y"][1] - PLUG["y"][0],
                                  PLUG["z"][1] - PLUG["z"][0], centered=False)         .translate((PLUG["x"][0], PLUG["y"][0], PLUG["z"][0]))
    br = build_bracket()
    ports = cq.Workplane("XY").box(PORTS["x"][1] - PORTS["x"][0], 40.0, PORTS["z"][1] - PORTS["z"][0],
                                   centered=False).translate((PORTS["x"][0], -40.0, PORTS["z"][0]))
    return c, fingers, plug, br, ports


# --------------------------------------------------------------------------
def export(shape, name):
    path = os.path.join(OUT, f"{name}.stl")
    cq.exporters.export(shape, path, tolerance=0.08, angularTolerance=0.2)
    return path


def read_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        return np.array([struct.unpack("<12fH", f.read(50))[3:12] for _ in range(n)])


def vol(a, b):
    try:
        return a.intersect(b).val().Volume()
    except Exception:
        return 0.0


def checks(fp, sh):
    res = []
    def ok(name, cond, detail):
        res.append((name, bool(cond), detail))
    for n, p in (("faceplate", fp), ("shelf", sh)):
        v = p.val()
        ok(f"{n} solid valid", v.isValid(), f"{len(p.solids().vals())} solid(s)")
        bb = v.BoundingBox()
        dims = sorted([bb.xlen, bb.ylen, bb.zlen], reverse=True)
        ok(f"{n} fits 320x320 bed", dims[0] <= 315 and dims[1] <= 315,
           f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}")
    card, fingers, plug, br, ports = card_envelope()
    # the contoured pads rise into this flat-bottomed box on purpose (they follow the real curved
    # underside), so their footprints are left out here and checked against both real meshes below
    pads = None
    for x_edge, sx in ((SHROUD_X[0], -1), (SHROUD_X[1], 1)):
        for y in (LIP_D + 10.0, CARD_L / 2, CARD_L - 12.0):
            # whole smooth_pad footprint: 13 mm inside the shroud edge out to the lip's outer face
            x_a, x_b = x_edge - sx * 13.0, x_edge + sx * (CLR + 3.0)
            b = cq.Workplane("XY").box(abs(x_b - x_a), 12.0, 60.0, centered=(True, True, False)) \
                .translate(((x_a + x_b) / 2, y, 0))
            pads = b if pads is None else pads.union(b)
    for n, p, box in (("faceplate", fp, card), ("shelf", sh, card.cut(pads))):
        ok(f"{n} clear of card (+{CLR} mm)", vol(p, box) < 1e-3,
           f"overlap {vol(p, box):.2f} mm3" + (" (pads: see real-mesh checks)" if n == "shelf" else ""))
    for n, p in (("faceplate", fp), ("shelf", sh)):
        ok(f"{n} clear of 16-pin", vol(p, plug) < 1e-3, f"overlap {vol(p, plug):.2f} mm3")
        ok(f"{n} clear of PCIe fingers", vol(p, fingers) < 1e-3, f"overlap {vol(p, fingers):.2f} mm3")
        ok(f"{n} clear of I/O bracket + flange", vol(p, br) < 1e-3, f"overlap {vol(p, br):.2f} mm3")
        ok(f"{n} leaves HDMI/DP open", vol(p, ports) < 1e-3, f"overlap {vol(p, ports):.2f} mm3")
    # nothing but the ears may enter the posts' columns inside the rack depth
    # the real L-section posts, all four corners, over the 3U block
    posts = []
    for sx in (-1, 1):
        xo = sx * (CLEAR_X + POST_W)                       # outer edge
        for y0, yf in ((0.0, 0.0), (RACK_OUT - POST_D, RACK_OUT - FLANGE_T)):
            fl = cq.Workplane("XY").box(POST_W, FLANGE_T, UNITS * U, centered=False)                 .translate((min(xo, xo - sx * POST_W), yf, 0))
            web = cq.Workplane("XY").box(WEB_T, POST_D, UNITS * U, centered=False)                 .translate((min(xo, xo - sx * WEB_T), y0, 0))
            posts += [fl, web]
    pv = sum(vol(sh, p) for p in posts) + sum(vol(fp, p) for p in posts)
    heads = cq.Workplane("YZ").pushPoints([(BR_FL_HOLE_Y, z) for z in FL_SCREW_Z]).circle(2.9)         .extrude(2.5).translate((BR_FL_X - 2.5, 0, 0))
    ok("tab screw heads clear of HDMI/DP", vol(heads, card_envelope()[4]) < 1e-3, "M3 button heads, -x side of tab")
    ok("tab screw heads clear of faceplate", vol(heads, fp) < 1e-3, f"overlap {vol(heads, fp):.2f} mm3")
    ok("clear of the 4 Lab Rax posts", pv < 1e-3, f"overlap {pv:.2f} mm3")
    # the real card mesh (GrabCAD FTW3, Ti thickness) against the printed parts, point by point
    import glob
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.TopAbs import TopAbs_IN
    from OCP.gp import gp_Pnt
    cards = [("REAL card mesh", [os.path.join(OUT, "_ref_card_3090ti.stl")]),
             ("Ti CAD (STEP)", sorted(glob.glob(os.path.join(OUT, "ti_cad_*.stl"))))]
    P = None
    for label, files in cards:
        files = [f for f in files if os.path.exists(f)]
        if not files:
            continue
        P = np.unique(np.concatenate([read_stl(f).reshape(-1, 3) for f in files]).round(2), axis=0)
        P = P[:: max(1, len(P) // 15000)]
        for n, part in (("faceplate", fp), ("shelf", sh)):
            bb = part.val().BoundingBox()
            cand = P[(P[:, 0] > bb.xmin) & (P[:, 0] < bb.xmax) & (P[:, 1] > bb.ymin) & (P[:, 1] < bb.ymax)
                     & (P[:, 2] > bb.zmin) & (P[:, 2] < bb.zmax)]
            cls = BRepClass3d_SolidClassifier(part.val().wrapped)
            hits = []
            for x, y, z in cand:
                cls.Perform(gp_Pnt(float(x), float(y), float(z)), 0.05)
                # y > -0.3 on the faceplate = the bracket face bearing on its back: contact, not a clash
                if cls.State() == TopAbs_IN and not (n == "faceplate" and y > -0.3):
                    hits.append((x, y, z))
            pad_hits = 0
            if label.startswith("Ti CAD") and n == "shelf":
                # the STEP shroud is flat-bottomed, the pads follow the detailed mesh's real curve:
                # contact inside a pad footprint is expected there, anything else still fails
                def on_pad(x, y):
                    return any(abs(x - (e - sx * 7.0)) <= 6.0 + CLR + 3.0 and abs(y - yy) <= 6.0
                               for e, sx in ((SHROUD_X[0], -1), (SHROUD_X[1], 1))
                               for yy in (LIP_D + 10.0, CARD_L / 2, CARD_L - 12.0))
                pad_hits = sum(1 for h in hits if on_pad(h[0], h[1]))
                hits = [h for h in hits if not on_pad(h[0], h[1])]
            det = f"{len(hits)} of {len(cand)} nearby card points inside"
            if pad_hits:
                det += f"; {pad_hits} on contoured pads ignored (STEP shroud bottom is flat)"
            if hits:
                h = np.array(hits); det += f" (x {h[:,0].min():.0f}..{h[:,0].max():.0f} y {h[:,1].min():.0f}..{h[:,1].max():.0f} z {h[:,2].min():.0f}..{h[:,2].max():.0f})"
            ok(f"{n} clear of {label}", not hits, det)
    if P is not None:
        ok("real card rear stick-out", True, f"tail at {P[:, 1].max():.0f} -> {P[:, 1].max() - RACK_OUT:.0f} mm past frame + plug")
    top = max(fp.val().BoundingBox().zmax, sh.val().BoundingBox().zmax, CARD_Z1)
    ok("stack inside 3U", top <= UNITS * U, f"top {top:.1f} of {UNITS * U:.2f}")
    gap = CARD_X0 - FINGER_OUT - RISER_X
    bay = cq.Workplane("XY").box(gap - 0.2, RISER_Y[1] - RISER_Y[0], 80, centered=False)         .translate((RISER_X + 0.1, RISER_Y[0], CARD_Z0))
    ok("riser bay clear above the floor", vol(sh, bay) < 1e-3, f"{gap:.0f} mm wide, nothing in it")
    slit = cq.Workplane("XY").box(RISER_SLIT_X[1] - RISER_SLIT_X[0], RISER_SLIT_Y[1] - RISER_SLIT_Y[0],
                                  SHELF_T + 2, centered=False).translate((RISER_SLIT_X[0], RISER_SLIT_Y[0], SHELF_Z0 - 1))
    ok("riser slot open under the fingers", vol(sh, slit) < 1e-3,
       f"{RISER_SLIT_X[1] - RISER_SLIT_X[0]:.0f} x {RISER_SLIT_Y[1] - RISER_SLIT_Y[0]:.0f} mm, to x {RISER_SLIT_X[1]:.1f} (PCB edge {CARD_X0:.1f})")
    # span check: two rims + vented plate, simply supported front lip -> rear ears
    E, P, L = 1900.0, 2.16 * 9.81, RACK_D
    Ir = 2 * RIM_T * (RIM_H + SHELF_T) ** 3 / 12
    Ip = 0.5 * 2 * SHELF_HALF * SHELF_T ** 3 / 12     # half credit for the hex holes
    dfl = P * L ** 3 / (48 * E * (Ir + Ip))
    ok("span deflection < 1 mm (PETG)", dfl < 1.0, f"{dfl:.2f} mm centre load")
    stick = PLUG["y"][1] - RACK_OUT
    ok("rear stick-out (past frame back)", True,
       f"card {CARD_L - RACK_OUT:.0f} + plug {PLUG['y'][1] - CARD_L:.0f} = {stick:.0f} mm")
    return res


# --------------------------------------------------------------------------
W, H = 1100, 760


def render(groups, az, el, path):
    """Orthographic z-buffer, one colour per group. Same approach as cad/stl_preview.py."""
    a, e = math.radians(az), math.radians(el)
    d = np.array([math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), -math.sin(e)])
    # right = view x up (not up x view, which mirrors the image left-to-right)
    r = np.cross(d, [0.0, 0.0, 1.0])
    r = r / np.linalg.norm(r) if np.linalg.norm(r) > 1e-6 else np.array([1.0, 0, 0])
    u = np.cross(r, d)
    u /= np.linalg.norm(u)
    allv = np.concatenate([g[0].reshape(-1, 3) for g in groups])
    cen = (allv.min(0) + allv.max(0)) / 2
    proj = lambda p: (p @ r, p @ u, p @ d)
    xs, ys, _ = proj(allv - cen)
    s = min((W - 60) / (xs.max() - xs.min()), (H - 60) / (ys.max() - ys.min()))
    img = np.full((H, W, 3), 245, np.uint8)
    zb = np.full((H, W), 1e18)
    light = np.array([0.4, -0.5, 0.75]) / np.linalg.norm([0.4, -0.5, 0.75])
    for tris, col in groups:
        v = tris.reshape(-1, 3, 3) - cen
        x, y, z = v @ r, v @ u, v @ d
        px = (x * s + W / 2).astype(np.int32)
        py = (H / 2 - y * s).astype(np.int32)
        n = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        shade = np.abs(n @ light) * 0.7 + 0.3
        for k in range(len(v)):
            X, Y, Z = px[k], py[k], z[k]
            x0, x1 = max(X.min(), 0), min(X.max(), W - 1)
            y0, y1 = max(Y.min(), 0), min(Y.max(), H - 1)
            if x1 < x0 or y1 < y0:
                continue
            bx, by, cx, cy = X[1] - X[0], Y[1] - Y[0], X[2] - X[0], Y[2] - Y[0]
            det = bx * cy - cx * by
            if det == 0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            wx, wy = gx - X[0], gy - Y[0]
            b = (wx * cy - cx * wy) / det
            c = (bx * wy - wx * by) / det
            ins = (b >= 0) & (c >= 0) & (b + c <= 1)
            if not ins.any():
                continue
            zz = Z[0] + b * (Z[1] - Z[0]) + c * (Z[2] - Z[0])
            sub = zb[y0:y1 + 1, x0:x1 + 1]
            hit = ins & (zz < sub)
            sub[hit] = zz[hit]
            img[y0:y1 + 1, x0:x1 + 1][hit] = (np.array(col) * shade[k]).astype(np.uint8)
    raw = b"".join(b"\0" + img[i].tobytes() for i in range(H))
    def chunk(t, dat):
        c = t + dat
        return struct.pack(">I", len(dat)) + c + struct.pack(">I", __import__("zlib").crc32(c) & 0xFFFFFFFF)
    import zlib
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def export_posts():
    """Place the real Lab Rax 3U post (ref/rail-height-3u.stl) at the four corners for the viewer.

    Post local frame: web at x 0..6.5 (outer side), hole flange at y 0..6 (front), z 0..133.35.
    """
    src = os.path.join(os.path.dirname(OUT), "ref", "rail-height-3u.stl")
    v = read_stl(src).reshape(-1, 3, 3)
    v = v - v.reshape(-1, 3).min(0)
    xo = CLEAR_X + POST_W
    corners = {"FL": lambda p: (-xo + p[..., 0], p[..., 1]),
               "FR": lambda p: (xo - p[..., 0], p[..., 1]),
               "RL": lambda p: (-xo + p[..., 0], RACK_OUT - p[..., 1]),
               "RR": lambda p: (xo - p[..., 0], RACK_OUT - p[..., 1])}
    for k, f in corners.items():
        w = v.copy()
        w[..., 0], w[..., 1] = f(v)
        with open(os.path.join(OUT, f"_ref_post_{k}.stl"), "wb") as fh:
            fh.write(b"lab rax post".ljust(80, b" ") + struct.pack("<I", len(w)))
            for tri in w:
                fh.write(struct.pack("<12fH", 0, 0, 0, *tri.reshape(-1), 0))


def main():
    os.makedirs(OUT, exist_ok=True)
    fp, sh = build_faceplate(), build_shelf()
    paths = {"gpu_faceplate_3u": export(fp, "gpu_faceplate_3u"), "gpu_shelf": export(sh, "gpu_shelf")}
    card, fingers, plug, br, ports = card_envelope(clr=0)
    ghost = card.union(fingers)
    export(br, "_ref_bracket")
    export(ports, "_ref_ports")
    gp, pp = export(ghost, "_ref_card"), export(plug, "_ref_plug")
    res = checks(fp, sh)
    export_posts()
    import json
    with open(os.path.join(OUT, "REPORT.json"), "w") as f:
        json.dump({"checks": [{"name": n, "pass": g_, "detail": d} for n, g_, d in res],
                   "rack": {"outside_depth": RACK_OUT, "rear_ear_seat": RACK_D, "units": UNITS},
                   "card": {"L": CARD_L, "W": CARD_W, "T": CARD_T, "x0": CARD_X0, "z0": CARD_Z0}}, f, indent=1)
    bad = 0
    for n, good, det in res:
        bad += not good
        print(f"  {'PASS' if good else 'FAIL'}  {n:34s} {det}")
    for n, p in paths.items():
        print(f"  {n}.stl  {len(read_stl(p))} tris")
    g = [(read_stl(paths["gpu_shelf"]), (120, 170, 235)), (read_stl(paths["gpu_faceplate_3u"]), (235, 140, 60)),
         (read_stl(gp), (70, 70, 80)), (read_stl(pp), (225, 60, 40))]
    views = {"iso": (215, 28), "front": (180, 0), "side": (270, 0), "top": (180, 90)}
    for vn, (az, el) in views.items():
        render(g, az, el, os.path.join(OUT, f"assembly_{vn}.png"))
    render(g[:2], 215, 35, os.path.join(OUT, "parts_iso.png"))
    print(f"  renders -> {OUT}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
