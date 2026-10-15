"""Generic hardware placed on the real module CAD by its standard mounting holes.

  atx_psu()     ATX PSU, 150 x 86 x 140 (Corsair RM1000e 2025 size), in the coordinates of
                ATX+PSU+2U+Mount...stl (x across, y depth with the face at 0, z up). The mount's four
                o5 holes are at (41.42, 7.61) (179.42, 7.61) (179.42, 71.62) (65.42, 81.62): offsets
                (0,0) (138,0) (138,64) (24,74) = the ATX rear screw pattern, whose lower-left hole is
                6 mm in from the PSU's corner. So the PSU face is x 35.42..185.42, z 1.61..87.61, and
                it sits behind the 4 mm face plate.
  mitx_board()  generic mini-ITX board (170 x 170) on 6.35 mm standoffs, in the coordinates of
                "2U Mini ITX Computer Shelf.stl" (x across, y = height but stored upside down with the
                floor top at y 82.4, z depth with the face at 0). The shelf's M3 holes at x 43.67 /
                201.15 (157.48 apart) and z 38.67 / 170.75 and 15.81 / 170.75 (132.08 and 154.94) are
                mini-ITX holes H, C and J, F; C/F sit 10.16 in from the I/O edge, so the I/O edge is at
                z 180.91 (rear) and the board's left edge at x 37.32.
"""
import os, tempfile
import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))


def _tris(shape):
    f = os.path.join(tempfile.gettempdir(), "_hw.stl")
    cq.exporters.export(shape, f, tolerance=0.1, angularTolerance=0.3)
    import sys; sys.path.insert(0, HERE)
    from rack_layout import read_stl
    return read_stl(f)


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def atx_psu():
    x0, z0 = 41.42 - 6.0, 7.61 - 6.0
    W, H, D, plate = 150.0, 86.0, 140.0, 4.0
    body = _box(x0, x0 + W, plate, plate + D, z0, z0 + H)
    # rear panel as seen through the mount: IEC C14 inlet + rocker switch + exhaust grille
    body = body.cut(_box(x0 + 108, x0 + 136, plate - 0.1, plate + 3, z0 + 50, z0 + 70))       # IEC
    body = body.cut(_box(x0 + 112, x0 + 132, plate - 0.1, plate + 3, z0 + 20, z0 + 35))       # switch
    for i in range(7):                                                                          # grille
        body = body.cut(_box(x0 + 12 + i * 12, x0 + 18 + i * 12, plate - 0.1, plate + 2, z0 + 10, z0 + 76))
    # 120 mm fan on the bottom face
    fan = (cq.Workplane("XY").circle(58).circle(20).extrude(1.5)
           .translate((x0 + W / 2, plate + D / 2, z0 - 0.5)))
    return _tris(body.cut(fan))


def mitx_board():
    FLOOR, SO, PCB = 82.4, 6.35, 1.6
    U0, IO = 43.67 - 6.35, 170.75 + 10.16           # board left edge (x), I/O edge (z)

    def part(bu0, bu1, bv0, bv1, w0, w1):
        """board coords: bu from the left edge, bv from the I/O edge toward the front, w up from
        the shelf floor; -> shelf-file coords (x, y = FLOOR - w, z)"""
        return _box(U0 + bu0, U0 + bu1, FLOOR - w1, FLOOR - w0, IO - bv1, IO - bv0)
    top = SO + PCB
    parts = [part(0, 170, 0, 170, SO, top)]                                    # PCB
    parts.append(part(8, 160, -2, 22, top, top + 38))                          # rear I/O stack
    parts.append(part(52, 147, 28, 123, top, top + 53))                        # AXP90-X53 cooler (53 tall)
    parts.append(part(152, 158, 18, 151, top, top + 34))                       # DIMM A + RAM
    parts.append(part(160, 166, 18, 151, top, top + 34))                       # DIMM B + RAM
    parts.append(part(8, 98, 152, 161, top, top + 12))                         # PCIe x16 (front edge)
    parts.append(part(162, 169, 120, 150, top, top + 16))                      # 24-pin ATX
    for bu, bv in ((6.35, 10.16), (163.83, 10.16), (6.35, 142.24), (163.83, 165.10)):   # standoffs
        parts.append(cq.Workplane("XZ").polygon(6, 6.4).extrude(-SO)
                     .translate((U0 + bu, FLOOR - SO, IO - bv)))
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return _tris(out)


if __name__ == "__main__":
    for nm, fn in (("atx_psu", atx_psu), ("mitx_board", mitx_board)):
        t = fn(); v = t.reshape(-1, 3)
        print(f"{nm}: {len(t)} verts, bbox {v.min(0).round(2)} .. {v.max(0).round(2)}")
