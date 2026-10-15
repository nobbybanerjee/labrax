"""Whole-rack layout: Lab Rax 10 inch, 3 x 5U posts + 2 x 1U joiners = 17U.

Every dimension here is READ from a real file, not guessed:
  posts          cad/spec/labrax/5U+Vertical+Post.stl                 (30 x 35 x 222.2 = exactly 5U)
  joiner         cad_gpu/ref/labrax/1U+Support+Extension...stl        (211 x 214 x 30)
  Pi holders     cad/spec/labrax/Pi+4+Holder.stl, Pi+5+Holder...stl   (29 x 92 x 86.4)
  GPU shelf      cad_gpu/print/gpu_shelf.stl + gpu_faceplate_3u.stl   (our own, rev 3c)
Modules with no CAD on disk (ATX PSU 2U mount, 2U mini-ITX shelf, keystone blanks, the small
PSU shelf) are drawn as labelled placeholder boxes at their real U height -- see MODULES.

Rack frame (same numbers the GPU shelf is built to):
  U = 44.45, clear width 222, M6 hole spacing 236.525, outside depth 240.

    python rack_layout.py   ->  out/*.stl, out/LAYOUT.json, rack_front.png, rack_iso.png
"""
import json
import math
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
LABRAX = os.path.join(os.path.expanduser("~"), "Downloads", "CAD", "LabRax")

U = 44.45
CLEAR_X, POST_W, POST_D = 111.0, 30.0, 35.0
RACK_OUT = 2 * POST_D + 170.0          # 240 front face to back face
UNITS_PER_POST, N_POSTS = 5, 3
JOINER_U = float(os.environ.get("JOINER_U", "1.0"))   # upgraded joiners: 1U between sections (0 = posts butt together)
TOTAL_U = N_POSTS * UNITS_PER_POST + (N_POSTS - 1) * JOINER_U     # 17

SRC = {
    "post":    os.path.join(WS, "cad", "spec", "labrax", "5U+Vertical+Post.stl"),
    "joiner":  os.path.join(WS, "cad_gpu", "ref", "labrax", "1U+Support+Extension+Brass+Insert+Version.stl"),
    "pi4":     os.path.join(WS, "cad", "spec", "labrax", "Pi+4+Holder.stl"),
    "pi5":     os.path.join(WS, "cad", "spec", "labrax", "Pi+5+Holder+-+Fits+Pi+3+Too.stl"),
    "gpu_shelf":  os.path.join(WS, "cad_gpu", "print", "gpu_shelf.stl"),
    "gpu_face":   os.path.join(WS, "cad_gpu", "print", "gpu_faceplate_3u.stl"),
    "gpu_card":   os.path.join(WS, "cad_gpu", "print", "_ref_card_3090ti.stl"),   # detailed Ti mesh
    "foot":    os.path.join(WS, "cad", "spec", "labrax", "Foot.stl"),
    "side":    os.path.join(WS, "cad_gpu", "ref", "labrax", "labrax-hws.stl"),   # what was printed (x2)
    # real creator STLs, C:\Users\nabaru\Downloads\CAD\LabRax (no g-code rebuilds)
    "horiz_edge": os.path.join(LABRAX, "Solid+Horizontal+Edge.stl"),
    "horiz_vent": os.path.join(LABRAX, "Ventilated+Horizontal+Edge.stl"),
    "top_edge":   os.path.join(LABRAX, "Top+Edge.stl"),
    "handle":     os.path.join(LABRAX, "Handle.stl"),
    # the top panel actually printed (latest of the two SmartiPi jobs, 2026-09-19)
    "top_panel":  os.path.join(LABRAX, "from_nobby", "Top+Panel_SmartiPi_20mmRearTrim_226mm.stl"),
}
SIDE_SECTIONS = 1       # 2 side panels printed -> one 5U section's worth

