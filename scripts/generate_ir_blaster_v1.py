#!/usr/bin/env python3
"""Generate the IR Blaster V1 KiCad board and supporting source artifacts."""

from __future__ import annotations

import csv
import json
import math
import shutil
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMD = "--smd" in sys.argv
PROJECT = "ir_blaster_v2_smd" if SMD else "ir_blaster_v1"
OUT = ROOT / PROJECT
BOARD = OUT / f"{PROJECT}.kicad_pcb"
CX = CY = 100.0
R_BOARD = 37.0
BOARD_DIAMETER_MM = 74.0


def uid() -> str:
    return str(uuid.uuid4())


def xy_at(radius: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg - 90.0)
    return CX + radius * math.cos(a), CY + radius * math.sin(a)


def fmt(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def at(x: float, y: float, deg: float | None = None) -> str:
    return f"(at {fmt(x)} {fmt(y)}" + (f" {fmt(deg)}" if deg is not None else "") + ")"


def fp_text(kind: str, text: str, x: float, y: float, size: float = 0.8, layer: str = "F.SilkS", hide: bool = False) -> str:
    hidden = " hide" if hide else ""
    return f'''    (property "{kind}" "{text}" {at(x, y)} (layer "{layer}"){hidden}
      (effects (font (size {size} {size}) (thickness 0.13)))
    )'''


def led_fp(ref: str, value: str, x: float, y: float, rot: float, anet: int, wide: bool) -> str:
    body = "rect" if wide else "circle"
    shape = ('(fp_rect (start -2.5 -1.35) (end 2.5 1.35)\n'
             '      (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))') if wide else (
             '(fp_circle (center 0 0) (end 2.6 0)\n'
             '      (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))')
    return f'''  (footprint "IR_Blaster:{'OSI5LA7WA1B' if wide else 'OSI5LA5A33A-B'}" (layer "F.Cu")
    {at(x, y, rot)}
{fp_text('Reference', ref, 0, -3.7)}
{fp_text('Value', value, 0, 3.7, layer='F.Fab', hide=True)}
    {shape}
    (fp_line (start 1.8 -2.1) (end 1.8 2.1) (stroke (width 0.45) (type default)) (layer "F.SilkS"))
    (fp_text user "A" (at -1.27 2.8 {fmt(-rot)}) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.13))))
    (fp_text user "K" (at 1.27 2.8 {fmt(-rot)}) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.13))))
    (fp_text user "OUT →" (at 0 -4.8 {fmt(-rot)}) (layer "F.SilkS") (effects (font (size 0.65 0.65) (thickness 0.11))))
    (attr through_hole exclude_from_pos_files exclude_from_bom)
    (pad "1" thru_hole rect (at -1.27 0 {fmt(rot)}) (size 2 2) (drill 0.9) (layers "*.Cu" "*.Mask") (net {anet} "{ref}_A"))
    (pad "2" thru_hole circle (at 1.27 0 {fmt(rot)}) (size 2 2) (drill 0.9) (layers "*.Cu" "*.Mask") (net 3 "LED_DRAIN"))
    (model "${{KICAD9_3DMODEL_DIR}}/LED_THT.3dshapes/LED_D5.0mm_IRGrey.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
  )'''


def resistor_fp(ref: str, value: str, x: float, y: float, rot: float, net1: int, name1: str, net2: int, name2: str, dnp: bool = False) -> str:
    if SMD:
        power = ref.startswith("R") and ref[1:].isdigit()
        half = 1.8 if power else 0.95
        pad_x = 1.4 if power else 0.9
        pad_y = 1.8 if power else 0.95
        body_x = 1.6 if power else 0.8
        body_y = 0.9 if power else 0.45
        package = "R_1206_3216Metric" if power else "R_0603_1608Metric"
        return f'''  (footprint "Resistor_SMD:{package}" (layer "F.Cu")
    {at(x, y, rot)}
{fp_text('Reference', ref, 0, -2.0 if power else -1.3, 0.65)}
{fp_text('Value', value, 0, 2.0, layer='F.Fab', hide=True)}
    (fp_rect (start -{body_x} -{body_y}) (end {body_x} {body_y}) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))
    (attr smd)
    (pad "1" smd roundrect (at -{half} 0 {fmt(rot)}) (size {pad_x} {pad_y}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (net {net1} "{name1}"))
    (pad "2" smd roundrect (at {half} 0 {fmt(rot)}) (size {pad_x} {pad_y}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (net {net2} "{name2}"))
  )'''
    attrs = " through_hole" + (" exclude_from_pos_files exclude_from_bom" if dnp else "")
    return f'''  (footprint "IR_Blaster:R_Axial_DIN0207_P10.16mm" (layer "F.Cu")
    {at(x, y, rot)}
{fp_text('Reference', ref, 0, -2.0)}
{fp_text('Value', value, 0, 2.0, layer='F.Fab', hide=True)}
    (fp_rect (start -3.5 -1.25) (end 3.5 1.25) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))
    (fp_line (start -5.08 0) (end -3.5 0) (stroke (width 0.2) (type default)) (layer "F.SilkS"))
    (fp_line (start 3.5 0) (end 5.08 0) (stroke (width 0.2) (type default)) (layer "F.SilkS"))
    (attr{attrs})
    (pad "1" thru_hole circle (at -5.08 0 {fmt(rot)}) (size 2 2) (drill 0.9) (layers "*.Cu" "*.Mask") (zone_connect 2) (net {net1} "{name1}"))
    (pad "2" thru_hole circle (at 5.08 0 {fmt(rot)}) (size 2 2) (drill 0.9) (layers "*.Cu" "*.Mask") (zone_connect 2) (net {net2} "{name2}"))
    (model "${{KICAD9_3DMODEL_DIR}}/Resistor_THT.3dshapes/R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
  )'''


def simple_2pin_fp(ref: str, value: str, x: float, y: float, pitch: float, net1: tuple[int, str], net2: tuple[int, str], polarized: bool = False) -> str:
    marker = '(fp_text user "+" (at -4 -2.5) (layer "F.SilkS") (effects (font (size 1.5 1.5) (thickness 0.25))))' if polarized else ""
    return f'''  (footprint "IR_Blaster:{ref}_{value}" (layer "F.Cu")
    {at(x, y)}
{fp_text('Reference', ref, 0, -3.0)}
{fp_text('Value', value, 0, 3.0, layer='F.Fab', hide=True)}
    (fp_circle (center 0 0) (end 4 0) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))
    {marker}
    (attr through_hole)
    (pad "1" thru_hole rect (at {fmt(-pitch/2)} 0) (size 2.2 2.2) (drill 1.0) (layers "*.Cu" "*.Mask") (net {net1[0]} "{net1[1]}"))
    (pad "2" thru_hole circle (at {fmt(pitch/2)} 0) (size 2.2 2.2) (drill 1.0) (layers "*.Cu" "*.Mask") (net {net2[0]} "{net2[1]}"))
  )'''


def header_fp(ref: str, x: float, y0: float, left: bool) -> str:
    pin_names_left = ["3V3", "EN", "VP", "VN", "IO34", "IO35", "IO32", "IO33", "GPIO25", "IO26", "IO27", "IO14", "IO12", "GND", "IO13", "D2", "D3", "CMD", "5V"]
    pin_names_right = ["GND", "IO23", "IO22", "TX", "RX", "IO21", "GND", "IO19", "IO18", "IO5", "IO17", "IO16", "IO4", "IO0", "IO2", "IO15", "D1", "D0", "CLK"]
    names = pin_names_left if left else pin_names_right
    pads = []
    for i, name in enumerate(names, 1):
        net = None
        if left and name == "GPIO25": net = (4, "IR_TX")
        elif left and name == "5V": net = (1, "+5V")
        elif left and name == "GND": net = (2, "GND")
        net_s = f' (net {net[0]} "{net[1]}")' if net else ""
        shape = "rect" if i == 1 else "circle"
        pads.append(f'    (pad "{i}" thru_hole {shape} (at 0 {fmt((i-1)*2.54)}) (size 1.8 1.8) (drill 1.0) (layers "*.Cu" "*.Mask"){net_s})')
    return f'''  (footprint "IR_Blaster:ESP32_DevKitC_V4_1x19" (layer "B.Cu")
    {at(x, y0)}
{fp_text('Reference', ref, 0, -2.2, layer='B.SilkS')}
{fp_text('Value', 'ESP32_DEVKITC_SOCKET_DNP', 0, 48.0, layer='B.Fab', hide=True)}
    (fp_rect (start -1.6 -1.6) (end 1.6 47.3) (stroke (width 0.25) (type default)) (fill none) (layer "B.SilkS"))
    (attr through_hole exclude_from_pos_files exclude_from_bom)
{chr(10).join(pads)}
    (model "${{KICAD9_3DMODEL_DIR}}/Connector_PinSocket_2.54mm.3dshapes/PinSocket_1x19_P2.54mm_Vertical.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 180 0)))
  )'''


def q_fp() -> str:
    if SMD:
        return f'''  (footprint "Package_TO_SOT_SMD:SOT-23" (layer "F.Cu")
    {at(100, 116)}
{fp_text('Reference', 'Q1', 0, -2.3)}
{fp_text('Value', 'AO3400A', 0, 2.3, layer='F.Fab', hide=True)}
    (fp_rect (start -1.6 -1.5) (end 1.6 1.5) (stroke (width 0.18) (type default)) (fill none) (layer "F.SilkS"))
    (attr smd)
    (pad "1" smd roundrect (at -1 -0.95) (size 1 1.1) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (net 5 "GATE"))
    (pad "2" smd roundrect (at -1 0.95) (size 1 1.1) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (net 2 "GND"))
    (pad "3" smd roundrect (at 1 0) (size 1 1.1) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (net 3 "LED_DRAIN"))
  )'''
    return f'''  (footprint "IR_Blaster:INK021ABS1_TO92S" (layer "F.Cu")
    {at(100, 116)}
{fp_text('Reference', 'Q1', 0, -3.2)}
{fp_text('Value', 'INK021ABS1-T112', 0, 3.2, layer='F.Fab', hide=True)}
    (fp_rect (start -4 -2.0) (end 4 2.0) (stroke (width 0.3) (type default)) (fill none) (layer "F.SilkS"))
    (fp_text user "S   D   G" (at 0 3.0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.14))))
    (attr through_hole)
    (pad "1" thru_hole rect (at -2.5 0) (size 2 2) (drill 0.9) (layers "*.Cu" "*.Mask") (net 2 "GND"))
    (pad "2" thru_hole circle (at 0 0) (size 2 2) (drill 0.9) (layers "*.Cu" "*.Mask") (net 3 "LED_DRAIN"))
    (pad "3" thru_hole circle (at 2.5 0) (size 2 2) (drill 0.9) (layers "*.Cu" "*.Mask") (net 5 "GATE"))
    (model "${{KICAD9_3DMODEL_DIR}}/Package_TO_SOT_THT.3dshapes/TO-92_Inline.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
  )'''


def tp_fp(ref: str, label: str, x: float, y: float, net: tuple[int, str]) -> str:
    return f'''  (footprint "IR_Blaster:TestPoint_D2.0mm" (layer "F.Cu")
    {at(x, y)}
{fp_text('Reference', ref, 0, -2.0, 0.65)}
{fp_text('Value', label, 0, 2.0, 0.65, 'F.SilkS')}
    (attr through_hole exclude_from_bom exclude_from_pos_files)
    (pad "1" thru_hole circle (at 0 0) (size 2.4 2.4) (drill 1.0) (layers "*.Cu" "*.Mask") (net {net[0]} "{net[1]}"))
  )'''


def cdec_fp() -> str:
    if not SMD:
        return simple_2pin_fp("Cdec", "100nF", 102, 101, 2.54, (1, "+5V"), (2, "GND"))
    return f'''  (footprint "Capacitor_SMD:C_0603_1608Metric" (layer "F.Cu")
    {at(102, 101)}
{fp_text('Reference', 'Cdec', 0, -1.5, 0.65)}
{fp_text('Value', '100nF', 0, 1.5, layer='F.Fab', hide=True)}
    (attr smd)
    (pad "1" smd roundrect (at -0.9 0) (size 0.9 0.95) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (net 1 "+5V"))
    (pad "2" smd roundrect (at 0.9 0) (size 0.9 0.95) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (net 2 "GND"))
  )'''


def segment(a: tuple[float, float], b: tuple[float, float], width: float, layer: str, net: int) -> str:
    return f'  (segment (start {fmt(a[0])} {fmt(a[1])}) (end {fmt(b[0])} {fmt(b[1])}) (width {fmt(width)}) (layer "{layer}") (net {net}))'


def via(x: float, y: float, net: int) -> str:
    return f'  (via (at {fmt(x)} {fmt(y)}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net {net}))'


def ring(radius: float, width: float, net: int, layer: str, steps: int = 48) -> list[str]:
    pts = [xy_at(radius, i * 360 / steps) for i in range(steps)]
    return [segment(pts[i], pts[(i + 1) % steps], width, layer, net) for i in range(steps)]


def circle_zone(radius: float, net: int, name: str, layer: str, steps: int = 64) -> str:
    pts = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in [xy_at(radius, i * 360 / steps) for i in range(steps)])
    return f'''  (zone (net {net}) (net_name "{name}") (layer "{layer}") (hatch edge 0.5)
    (connect_pads (clearance 0.25))
    (min_thickness 0.25)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon (pts {pts}))
  )'''


