# What nabaru has actually printed — real inventory

Source: the Neptune 4 Plus's own Moonraker history (83 jobs) joined against each plate's
`EXCLUDE_OBJECT_DEFINE` metadata, which the slicer writes with the **exact part name and outline
polygon for every object on the plate**. Counted only for jobs whose status is `completed`.

**Job names are unreliable** — they are the first object's name at slice time and were often
carried over from an earlier slice. Several plates named `5U+Vertical+Post` contain no posts at
all. Always read the plate contents, never the job name.

## Lab Rax frame

| Part | Footprint (slicer polygon) | Owned | Needed for 17U | Note |
|---|---|---|---|---|
| Rack_Edge = **the 5U vertical post** | 30.0 × 222.2 | **12** | 12 (4 per 5U section × 3) | Same 30 × 222.25 footprint as `5U+Vertical+Post.stl` lying on its 35 mm side, and only ever on plates named `5U+Vertical+Post`. Inferred from footprint + plate name; print height not yet checked (that g-code is only on the printer). |
| Solid_Horizontal_Edge | 61.1 × 282.2 | 2 | 2 (base) | 282.2 = the rack's full outside width |
| Ventilated_Horizontal_Edge | 61.1 × 282.2 | 2 | 2 (top) | interchangeable with the solid one |
| Top_Edge | 35.0 × 170.0 | 4 | 4 | 170 = inner front-to-rear gap |
| Handle | 23.0 × 170.0 | 2 | 2 | same 170 length and hole pattern as Top_Edge |
| Right_Front_Foot | 26.0 × 26.0 | 4 | 4 | printed, despite no foot job in the visible history |
| Brass_Insert_Post_Joiner | 39.7 × 23.8 | 4 | 4 | post-to-post joiner |
| 1U_Support_Extension_Brass_Insert_Version | 87.9 × 240.7 | **4** | 4 (2 per band × 2 bands) | exactly enough |
| labrax-hws (side panel) | 175.0 × 227.2 | **2** | **6** | short by 4 |
| Bottom_Panel_Hex_Ventilated | 228.0 × 171.5 | 1 | 1 | |
| Lab Rax Top Panel | — | **0** | 1 | never printed; the `Top_Panel_SmartiPi_*` jobs are a different project |

## Modules

| Part | Footprint | Owned |
|---|---|---|
| ATX_PSU_2U_Mount_-_Lab_Rax_extra_support_mounts | 88.8 × 252.0 | 1 |
| 2U_Mini_ITX_Computer_Shelf | 86.5 × 252.0 | 1 |
| 2U_7_SBC_Holder | 86.4 × 252.0 | 1 |
| Pi_Tray | 92.0 × 86.4 | 4 |
| 2U_Plate | 252.0 × 86.4 | 1 |
| keystone-blank-1_2u-10i-rm | 254.0 × 22.3 | 1 |
| obj_1_1U_Open_Shelf | 252.0 × 237.0 | 1 |
| 1U_Open_Shelf_140mm | 140.0 × 252.0 | 1 |
| Shelf_Support_Left / _Right (incl. SOLID variants) | 34.0 × 42.0 | 10 |
| PRINT_gpu_shelf_3u / gpu_faceplate_3u | ours | 1 each |

The 252–254 mm width and the ~86.4 (2U) / 22.3 (0.5U) heights confirm these are all Lab Rax
faceplate-style modules.

## Corrections this inventory forced

1. **Handles were printed** (2, hidden on a plate named `5U+Vertical+Post`). An earlier note said
   they never were.
2. **Feet were printed** (`Right_Front_Foot`, 4 off) — no job in the visible history says so.
3. ~~`Rack_Edge` was missing from the CAD~~ — **retracted.** `Rack_Edge` is the 5U vertical post
   under another object name (its footprint is the post's 30 × 222.25, and it only appears on
   `5U+Vertical+Post` plates). The CAD already has all 12.
4. The SBC row is **`2U_7_SBC_Holder` + 4 × `Pi_Tray`**, not the `Pi+4+Holder` / `Pi+5+Holder`
   STLs the layout currently draws.
5. The BOM's "Edge" (×4) is the printed **`Top_Edge`** (35 × 170, L-section): the left/right
   members of the base and top frames. The CAD already places them there.
6. The keystone plate also carried 9 Neptune printer parts (bed clamps, cable holder, screw),
   which is why the first whole-plate rebuild measured 34.8 mm tall instead of 22.2 mm.
   `_gcode_obj.py` now rebuilds a single object from its own EXCLUDE_OBJECT-tagged moves.

## Screw/insert budget (creator's BOM: 24 of each for the frame)

Creator: "Each of the four posts and four edge pieces need two brass inserts" = 16, plus the
inserts in the edge pieces for 2 handles and 4 feet. The guide doesn't state the per-handle /
per-foot count, so the split of the remaining 8 is not confirmed.