# Bill of materials from the creator's build guide (the-diy-life.com, "Introducing Lab Rax"):
#   4 Vertical Post | 4 Horizontal Edge (solid or vented) | 4 Edge (= Top+Edge.stl) | 2 Handle
#   4 Foot | 2 Side Panel | 1 Top Panel | 1 Bottom Panel | 24 M6x10 screws + 24 M6 brass inserts
#
# How the frame goes together, from the hole positions in the real STLs (_realbores.py,
# _cbores.py), local coordinates of each file:
#   Post      insert o7.6 axis X at (y 22.50, z 10.00) from each end; pocket x 1.5..7.0, opening
#             on the web's inner side at 7.0 from the outer face. Side-panel slot down the web
#             edge facing the opposite post, 2..5 in from the outer face.
#   Top Edge  the SAME L-profile as the post, 170 long, turned on its side: its 35 mm leg stands
#             as a wall at the outer face, its thin leg is a ledge at the foot. Joint insert o7.6
#             at 22.5 up the wall, 10 from each end, opening at 7.0 -- the post's insert again.
#             3 mm groove along the top of the wall at 2..5 inward: the side panel's bottom edge.
#             Groove at the ledge tip, 27..29 inward: the base panel edge (228 / 2 = 141 - 27).
#             Vertical inserts in the ledge, 19.98 from each end, 16.23 in from the outer face,
#             opening downward: feet (bottom edges) and handles (top edges).
#   So each Top Edge sits directly UNDER (or over) a post section, between the front and rear
#   posts (y 35..205): wall top = post end, and 222.25 + 2 x 2.95 = 228.15 = the side panel.
#   Horizontal Edge  an L-angle printed at 45 deg. Each end pad has two o6.4 holes with o10.8
#             counterbores, 31.82 apart. Post insert (y 22.5, z +10) and Top Edge insert
#             (y 35+10 = 45, z -35+22.5 = -12.5) are (22.5, -22.5) apart = 31.82: the pad
#             bridges the two at 45 deg, one screw into each. Pad face at 7.2 from the outer face
#             meets both pockets' opening at 7.0 (0.2 gap). Full width 282.25 = outside width.
# z = 0 stays at the bottom of the lowest post so the module U positions don't move; the base
# frame hangs below it (Top Edge z -35..0, feet below that).
TE_H = 35.0             # Top Edge wall height (its 35 mm leg)
PANEL_IN = 1.4          # side-panel slot 1.2..4.6 in from the outer face, 3.0 deep -- measured at
                        # 0.25 mm on the Top Edge and the 1U extension (same groove); 3 mm panel centred

# (key, label, U from bottom, U height, kind, colour)
#   kind "real" = geometry from SRC, "box" = placeholder at the right U height (no CAD on disk yet)
# nabaru's stack, bottom up (2026-10-13). Rack gear can only start on a U boundary -- a 1U panel's
# holes are 15.875 + 15.875 apart, one hole up the post they are 15.875 + 12.7 -- so "5 holes
# empty" is the 2U below the keystone panel, and "2 holes left" under the GPU is 1U.
# Keystone blank: its slot is 6.1 from one edge. nabaru mounts it flipped, slot near the TOP, so it
# hangs from the 6th hole (U1 + 38.1) with its top flush at U2 -> 5 holes empty below, and the
# shelf above starts at U2.
MODULES = [
    ("empty_lo",  "1.5U · empty (5 holes)",                       0.0, 1.5, "air",  0x2a3340),
    ("keystone",  "0.5U · keystone blank (flipped, 6th hole)",    1.5, 0.5, "real", 0x5f6b7a),
    ("tpe_shelf", "1U · open shelf, tpe_bg_380",                  2.0, 1.0, "real", 0x8a7f6a),
    ("gs108t",    "1U · open shelf, GS108T switch",               3.0, 1.0, "real", 0x6a8a7f),
    ("sbc",       "2U · SBC holder: 1 empty, 4x Pi 4, 2x Pi 5 (right)", 4.0, 2.0, "sbc", 0x3fb950),
    ("psu_shelf", "1U · PETG open shelf carrying the PSU (shares U6)", 6.0, 1.0, "real", 0xb98cff),
    ("pc_psu",    "2U · ATX PSU mount + ATX PSU (RM1000e size)",   6.0, 2.0, "real", 0x9b8cff),
    ("itx",       "2U · mini-ITX shelf + mini-ITX board",          8.0, 2.0, "real", 0x58a6ff),
    ("gap",       "1U · empty",                                  10.0, 1.0, "air",  0x2a3340),
    ("gpu",       "3U · GPU shelf + RTX 3090 Ti FTW3",           11.0, 3.0, "gpu",  0xe58c3c),
]
# real faceplate modules: file, width axis, height axis, depth axis (front face at depth 0),
# height flipped (file stores the part upside down), U height actually occupied
NOBBY = os.path.join(LABRAX, "from_nobby")        # copied from nobby D:\Downloads\08_3D_Printing\LabRax
REAL = {"tpe_shelf": (os.path.join(LABRAX, "tpe_bg_380_1u_open_shelf_solid.stl"), 0, 2, 1, False, 1.0),
        "gs108t":    (os.path.join(LABRAX, "gs108t_1u_open_shelf_solid_.stl"), 0, 2, 1, False, 1.0),
        # 252 x 26 x 88.75, full-width face at local y = 0
        "pc_psu":    (os.path.join(NOBBY, "ATX+PSU+2U+Mount+-+Lab+Rax+extra+support+mounts.stl"), 0, 2, 1, False, 2.0),
        # 252 x 86.45 x 237, face at local z = 0, floor at local y = 86 -> stored upside down
        "itx":       (os.path.join(NOBBY, "2U Mini ITX Computer Shelf.stl"), 0, 1, 2, True, 2.0),
        # 254 x 22.25 x 9.5 = a 0.5U blank, mounted flipped (slot near the top)
        "keystone":  (os.path.join(NOBBY, "keystone-blank-1_2u-10i-rm.stl"), 0, 1, 2, True, 0.5),
        # printed in PETG 2026-09-30: 252 x 237 x 42, ears only (no faceplate) at local y = 237,
        # hex floor 4 mm. Its ears share the PSU mount's lower-U holes, sitting under the mount's ears.
        "psu_shelf": (os.path.join(NOBBY, "obj_1_1U Open Shelf.stl"), 0, 2, 1, False, 1.0)}