def board_text(text: str, x: float, y: float, size: float = 1.0, justify: str = "") -> str:
    just = f" (justify {justify})" if justify else ""
    return f'''  (gr_text "{text}" {at(x, y)} (layer "F.SilkS")
    (effects (font (size {size} {size}) (thickness {fmt(max(0.15, size*0.16))})){just})
  )'''


def generate_board() -> None:
    nets = ['  (net 0 "")', '  (net 1 "+5V")', '  (net 2 "GND")', '  (net 3 "LED_DRAIN")', '  (net 4 "IR_TX")', '  (net 5 "GATE")']
    for i in range(1, 13):
        nets.append(f'  (net {5+i} "D{i}_A")')

    fps: list[str] = []
    led_points = []
    res_points = []
    for i, deg in enumerate(range(0, 360, 30), 1):
        wide = deg % 90 == 0
        lx, ly = xy_at(32.2, deg)
        resistor_radius = (15.0 if SMD and deg in (30, 330) else 22.0) if SMD else 24.7
        rx, ry = xy_at(resistor_radius, deg)
        # KiCad footprint local +X points outward when rotated by (radial angle - 90°).
        footprint_rot = 90 - deg
        fps.append(led_fp(f"D{i}", "OSI5LA7WA1B" if wide else "OSI5LA5A33A-B", lx, ly, footprint_rot, 5+i, wide))
        fps.append(resistor_fp(f"R{i}", "100R 0.25W", rx, ry, footprint_rot, 1, "+5V", 5+i, f"D{i}_A"))
        led_points.append((deg, lx, ly))
        res_points.append((deg, rx, ry))

    fps += [
        header_fp("J1", 87.3, 72.0, True),
        header_fp("J2", 112.7, 72.0, False),
        q_fp(),
        resistor_fp("RG", "220R", 104, 109, -90, 4, "IR_TX", 5, "GATE"),
        resistor_fp("RPD", "10k", 108, 116, -90, 5, "GATE", 2, "GND"),
        simple_2pin_fp("Cbulk", "1000uF_10V", 94, 106, 5.0, (1, "+5V"), (2, "GND"), True),
        cdec_fp(),
        tp_fp("TP1", "5V", 94, 95, (1, "+5V")),
        tp_fp("TP2", "GND", 106, 95, (2, "GND")),
        tp_fp("TP3", "IR_TX", 96, 102, (4, "IR_TX")),
        tp_fp("TP4", "DRAIN", 103, 120, (3, "LED_DRAIN")),
    ]

    tracks: list[str] = []
    tracks += ring(34.1, 0.8, 3, "B.Cu")
    for i, (deg, lx, ly) in enumerate(led_points, 1):
        ux, uy = math.cos(math.radians(deg - 90)), math.sin(math.radians(deg - 90))
        resistor_radius = (15.0 if SMD and deg in (30, 330) else 22.0) if SMD else 24.7
        resistor_half = 1.8 if SMD else 5.08
        res_in = xy_at(resistor_radius - resistor_half, deg)
        res_out = xy_at(resistor_radius + resistor_half, deg)
        led_an = (lx - 1.27 * ux, ly - 1.27 * uy)
        led_k = (lx + 1.27 * ux, ly + 1.27 * uy)
        ringd = xy_at(34.1, deg)
        if SMD and deg in (30, 330):
            through_y = 83.43
            outside_x = 114.9 if deg == 30 else 85.1
            inner_x = 110.5 if deg == 30 else 89.5
            tracks += [
                via(res_out[0], res_out[1], 5+i),
                segment(res_out, (inner_x, through_y), 0.2, "B.Cu", 5+i),
                segment((inner_x, through_y), (outside_x, through_y), 0.2, "B.Cu", 5+i),
                segment((outside_x, through_y), led_an, 0.2, "B.Cu", 5+i),
            ]
        else:
            tracks.append(segment(res_out, led_an, 0.6, "F.Cu", 5+i))
        tracks.append(segment(led_k, ringd, 1.0, "B.Cu", 3))

    # Header and central component connections.
    j1_gpio25 = (87.3, 72.0 + 8*2.54)
    tracks += [
        segment(j1_gpio25, (92, 92.32), 0.3, "F.Cu", 4),
        segment((92, 92.32), (98, 92.32), 0.3, "F.Cu", 4),
        segment((98, 92.32), (108, 92.32), 0.3, "F.Cu", 4),
        segment((108, 92.32), (110, 98), 0.3, "F.Cu", 4),
        segment((110, 98), (110, 104), 0.3, "F.Cu", 4),
        segment((116.9916, 90.19), (119.62, 100), 1.0, "F.Cu", 1),
    ]
    if SMD:
        tracks += [
            segment((101, 116), (103, 120), 0.8, "F.Cu", 3),
            segment((103, 120), xy_at(34.1, 165), 0.8, "B.Cu", 3),
            segment((110, 104), (104, 108.05), 0.3, "F.Cu", 4),
            segment((104, 109.95), (102, 112), 0.3, "F.Cu", 5),
            segment((102, 112), (99, 115.05), 0.3, "F.Cu", 5),
            segment((108, 115.05), (106, 113), 0.3, "F.Cu", 5),
            segment((106, 113), (102, 112), 0.3, "F.Cu", 5),
            segment((96, 102), (104, 108.05), 0.3, "F.Cu", 4),
            via(99, 116.95, 2),
            via(108, 116.95, 2),
            via(102.9, 101, 2),
        ]
    else:
        tracks += [
            segment((100, 116), (103, 120), 0.8, "B.Cu", 3),
            segment((103, 120), xy_at(34.1, 165), 0.8, "B.Cu", 3),
            segment((110, 104), (104, 103.92), 0.3, "F.Cu", 4),
            segment((104, 114.08), (102.5, 116), 0.3, "F.Cu", 5),
            segment((108, 110.92), (102.5, 116), 0.3, "F.Cu", 5),
            segment((96, 102), (104, 103.92), 0.3, "F.Cu", 4),
        ]

    silks = [
        board_text("IR BLASTER V2 SMD" if SMD else "IR BLASTER V1", 100, 92, 1.2),
        board_text("12 x 940nm / GPIO25", 100, 94.5, 0.75),
        board_text("USB ↓", 100, 133.5, 1.1),
        board_text("ESP32 ANTENNA EDGE ↑", 100, 64.2, 0.7),
        board_text("LED + SOCKETS: DNP / USER SOLDER", 100, 129.8, 0.62),
        board_text("SMD PASSIVES + AO3400A PCBA" if SMD else "THT DRIVER COMPONENTS", 100, 127.8, 0.58),
        board_text("5V", 84.5, 118.0, 0.7),
        board_text("GND", 84.0, 105.0, 0.7),
        board_text("GPIO25", 83.0, 92.3, 0.65),
    ]

    pcb = f'''(kicad_pcb (version 20240108) (generator pcbnew)
  (general (thickness 1.6))
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "b.silkscreen")
    (37 "F.SilkS" user "f.silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (44 "Edge.Cuts" user)
  )
  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))
{chr(10).join(nets)}
{chr(10).join(fps)}
{chr(10).join(silks)}
  (gr_circle (center {CX} {CY}) (end {CX+R_BOARD} {CY}) (stroke (width 0.25) (type default)) (fill none) (layer "Edge.Cuts"))
  (gr_rect (start 86.03 70.71) (end 113.97 119.0) (stroke (width 0.15) (type dash)) (fill none) (layer "Dwgs.User"))
{chr(10).join(tracks)}
{circle_zone(22.5, 1, '+5V', 'F.Cu')}
{circle_zone(22.0, 2, 'GND', 'B.Cu')}
)\n'''
    BOARD.write_text(pcb)