DEPTH_FLIP = {"psu_shelf"}                 # file has its ears at the far end of the depth axis
EAR_T = {"psu_shelf": 3.0}                 # ear thickness where the side gussets confuse the measurement
Y_SHIFT = {"pc_psu": -3.0}                 # PSU mount bolts on top of the open shelf's 3 mm ears
REAR = {"pc_psu", "psu_shelf"}             # hung from the REAR posts, facing out the back (same U)


def to_rear(P):
    """rotate 180 deg about vertical: front-post mounting -> rear-post mounting, facing backwards"""
    q = P.reshape(-1, 3).copy()
    q[:, 0], q[:, 1] = -q[:, 0], RACK_OUT - q[:, 1]
    return q
# PSU rests on the shelf floor (top 1.225 + 4.0 above U6), not where the mount's ATX holes alone put
# it (0.075 + 1.61 above U6): +3.54 mm. See the note in the summary -- the holes then sit 3.5 high.
PSU_LIFT = (U - 42.0) / 2 + 4.0 - ((2 * U - 88.75) / 2 + 1.61)
BOTTOM_PANEL = os.path.join(NOBBY, "Bottom_Panel_Hex_Ventilated.stl")
HARDWARE = {"pc_psu": "atx_psu", "itx": "mitx_board"}      # _hardware.py, placed on the module's holes
SBC_HOLDER = os.path.join(LABRAX, "2U+7+SBC+Holder.stl")      # width y, height x, depth z
SBC_SLOTS = (None, "pi4", "pi4", "pi4", "pi4", "pi5", "pi5")  # left -> right, seen from the front


# ---------------------------------------------------------------- STL helpers
def read_stl(path):
    with open(path, "rb") as f:
        head = f.read(80)
        if head[:5].lower().lstrip() == b"solid" and b"facet" in f.read(400):
            f.seek(0)
            v = [float(w) for ln in f.read().decode("ascii", "ignore").splitlines()
                 if ln.strip().startswith("vertex") for w in ln.split()[1:4]]
            return np.array(v, "f4").reshape(-1, 3)
        f.seek(80)
        n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.uint8).reshape(n, 50)
        return d[:, 12:48].copy().view("<f4").reshape(-1, 3)


Z_FLOOR = [0.0]     # set in main(): lift on export so z = 0 is the bottom of the feet


def write_stl(path, tris):
    t = tris.reshape(-1, 3, 3).astype("<f4").copy()
    t[:, :, 2] += Z_FLOOR[0]
    with open(path, "wb") as f:
        f.write(b"rack layout".ljust(80, b" ") + struct.pack("<I", len(t)))
        for tri in t:
            f.write(struct.pack("<12fH", 0, 0, 0, *tri.reshape(-1), 0))


def box_tris(x0, y0, z0, x1, y1, z1):
    """Triangles of an axis-aligned box."""
    p = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], "f4")
    q = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return p[np.array(q).reshape(-1)]


FP_HALF, FP_T = 126.5, 5.0           # Lab Rax faceplate: 253 wide, 5 thick, same as the GPU one
HOLE_X = 236.525 / 2                 # M6 hole spacing across the rack
EIA = (6.35, 22.225, 38.1)           # hole heights within each U
M6_SLOT = (9.8, 7.4)                 # slot length x width, the printed size on the GPU faceplate


def shelf_tris(u0, uh, depth=180.0, floor_t=4.0, rim=12.0):
    """A Lab Rax-style module: front faceplate with real M6 rack slots at the EIA heights it
    spans, a tray floor behind it, and two side rims. Placeholder geometry, real interfaces --
    so the rack reads correctly and the bolt positions can be checked against the posts."""
    import cadquery as cq
    h = uh * U - 0.8                                   # 0.8 gap to the neighbouring module
    z0 = u0 * U + 0.4
    fp = (cq.Workplane("XZ").center(0, z0 + h / 2).rect(2 * FP_HALF, h)
          .extrude(-FP_T).translate((0, -FP_T, 0)))
    pts = [(sx * HOLE_X, k * U + e) for sx in (-1, 1)
           for k in range(int(math.floor(u0)), int(math.ceil(u0 + uh)))
           for e in EIA if z0 <= k * U + e <= z0 + h]
    if pts:
        fp = fp.cut(cq.Workplane("XZ").workplane(offset=10)
                    .pushPoints(pts).slot2D(*M6_SLOT, 0).extrude(-30))
    # the tray lives BEHIND the faceplate, so it must fit the 222 mm clear width between the
    # posts -- not the 253 mm faceplate width, which overhangs them on purpose
    floor = (cq.Workplane("XY").box(2 * CLEAR_X - 2.0, depth, floor_t, centered=(True, False, False))
             .translate((0, 0, z0)))
    body = fp.union(floor)
    for sx in (-1, 1):                                  # side rims, like the real open shelf
        body = body.union(cq.Workplane("XY")
                          .box(3.0, depth, min(rim, h - floor_t), centered=(True, False, False))
                          .translate((sx * (CLEAR_X - 2.5), 0, z0 + floor_t)))
    import tempfile
    f = os.path.join(tempfile.gettempdir(), "_shelf.stl")
    cq.exporters.export(body, f, tolerance=0.08, angularTolerance=0.25)
    return read_stl(f)


# ---------------------------------------------------------------- frame
def frame_tris():
    """Four corner stacks: post, joiner, post, joiner, post -- 17U total."""
    post = read_stl(SRC["post"])
    post = post - post.min(0)
    ph = post[:, 2].max()
    joiner = read_stl(SRC["joiner"])
    joiner = joiner - joiner.min(0)

    xo = CLEAR_X + POST_W
    corners = {"FL": (lambda p: (-xo + p[:, 0], p[:, 1])),
               "FR": (lambda p: (xo - p[:, 0], p[:, 1])),
               "RL": (lambda p: (-xo + p[:, 0], RACK_OUT - p[:, 1])),
               "RR": (lambda p: (xo - p[:, 0], RACK_OUT - p[:, 1]))}
    posts, joiners = [], []
    for k, f in corners.items():
        w = post.copy()
        w[:, 0], w[:, 1] = f(post)
        for i in range(N_POSTS):
            z = i * (UNITS_PER_POST + JOINER_U) * U
            q = w.copy(); q[:, 2] += z
            posts.append(q)
    # 1U extension ("Lab Rax Upgraded 1U Extension Module"). Measured off the real STL, not guessed
    # -- see _bores2.py / _extfit.py. It is NOT a diagonal corner brace: it is a full-depth side
    # rail, one per side, and the creator's "structural cross brace between the front and rear
    # posts" is exactly that. Proof, all from the mesh:
    #   * its long axis is 240.00 mm = the rack's outside depth, so it ends flush front and rear;
    #   * it carries three o7.6 bores running the WHOLE 240 mm, at 22.86 mm from the outer face --
    #     the post's own M6 column is at 22.86 mm too (rack x 118.14 vs spec 118.26, 0.12 mm);
    #   * those bores sit 15.90 mm apart = the EIA pitch, so the band gets its own 3 rack holes.
    #     That is how it "adds an additional 1U of usable rack space".
    #   * putting bore 1 on the band's first EIA height puts bores 2 and 3 on the other two to
    #     within 0.06 mm, and leaves a symmetric 19.83 / 19.89 mm lap onto the post below / above.
    # Local axes of ext_rot.npy: x = depth 0..240, y = vertical 0..84.17, z = across 0..30 measured
    # from the OUTER face, same sense as the post's local x. Hence rack x = +-(141 - z).
    EXT_LAP, EXT_HOLE_V = 19.83, 26.18
    rot = os.path.join(HERE, "ext_rot.npy")
    for i in range(N_POSTS - 1):
        z = (i * (UNITS_PER_POST + JOINER_U) + UNITS_PER_POST) * U
        if os.path.exists(rot) and JOINER_U > 0:
            base = np.load(rot)
            base = base - base.reshape(-1, 3).min(0)
            for sx in (-1, 1):
                q = np.empty_like(base)
                q[:, :, 0] = sx * (CLEAR_X + POST_W - base[:, :, 2])   # across, from the outer face
                q[:, :, 1] = base[:, :, 0]                             # depth 0..240, flush
                q[:, :, 2] = base[:, :, 1] + z + EIA[0] - EXT_HOLE_V   # bores onto the band's EIA
                if sx < 0:                                             # keep winding after mirror
                    q = q[:, ::-1, :]
                joiners.append(q)
    jo = np.concatenate(joiners) if joiners else np.zeros((0, 3, 3), 'f4')
    return np.concatenate(posts), jo, ph