def generate_schematic() -> None:
    # Valid KiCad schematic overview. PCB connectivity is authoritative and fully DRC checked.
    def text(t, x, y, s=1.27):
        esc = t.replace('"', '\\"')
        return f'''  (text "{esc}" (exclude_from_sim no) (at {x} {y} 0) (effects (font (size {s} {s})) (justify left bottom)) (uuid "{uid()}"))'''
    items = [text(("IR BLASTER V2 SMD" if SMD else "IR BLASTER V1") + " — GPIO25 low-side switched 12-channel IR emitter", 20, 18, 1.6)]
    items += [text("ELECTRICAL NETLIST (PCB is authoritative)", 20, 28, 1.2)]
    for i in range(12):
        y = 38 + i * 7.5
        items += [text(f"+5V -> R{i+1} 100R -> D{i+1} anode; D{i+1} cathode -> LED_DRAIN", 25, y, 0.9)]
    items += [text("LED_DRAIN -> Q1 pin 2 DRAIN; Q1 pin 1 SOURCE -> GND", 25, 132, 0.95)]
    items += [text("GPIO25 / IR_TX -> RG 220R -> Q1 pin 3 GATE", 25, 140, 0.95)]
    items += [text("RPD 10k: GATE -> GND", 25, 148, 0.95), text("Cbulk 1000uF + Cdec 100nF: +5V -> GND", 25, 156, 0.95)]
    items += [text("D1,D4,D7,D10 = OSI5LA7WA1B wide 100°; remaining LEDs = OSI5LA5A33A-B narrow 30°", 25, 166, 0.85)]
    items += [text("Confirmed mapping: both LED types pin 1=A, pin 2=K; Q1 pin 1=S, pin 2=D, pin 3=G", 25, 174, 0.85)]
    sch = f'''(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "9.0")
  (uuid "{uid()}")
  (paper "A4")
  (lib_symbols)
{chr(10).join(items)}
  (sheet_instances (path "/" (page "1")))
  (embedded_fonts no)
)\n'''
    (OUT / f"{PROJECT}.kicad_sch").write_text(sch)