# ---------------------------------------------------------------- enclosure: frames, panels, feet, handles
def enclosure_tris():
    """Base frame, top frame, feet, handles, base/top panels and side panels -- real STLs only.
    See the header comment above TE_H for where every placement number comes from."""
    XO = CLEAR_X + POST_W                                   # 141, outer face
    z_top = (N_POSTS * UNITS_PER_POST + (N_POSTS - 1) * JOINER_U) * U   # top of the top post
    frames, feet, handles, panels, sides = [], [], [], [], []

    # ---- Top Edge: local x = 35 leg (-> height), y = 170 length (-> depth), z = 30 leg (-> inward)
    te = read_stl(SRC["top_edge"]); te = te - te.min(0)
    for top in (False, True):
        for sx in (-1, 1):
            q = np.empty_like(te)
            q[:, 0] = sx * (XO - te[:, 2])
            q[:, 1] = POST_D + (te[:, 1] if sx > 0 else 170.0 - te[:, 1])
            q[:, 2] = (z_top + TE_H - te[:, 0]) if top else (te[:, 0] - TE_H)
            frames.append(q)

    # ---- Horizontal Edge: pads bridge post insert (y 22.5, z +10) and Top Edge insert
    # (y 45, z -12.5). Local hole centres (x, z) from _cbores.py.
    h1, h2 = np.array([14.64, 24.40]), np.array([46.46, 24.40])
    post_ins, te_ins = np.array([22.5, 10.0]), np.array([POST_D + 10.0, -TE_H + 22.5])
    target = te_ins - post_ins                               # (22.5, -22.5)

    def place(he, a, b):
        """rotate local (x, z) so hole a -> post insert and hole b -> Top Edge insert"""
        ang = math.atan2(target[1], target[0]) - math.atan2(*(b - a)[::-1])
        c, s = math.cos(ang), math.sin(ang)
        x, z = he[:, 0] - a[0], he[:, 2] - a[1]
        q = np.empty_like(he)
        q[:, 0] = XO + 0.125 - he[:, 1]                    # 282.25 long, centred
        q[:, 1] = post_ins[0] + c * x - s * z
        q[:, 2] = post_ins[1] + s * x + c * z
        return q

    def inside_frame(q):
        """vertices that would sit inside a post, a Top Edge wall or the base panel opening"""
        x, y, z = np.abs(q[:, 0]), q[:, 1], q[:, 2]
        post = (x > XO - 30 + 0.3) & (x < XO - 7.3) & (y > 0.3) & (y < POST_D - 0.3) & (z > 0.3)
        wall = (x > XO - 13 + 0.3) & (x < XO - 7.3) & (y > POST_D + 0.3) & (z < -0.3) & (z > -TE_H + 0.3)
        void = (x < XO - 30) & (y > POST_D + 2) & (y < RACK_OUT - POST_D) & (z > -TE_H) & (z < 0)
        return int((post | wall | void).sum())

    he = read_stl(SRC["horiz_edge"]); he = he - he.min(0)
    cands = [place(he, h1, h2), place(he, h2, h1)]
    scores = [inside_frame(q) for q in cands]
    pick = int(np.argmin(scores))
    hb = cands[pick]
    print(f"  Horizontal Edge: candidate interferences {scores} -> using #{pick}, "
          f"bbox y {hb[:,1].min():.1f}..{hb[:,1].max():.1f} z {hb[:,2].min():.1f}..{hb[:,2].max():.1f}")
    # printed: 2 solid + 2 ventilated -- solid round the base, vented at the top (creator's layout)
    hv = read_stl(SRC["horiz_vent"]); hv = hv - hv.min(0)
    hvb = place(hv, *((h1, h2) if pick == 0 else (h2, h1)))
    for top in (False, True):
        for rear in (False, True):
            q = (hvb if top else hb).copy()
            if rear: q[:, 0], q[:, 1] = -q[:, 0], RACK_OUT - q[:, 1]
            if top:  q[:, 0], q[:, 2] = -q[:, 0], z_top - q[:, 2]
            frames.append(q)

    # ---- feet under, handles over, the Top Edge ledge inserts (19.98 from each end, 16.23 in)
    foot = read_stl(SRC["foot"]); foot = foot - foot.min(0)
    hd = read_stl(SRC["handle"]); hd = hd - hd.min(0)
    for sx in (-1, 1):
        xc = sx * (XO - 16.23)
        for yc in (POST_D + 19.98, POST_D + 150.02):
            q = foot.copy(); q[:, 0] += xc - foot[:, 0].max() / 2
            q[:, 1] += yc - foot[:, 1].max() / 2; q[:, 2] += -TE_H - foot[:, 2].max()
            feet.append(q)
        q = hd.copy(); q[:, 0] += xc - hd[:, 0].max() / 2
        q[:, 1] += POST_D; q[:, 2] += z_top + TE_H
        handles.append(q)

    # ---- panels in the ledge-tip groove (2..5 from the ledge face). Printed: hex bottom panel
    # (flat 3 mm) and the SmartiPi top panel, 226 x 151.5 x 7 with a 3 mm tongue (local z 0..3) round
    # its edge and the 4 mm reinforcement above it; the 20 mm rear trim leaves the back open.
    bp = read_stl(BOTTOM_PANEL); bp = bp - bp.min(0)
    q = bp.copy(); q[:, 0] -= bp[:, 0].max() / 2; q[:, 1] += (RACK_OUT - bp[:, 1].max()) / 2
    q[:, 2] += -TE_H + 2.0
    panels.append(q)
    tp = read_stl(SRC["top_panel"]); tp = tp - tp.min(0)
    q = tp.copy(); q[:, 0] = tp[:, 0].max() / 2 - tp[:, 0]            # flipped over: undo the mirror on x
    q[:, 1] += (RACK_OUT - 171.5) / 2                                  # front-aligned, trim at the rear
    q[:, 2] = z_top + TE_H - 2.0 - tp[:, 2]                            # tongue in the groove, ribs inward
    panels.append(q)

    # ---- side panels: printed 2 x labrax-hws (175 x 227.25 x 8 honeycomb wall). Its edge tongue is
    # local z 4..7 (3 mm), which seats in the 1.2..4.6 slot at 1.4..4.4; the 4 mm side of the body
    # goes inward, leaving the outer face 0.4 mm inside the frame. Only 2 printed: bottom section.
    pan = read_stl(SRC["side"]); pan = pan - pan.min(0)
    pd, ph, pt = pan.max(0)
    for i in range(SIDE_SECTIONS):
        z = i * (UNITS_PER_POST + JOINER_U) * U
        for sx in (-1, 1):
            q = np.empty_like(pan)
            q[:, 0] = sx * (XO - (PANEL_IN + 7.0) + pan[:, 2])
            q[:, 1] = pan[:, 0] + (RACK_OUT - pd) / 2
            q[:, 2] = pan[:, 1] + z - (ph - UNITS_PER_POST * U) / 2
            sides.append(q)
    cat = lambda a: np.concatenate(a) if a else np.zeros((0, 3), "f4")
    return cat(feet), cat(panels), cat(sides), cat(frames), cat(handles)