def generate_project() -> None:
    pro = {
        "boards": [], "cvpcb": {}, "erc": {}, "libraries": {},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [
                {"bus_width": 12, "clearance": 0.25, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": "Default", "pcb_color": "rgba(0,0,0,0)", "schematic_color": "rgba(0,0,0,0)", "track_width": 0.3, "via_diameter": 0.8, "via_drill": 0.4, "wire_width": 6},
                {"bus_width": 12, "clearance": 0.25, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": "IR_POWER", "pcb_color": "rgba(255,128,0,1)", "schematic_color": "rgba(255,128,0,1)", "track_width": 1.0, "via_diameter": 1.0, "via_drill": 0.5, "wire_width": 6}
            ],
            "meta": {"version": 3}, "net_colors": None,
            "netclass_assignments": {"+5V": "IR_POWER", "GND": "IR_POWER", "LED_DRAIN": "IR_POWER"}, "netclass_patterns": []
        },
        "pcbnew": {}, "schematic": {}, "sheets": [], "text_variables": {"BOARD_DIAMETER_MM": "74.0"}
    }
    (OUT / f"{PROJECT}.kicad_pro").write_text(json.dumps(pro, indent=2, ensure_ascii=False) + "\n")


def generate_bom() -> None:
    if SMD:
        rows = [
            ["D1,D4,D7,D10", 4, "940nm IR LED wide 100°", "OSI5LA7WA1B", "OptoSupply", "OSI5LA7WA1B", "DNP", "THT / DNP", "User hand solder; pin 1=A, 2=K"],
            ["D2,D3,D5,D6,D8,D9,D11,D12", 8, "940nm IR LED narrow 30°", "OSI5LA5A33A-B", "OptoSupply", "OSI5LA5A33A-B", "DNP", "THT / DNP", "User hand solder; pin 1=A, 2=K"],
            ["R1-R12", 12, "100R 0.25W", "R_1206_3216Metric", "UNI-ROYAL", "1206W4F1000T5E", "C17901", "SMT / top", "1206 selected for pulse-power margin"],
            ["RG", 1, "220R", "R_0603_1608Metric", "UNI-ROYAL", "0603WAF2200T5E", "C22962", "SMT / top", "Gate series resistor"],
            ["RPD", 1, "10k", "R_0603_1608Metric", "UNI-ROYAL", "0603WAF1002T5E", "C25804", "SMT / top", "Gate pull-down"],
            ["Q1", 1, "AO3400A", "SOT-23", "Alpha & Omega Semiconductor", "AO3400A", "C20917", "SMT / top", "Logic-level N-MOSFET; 1=G 2=S 3=D"],
            ["Cdec", 1, "100nF 50V X7R", "C_0603_1608Metric", "Samsung Electro-Mechanics", "CL10B104KB8NNNC", "C14663", "SMT / top", "Local decoupling"],
            ["Cbulk", 1, "1000uF 10V", "Radial P5.0mm", "TBD", "1000uF >=10V radial", "DNP", "THT / DNP", "Cost option: user hand solder; diameter <=8mm"],
            ["J1,J2", 2, "1x19 2.54mm socket", "ESP32_DevKitC_V4_1x19", "User supplied", "2.54mm female socket 1x19", "DNP", "THT / DNP", "User hand solder; 25.40mm row spacing"],
        ]
        with (OUT / "BOM.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Reference", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "JLC/LCSC", "Assembly method", "Notes"])
            w.writerows(rows)
        with (OUT / "assembly" / "BOM_JLCPCB.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
            for r in rows[2:7]:
                if r[0] == "R1-R12":
                    for i in range(1, 13):
                        w.writerow([r[2], f"R{i}", r[3], r[6]])
                else:
                    w.writerow([r[2], r[0], r[3], r[6]])
        with (OUT / "assembly" / "CPL_JLCPCB.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for i, deg in enumerate(range(0, 360, 30), 1):
                radius = 15.0 if deg in (30, 330) else 22.0
                x, y = xy_at(radius, deg)
                w.writerow([f"R{i}", f"{x:.3f}mm", f"{y:.3f}mm", "Top", 90-deg])
            w.writerows([
                ["RG", "104.000mm", "109.000mm", "Top", -90],
                ["RPD", "108.000mm", "116.000mm", "Top", -90],
                ["Q1", "100.000mm", "116.000mm", "Top", 0],
                ["Cdec", "102.000mm", "101.000mm", "Top", 0],
            ])
        return
    rows = []
    rows.append(["D1,D4,D7,D10", 4, "940nm IR LED wide 100°", "OSI5LA7WA1B", "OptoSupply", "OSI5LA7WA1B", "Not verified in live JLC library", "THT / DNP", "User hand solder; pin 1=A, 2=K"])
    rows.append(["D2,D3,D5,D6,D8,D9,D11,D12", 8, "940nm IR LED narrow 30°", "OSI5LA5A33A-B", "OptoSupply", "OSI5LA5A33A-B", "Not verified in live JLC library", "THT / DNP", "User hand solder; pin 1=A, 2=K"])
    rows.append(["R1-R12", 12, "100R 0.25W", "R_Axial_DIN0207_P10.16mm", "TBD", "100 ohm axial 1/4W", "Select exact stocked wave-solder part at order", "THT / wave/manual", "PCBA candidate"])
    rows.append(["RG", 1, "220R 0.25W", "R_Axial_DIN0207_P10.16mm", "TBD", "220 ohm axial 1/4W", "Select exact stocked wave-solder part at order", "THT / wave/manual", "PCBA candidate"])
    rows.append(["RPD", 1, "10k 0.25W", "R_Axial_DIN0207_P10.16mm", "TBD", "10k axial 1/4W", "Select exact stocked wave-solder part at order", "THT / wave/manual", "PCBA candidate"])
    rows.append(["Q1", 1, "N-MOSFET", "INK021ABS1_TO92S", "ISAHAYA Electronics", "INK021ABS1-T112", "No exact JLC result verified", "THT / global sourcing or consigned", "Do not substitute without approval; 1=S 2=D 3=G"])
    rows.append(["Cbulk", 1, "1000uF 10V", "Radial P5.0mm", "TBD", "1000uF >=10V radial", "Select exact stocked wave-solder part at order", "THT / wave/manual", "Verify diameter <=8mm"])
    rows.append(["Cdec", 1, "100nF", "Radial P2.54mm", "TBD", "100nF leaded ceramic", "Select exact stocked wave-solder part at order", "THT / wave/manual", "PCBA candidate"])
    rows.append(["J1,J2", 2, "1x19 2.54mm socket", "ESP32_DevKitC_V4_1x19", "User supplied", "2.54mm female socket 1x19", "N/A", "THT / DNP", "User hand solder; 25.40mm row spacing"])
    with (OUT / "BOM.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Reference", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "JLC/LCSC", "Assembly method", "Notes"])
        w.writerows(rows)
    # JLC upload candidate excludes user-DNP LEDs and sockets.
    with (OUT / "assembly" / "BOM_JLCPCB.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for r in rows[2:8]:
            w.writerow([r[2], r[0], r[3], "TBD_AT_ORDER"])
    (OUT / "assembly" / "CPL_JLCPCB.csv").write_text("Designator,Mid X,Mid Y,Layer,Rotation\n# THT wave/manual parts do not use SMT CPL coordinates; select through-hole service in portal.\n")


def main() -> None:
    for d in [OUT, OUT / "manufacturing", OUT / "assembly", OUT / "preview", OUT / "docs"]:
        d.mkdir(parents=True, exist_ok=True)
    generate_project()
    generate_schematic()
    generate_board()
    generate_bom()
    print(f"Generated {OUT}")


if __name__ == "__main__":
    main()