# ---------------------------------------------------------------- modules
def faceplate_module(T, u0, uh, wax, hax, dax, hflip=False, extras=(), dflip=False, ear_t=None, y_shift=0.0):
    """Place a real Lab Rax faceplate module: centred across, back of its ears on the post flange
    (y = 0), centred in its U band. Ear thickness = depth of the material outside the 222 opening.
    `extras` are meshes in the module file's own coordinates (e.g. the PSU on the mount's ATX screw
    holes); they get the same transform and come back as a list after the module."""
    lo = T.min(0); T = T - lo
    Wd, H, Dp = T[:, wax].max(), T[:, hax].max(), T[:, dax].max()
    ear = T[(T[:, wax] < 14) | (T[:, wax] > Wd - 14)]
    t = float(ear_t if ear_t is not None else ear[:, dax].max())
    odd = (wax, dax, hax) not in ((0, 1, 2), (1, 2, 0), (2, 0, 1))

    def xf(P):
        P = P.reshape(-1, 3) - lo
        q = np.empty_like(P)
        q[:, 0] = P[:, wax] - Wd / 2
        q[:, 1] = (Dp - P[:, dax] if dflip else P[:, dax]) - t + y_shift
        q[:, 2] = (H - P[:, hax] if hflip else P[:, hax]) + u0 * U + (uh * U - H) / 2
        if odd != (hflip != dflip):      # net mirror (odd permutation XOR flips): undo on x
            q[:, 0] = -q[:, 0]
        return q
    if extras:                           # extras are measured on the zeroed mesh (file - its min)
        return xf(T + lo), t, [xf(e.reshape(-1, 3) + lo) for e in extras]
    return xf(T + lo), t


# SBC sub-assembly, from the hole positions in the real files (_cbores.py):
#   2U+7+SBC+Holder.stl (x = height, y = width, z = depth, face at z = 0): 7 slot hole pairs, o4.4,
#     at y 37.00 / 66.67 / 96.33 / 126.00 / 155.67 / 185.33 / 215.00 (29.67 pitch), x 4.11 and 82.34,
#     through 7 mm bosses (z 0..7).
#   Pi+4+Holder.stl / Pi+5+Holder (fits Pi 3) (x = width 29, y = depth 92, z = height): front flange
#     y 0..2 with two o4.4 holes at x 14.50, z 4.01 and 82.34.
#   -> each Pi holder slides in from the front through the window; the back of its 2 mm flange sits
#     on the holder's FRONT face (holder z = 0), its two holes on a slot pair, screws into the bosses.
#     Empty slots get nothing. (nobby's original 3MFs are mesh-identical to these STLs.)
HOLE_UP = 1                               # nabaru: whole stack sits one hole higher than first drawn
BASE_HOLE = {"keystone": 5}               # lowest screw hole used, if not the U's first (3 * u0)
HOLE_UP_BY = {"gpu": 0}                   # nabaru: GPU assembly back down one hole


def hole_z(k):
    """height of rack hole k (0 = lowest), EIA 6.35 / 22.225 / 38.1 in every U"""
    return (k // 3) * U + EIA[k % 3]


SBC_SLOT_Y = (37.00, 66.67, 96.33, 126.00, 155.67, 185.33, 215.00)
SBC_HOLE_X, SBC_BOSS = (4.11, 82.34), 7.0
PI_HOLE_X, PI_HOLE_Z, PI_FLANGE = 14.50, (4.01, 82.34), 2.0


def sbc_row(u0):
    holder = read_stl(SBC_HOLDER)
    dz = (SBC_HOLE_X[0] - PI_HOLE_Z[0] + SBC_HOLE_X[1] - PI_HOLE_Z[1]) / 2      # 0.05: hole-pair fit
    extras, kinds = [], []
    for y_slot, kind in zip(SBC_SLOT_Y, SBC_SLOTS):
        if kind is None:
            continue
        p = read_stl(SRC[kind]); p = p - p.min(0)
        e = np.empty_like(p)                    # Pi holder coords -> SBC holder (zeroed) coords
        e[:, 0] = p[:, 2] + dz                  # height
        e[:, 1] = y_slot + (p[:, 0] - PI_HOLE_X) # width: hole line on the slot's hole line
        e[:, 2] = p[:, 1] - PI_FLANGE           # depth: flange's back face on the holder's front face
        extras.append(e); kinds.append(kind)
    frame, t, placed = faceplate_module(holder, u0, 2.0, 1, 0, 2, extras=extras)
    return frame, np.concatenate(placed), SBC_SLOT_Y[1] - SBC_SLOT_Y[0]


def main():
    os.makedirs(OUT, exist_ok=True)
    # internal z = 0 is the bottom of the lowest post (keeps the U maths simple); exported files
    # put z = 0 on the floor: Top Edge (35) + foot (12) below the posts.
    foot_h = float(np.ptp(read_stl(SRC["foot"])[:, 2]))
    Z_FLOOR[0] = TE_H + foot_h
    posts, joiners, post_h = frame_tris()
    write_stl(os.path.join(OUT, "frame_posts.stl"), posts)
    write_stl(os.path.join(OUT, "frame_joiners.stl"), joiners)
    feet, panels, sidep, frames, handles = enclosure_tris()
    write_stl(os.path.join(OUT, "feet.stl"), feet)
    write_stl(os.path.join(OUT, "bottom_panel.stl"), panels)
    write_stl(os.path.join(OUT, "side_panels.stl"), sidep)
    write_stl(os.path.join(OUT, "frames.stl"), frames)
    write_stl(os.path.join(OUT, "handles.stl"), handles)

    layout = {"U_mm": U, "total_U": TOTAL_U, "rack_outside_depth": RACK_OUT,
              "z_floor_mm": round(Z_FLOOR[0], 2),        # U0 sits this far above the floor
              "clear_width": 2 * CLEAR_X, "post_height_mm": round(float(post_h), 2),
              "enclosure": {"feet": 4, "bottom_panel": 1, "side_panels": 2 * N_POSTS,
                            "horizontal_edges": 4, "edges": 4},
              "modules": []}
    for key, label, u0, uh, kind, col in MODULES:
        # shift up by HOLE_UP hole positions from the module's lowest screw hole (15.875 or 12.7 mm
        # depending on where in the U that hole is); u0 becomes fractional
        k = BASE_HOLE.get(key, int(round(u0 * 3)))
        u0 = u0 + (hole_z(k + HOLE_UP_BY.get(key, HOLE_UP)) - hole_z(k)) / U
        z0, z1 = u0 * U, (u0 + uh) * U
        rec = {"key": key, "label": label, "U_from_bottom": round(u0, 4), "U_height": uh,
               "z_mm": [round(z0 + Z_FLOOR[0], 1), round(z1 + Z_FLOOR[0], 1)], "source": kind,
               "colour": f"#{col:06x}"}
        if kind == "gpu":
            sh = read_stl(SRC["gpu_shelf"]); sh[:, 2] += z0
            fp = read_stl(SRC["gpu_face"]);  fp[:, 2] += z0
            cd = read_stl(SRC["gpu_card"]);  cd[:, 2] += z0        # same frame as the shelf
            write_stl(os.path.join(OUT, "gpu_shelf.stl"), sh)
            write_stl(os.path.join(OUT, "gpu_faceplate.stl"), fp)
            write_stl(os.path.join(OUT, "gpu_card.stl"), cd)
            rec["files"] = ["gpu_shelf", "gpu_faceplate", "gpu_card"]
        elif kind == "sbc":
            frame, filled, pitch = sbc_row(u0)
            write_stl(os.path.join(OUT, "sbc_frame.stl"), frame)
            write_stl(os.path.join(OUT, "sbc_holders.stl"), filled)
            stale = os.path.join(OUT, "sbc_empty.stl")
            if os.path.exists(stale):
                os.remove(stale)                # the old placeholder block for the empty slot
            rec["files"] = ["sbc_frame", "sbc_holders"]
            rec["slot_pitch_mm"] = round(float(pitch), 2)
            rec["slots"] = [{"pi4": "Pi 4", "pi5": "Pi 5 / Pi 3"}.get(s, "empty") for s in SBC_SLOTS]
            rec["row_width_mm"] = round(float(7 * pitch), 1)
        elif kind == "air":
            rec["files"] = []
        elif kind == "real":
            fn, wax, hax, dax, hflip, occ = REAL[key]
            hw = HARDWARE.get(key)
            if hw:
                import sys
                if HERE not in sys.path:
                    sys.path.insert(0, HERE)
                import _hardware
                part = getattr(_hardware, hw)()
                if key == "pc_psu":
                    part = part.copy(); part[:, 2] += PSU_LIFT          # sits on the open shelf floor
                q, _, (h,) = faceplate_module(read_stl(fn), u0, occ, wax, hax, dax, hflip,
                                              extras=[part], y_shift=Y_SHIFT.get(key, 0.0))
                if key in REAR:
                    h = to_rear(h)
                write_stl(os.path.join(OUT, f"{key}_hw.stl"), h)
                rec["files"] = [key, f"{key}_hw"]
            else:
                q, _ = faceplate_module(read_stl(fn), u0, occ, wax, hax, dax, hflip,
                                        dflip=key in DEPTH_FLIP, ear_t=EAR_T.get(key),
                                        y_shift=Y_SHIFT.get(key, 0.0))
                rec["files"] = [key]
            if key in REAR:
                q = to_rear(q)
                rec["rear"] = True
            if key == "psu_shelf":
                rec["shares_U"] = True
            write_stl(os.path.join(OUT, f"{key}.stl"), q)
        else:
            write_stl(os.path.join(OUT, f"{key}.stl"), shelf_tris(u0, uh))
            rec["files"] = [key]
        layout["modules"].append(rec)

    used = sum(m["U_height"] for m in layout["modules"] if not m.get("shares_U"))
    layout["used_U"] = used
    layout["free_U"] = round(TOTAL_U - used, 2)
    with open(os.path.join(OUT, "LAYOUT.json"), "w") as f:
        json.dump(layout, f, indent=1)
    return layout


if __name__ == "__main__":
    L = main()
    print(f"{L['total_U']:.0f}U rack  ({N_POSTS} x {UNITS_PER_POST}U posts + "
          f"{N_POSTS - 1} x {JOINER_U:.0f}U joiners), post height {L['post_height_mm']} mm")
    for m in L["modules"]:
        print(f"  U{m['U_from_bottom']:>5.1f} .. U{m['U_from_bottom'] + m['U_height']:<5.1f} "
              f"z {m['z_mm'][0]:>6.1f}-{m['z_mm'][1]:<6.1f}  {m['source']:5} {m['label']}")
    print(f"  used {L['used_U']}U, free {L['free_U']}U of {L['total_U']:.0f}U")
