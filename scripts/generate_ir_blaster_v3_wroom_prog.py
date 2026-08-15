#!/usr/bin/env python3
"""Generate the isolated WROOM factory-programming interface revision.

This revision intentionally lives beside V1/V2 and does not overwrite them.
It implements the WROOM module land pattern, UART0 programming nets, a DNP
1x6 prototype header, and bottom-side 2x3 pogo pads.
"""

from __future__ import annotations

import csv
import json
import re
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = "ir_blaster_v3_wroom_factory_prog"
OUT = ROOT / PROJECT
BOARD = OUT / f"{PROJECT}.kicad_pcb"
KICAD_FP = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")
CX = CY = 100.0
RADIUS = 37.0


NETS = {
    "GND": 1,
    "+3V3": 2,
    "U0TXD": 3,
    "U0RXD": 4,
    "EN": 5,
    "IO0": 6,
}


def uid() -> str:
    return str(uuid.uuid4())


def fmt(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def fp_text(kind: str, text: str, x: float, y: float, layer: str, size: float = 0.8, hide: bool = False) -> str:
    hidden = " hide" if hide else ""
    justify = ' (justify mirror)' if layer.startswith("B.") else ""
    return f'''    (property "{kind}" "{text}" (at {fmt(x)} {fmt(y)}) (layer "{layer}"){hidden}
      (effects (font (size {size} {size}) (thickness 0.13)){justify})
    )'''


def add_nets_to_pads(text: str, pad_map: dict[str, tuple[int, str]]) -> str:
    """Add board-net clauses to every matching pad block in a library footprint."""
    starts = list(re.finditer(r'\(pad\s+"([^"]+)"', text))
    for match in reversed(starts):
        pad = match.group(1)
        if pad not in pad_map:
            continue
        depth = 0
        end = None
        for i in range(match.start(), len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            raise ValueError(f"Unclosed pad {pad}")
        net_id, name = pad_map[pad]
        text = text[:end] + f'\n        (net {net_id} "{name}")' + text[end:]
    return text


def library_footprint(path: Path, ref: str, value: str, x: float, y: float,
                      pad_map: dict[str, tuple[int, str]], dnp: bool = False) -> str:
    src = path.read_text()
    first_nl = src.index("\n")
    body = src[first_nl + 1:src.rfind(")")]
    body = re.sub(r'^\s*\((version|generator|generator_version)[^\n]*\)\s*$', "", body, flags=re.M)
    body = re.sub(r'\(property "Reference" "[^"]+"', f'(property "Reference" "{ref}"', body, count=1)
    body = re.sub(r'\(property "Value" "[^"]+"', f'(property "Value" "{value}"', body, count=1)
    body = add_nets_to_pads(body, pad_map)
    if dnp:
        body = body.replace("(attr through_hole)", "(attr through_hole exclude_from_bom exclude_from_pos_files)")
    library_name = path.parent.name.removesuffix(".pretty")
    return f'''  (footprint "{library_name}:{path.stem}" (layer "F.Cu")
    (at {fmt(x)} {fmt(y)})
{body}
  )'''


def wroom_fp() -> str:
    path = KICAD_FP / "RF_Module.pretty" / "ESP32-WROOM-32E.kicad_mod"
    mapping = {
        "1": (NETS["GND"], "GND"),
        "2": (NETS["+3V3"], "+3V3"),
        "3": (NETS["EN"], "EN"),
        "25": (NETS["IO0"], "IO0"),
        "34": (NETS["U0RXD"], "U0RXD"),
        "35": (NETS["U0TXD"], "U0TXD"),
        "38": (NETS["GND"], "GND"),
        "39": (NETS["GND"], "GND"),
    }
    fp = library_footprint(path, "U1", "ESP32-WROOM-32E-N16", 100, 80, mapping)
    # KiCad's official footprint uses 0.20 mm thermal vias. Use JLCPCB's
    # standard-cost 0.30 mm finished drill while keeping the official pad grid.
    fp = fp.replace('(size 0.6 0.6)\n\t\t(drill 0.2)', '(size 0.7 0.7)\n\t\t(drill 0.3)')
    return fp


def prog_header_fp() -> str:
    path = KICAD_FP / "Connector_PinHeader_2.54mm.pretty" / "PinHeader_1x06_P2.54mm_Vertical.kicad_mod"
    names = ["+3V3", "GND", "U0TXD", "U0RXD", "EN", "IO0"]
    mapping = {str(i + 1): (NETS[name], name) for i, name in enumerate(names)}
    fp = library_footprint(path, "J_PROG", "PinHeader_1x06_P2.54mm_Vertical_DNP", 75.5, 91, mapping, True)
    fp = fp.replace('(at 75.5 91)', '(at 75.5 91)')
    return fp


def pogo_fp(ref: str, label: str, x: float, y: float, net: str, pin1: bool = False) -> str:
    shape = "rect" if pin1 else "circle"
    marker = '    (fp_poly (pts (xy -1.8 -1.8) (xy -0.8 -1.8) (xy -1.8 -0.8)) (stroke (width 0.2) (type default)) (fill yes) (layer "B.SilkS"))\n' if pin1 else ""
    return f'''  (footprint "FactoryProg:PogoPad_D2.4mm" (layer "B.Cu")
    (at {fmt(x)} {fmt(y)})
{fp_text('Reference', ref, 0, 2.2, 'B.SilkS', 0.6, True)}
{fp_text('Value', label, 2.4, 0, 'B.SilkS', 0.8)}
{marker}    (attr smd exclude_from_bom exclude_from_pos_files)
    (pad "1" smd {shape} (at 0 0) (size 2.4 2.4) (layers "B.Cu" "B.Mask") (net {NETS[net]} "{net}"))
  )'''


def via(x: float, y: float, net: str) -> str:
    return f'  (via (at {fmt(x)} {fmt(y)}) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net {NETS[net]}))'


def seg(a: tuple[float, float], b: tuple[float, float], net: str, layer: str = "F.Cu", width: float = 0.3) -> str:
    return f'  (segment (start {fmt(a[0])} {fmt(a[1])}) (end {fmt(b[0])} {fmt(b[1])}) (width {fmt(width)}) (layer "{layer}") (net {NETS[net]}))'


def board_text(text: str, x: float, y: float, layer: str = "F.SilkS", size: float = 0.8) -> str:
    return f'''  (gr_text "{text}" (at {fmt(x)} {fmt(y)}) (layer "{layer}")
    (effects (font (size {size} {size}) (thickness 0.15)){' (justify mirror)' if layer == 'B.SilkS' else ''})
  )'''


def generate_board() -> None:
    fps = [wroom_fp(), prog_header_fp()]
    pogo = [
        ("TP_PROG_3V3", "3V3", 84.5, 90.0, "+3V3", True),
        ("TP_PROG_GND", "GND", 84.5, 93.81, "GND", False),
        ("TP_PROG_TX", "TX", 84.5, 97.62, "U0TXD", False),
        ("TP_PROG_RX", "RX", 84.5, 101.43, "U0RXD", False),
        ("TP_PROG_EN", "EN", 84.5, 105.24, "EN", False),
        ("TP_PROG_IO0", "IO0", 84.5, 109.05, "IO0", False),
    ]
    fps.extend(pogo_fp(*p) for p in pogo)

    # Absolute module pad locations from the KiCad 9 footprint, verified against
    # the Espressif recommended land pattern.
    module = {
        "+3V3": (91.25, 76.01),
        "EN": (91.25, 77.28),
        "IO0": (108.75, 91.25),
        "U0RXD": (108.75, 79.82),
        "U0TXD": (108.75, 78.55),
        "GND": (91.25, 74.74),
    }
    header = {
        "+3V3": (75.5, 91.0),
        "GND": (75.5, 93.54),
        "U0TXD": (75.5, 96.08),
        "U0RXD": (75.5, 98.62),
        "EN": (75.5, 101.16),
        "IO0": (75.5, 103.70),
    }
    pogo_xy = {p[4]: (p[2], p[3]) for p in pogo}
    tracks: list[str] = []

    # The straight 1x6 factory array preserves the header pin order.  Short,
    # monotonic bottom routes are fixture-friendly and avoid pad crossings.
    for net in ["+3V3", "GND", "U0TXD", "U0RXD", "EN", "IO0"]:
        tracks.append(seg(header[net], pogo_xy[net], net, "B.Cu", 0.25))

    # Module routes branch at the through-hole header.  Long UART routes use
    # opposite layers; EN and IO0 use independent inner/bottom corridors.
    tracks += [
        # +3V3, front inner-top corridor.
        seg(header["+3V3"], (78.0, 86.0), "+3V3", "F.Cu"),
        seg((78.0, 86.0), (88.0, 86.0), "+3V3", "F.Cu"),
        seg((88.0, 86.0), (88.0, 76.01), "+3V3", "F.Cu"),
        seg((88.0, 76.01), module["+3V3"], "+3V3", "F.Cu"),

        # TX, bottom copper outer-top corridor, then via at the module pad.
        seg(header["U0TXD"], (73.5, 96.08), "U0TXD", "B.Cu"),
        seg((73.5, 96.08), (73.5, 120.0), "U0TXD", "B.Cu"),
        seg((73.5, 120.0), (115.5, 120.0), "U0TXD", "B.Cu"),
        seg((115.5, 120.0), (115.5, 78.55), "U0TXD", "B.Cu"),
        seg((115.5, 78.55), module["U0TXD"], "U0TXD", "B.Cu"),
        via(*module["U0TXD"], "U0TXD"),

        # RX, front copper outer-bottom corridor; clear of the antenna keepout.
        seg(header["U0RXD"], (74.0, 98.62), "U0RXD", "F.Cu"),
        seg((74.0, 98.62), (74.0, 122.5), "U0RXD", "F.Cu"),
        seg((74.0, 122.5), (117.0, 122.5), "U0RXD", "F.Cu"),
        seg((117.0, 122.5), (117.0, 79.82), "U0RXD", "F.Cu"),
        seg((117.0, 79.82), module["U0RXD"], "U0RXD", "F.Cu"),

        # EN, front copper inner-left corridor.
        seg(header["EN"], (89.0, 101.16), "EN", "F.Cu"),
        seg((89.0, 101.16), (89.0, 77.28), "EN", "F.Cu"),
        seg((89.0, 77.28), module["EN"], "EN", "F.Cu"),

        # IO0 branches from its factory pad on bottom copper and approaches
        # the right module pad through a dedicated inner-right corridor.
        seg(pogo_xy["IO0"], (112.0, 109.05), "IO0", "B.Cu"),
        seg((112.0, 109.05), (112.0, 91.25), "IO0", "B.Cu"),
        seg((112.0, 91.25), module["IO0"], "IO0", "B.Cu"),
        via(*module["IO0"], "IO0"),

        # Module side GND pads join the exposed-pad thermal-via ground plane.
        via(*module["GND"], "GND"),
        via(108.75, 74.74, "GND"),
    ]

    nets = ['  (net 0 "")'] + [f'  (net {num} "{name}")' for name, num in NETS.items()]
    texts = [
        board_text("IR BLASTER V3 / WROOM FACTORY PROG", 100, 128.0, size=0.85),
        board_text("ESP32 ANTENNA KEEP CLEAR", 100, 65.2, size=0.8),
        board_text("PROG", 68.0, 107.0, size=0.85),
        board_text("1 3V3", 71.5, 91.0, size=0.8),
        board_text("2 GND", 71.5, 93.54, size=0.8),
        board_text("3 TX", 71.5, 96.08, size=0.8),
        board_text("4 RX", 71.5, 98.62, size=0.8),
        board_text("5 EN", 71.5, 101.16, size=0.8),
        board_text("6 IO0", 71.5, 103.70, size=0.8),
        board_text("FACTORY PROG", 90.5, 112.5, "B.SilkS", 0.8),
        board_text("1x6 3.81mm", 90.5, 114.0, "B.SilkS", 0.8),
        board_text("PIN1", 79.5, 86.5, "B.SilkS", 0.8),
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
{chr(10).join(texts)}
  (gr_circle (center {CX} {CY}) (end {CX + RADIUS} {CY}) (stroke (width 0.25) (type default)) (fill none) (layer "Edge.Cuts"))
{chr(10).join(tracks)}
  (zone (net {NETS['GND']}) (net_name "GND") (layer "B.Cu") (hatch edge 0.5)
    (connect_pads (clearance 0.25))
    (min_thickness 0.25)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon (pts
      (xy 100 63.5) (xy 107.12 64.2) (xy 113.97 66.28) (xy 120.21 69.72)
      (xy 125.81 74.19) (xy 130.28 79.79) (xy 133.72 86.03) (xy 135.8 92.88)
      (xy 136.5 100) (xy 135.8 107.12) (xy 133.72 113.97) (xy 130.28 120.21)
      (xy 125.81 125.81) (xy 120.21 130.28) (xy 113.97 133.72) (xy 107.12 135.8)
      (xy 100 136.5) (xy 92.88 135.8) (xy 86.03 133.72) (xy 79.79 130.28)
      (xy 74.19 125.81) (xy 69.72 120.21) (xy 66.28 113.97) (xy 64.2 107.12)
      (xy 63.5 100) (xy 64.2 92.88) (xy 66.28 86.03) (xy 69.72 79.79)
      (xy 74.19 74.19) (xy 79.79 69.72) (xy 86.03 66.28) (xy 92.88 64.2)
    ))
  )
)
'''
    BOARD.write_text(pcb)


def generate_schematic() -> None:
    def txt(t: str, x: float, y: float, size: float = 1.0) -> str:
        return f'  (text "{t}" (exclude_from_sim no) (at {x} {y} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{uid()}"))'
    rows = [
        "IR BLASTER V3 — WROOM FACTORY PROGRAMMING INTERFACE",
        "U1 ESP32-WROOM-32E-N16: pin2=3V3, pin1/38/39=GND, pin35=U0TXD, pin34=U0RXD, pin3=EN, pin25=IO0",
        "J_PROG pinout: 1=3V3, 2=GND, 3=TX, 4=RX, 5=EN, 6=IO0 (DNP)",
        "Bottom pogo: TP_PROG_3V3/GND/TX/RX/EN/IO0; straight 1x6 at 3.81mm pitch",
        "Programmer TX connects board RX; programmer RX connects board TX.",
        "Do not connect programmer 3V3 while another board supply is active.",
    ]
    items = [txt(t, 20, 25 + i * 12, 1.1 if i == 0 else 0.9) for i, t in enumerate(rows)]
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
)
'''
    (OUT / f"{PROJECT}.kicad_sch").write_text(sch)


def generate_project() -> None:
    pro = {
        "boards": [], "cvpcb": {}, "erc": {}, "libraries": {},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
        "net_settings": {"classes": [{"name": "Default", "clearance": 0.25, "track_width": 0.3,
                                           "via_diameter": 0.8, "via_drill": 0.4}],
                         "meta": {"version": 3}, "net_colors": None,
                         "netclass_assignments": {}, "netclass_patterns": []},
        "pcbnew": {}, "schematic": {}, "sheets": [],
        "text_variables": {"BOARD_DIAMETER_MM": "74.0", "PROGRAM_POGO_PITCH_MM": "3.81"},
    }
    (OUT / f"{PROJECT}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")


def generate_bom() -> None:
    with (OUT / "BOM.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Reference", "Qty", "Value", "Manufacturer", "MPN", "JLC/LCSC", "Assembly", "Notes"])
        w.writerow(["U1", 1, "ESP32-WROOM-32E-N16", "Espressif Systems", "ESP32-WROOM-32E-N16", "C701343", "SMT / Standard PCBA", "16MB flash; X-ray required by JLCPCB"])
        w.writerow(["J_PROG", 1, "1x6 2.54mm male header", "Samtec-compatible", "TSW-106-07-G-S compatible", "DNP", "DNP", "1.0mm drill, 1.7mm pad"])
        w.writerow(["TP_PROG_*", 6, "2.4mm bottom pogo pads", "PCB feature", "N/A", "N/A", "PCB only", "1x6 straight, 3.81mm pitch"])
    with (OUT / "assembly" / "BOM_JLCPCB.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        w.writerow(["ESP32-WROOM-32E-N16", "U1", "ESP32-WROOM-32E", "C701343"])
    with (OUT / "assembly" / "CPL_JLCPCB.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerow(["U1", "100.000mm", "80.000mm", "Top", 0])


def main() -> None:
    for d in [OUT, OUT / "assembly", OUT / "manufacturing", OUT / "docs", OUT / "preview"]:
        d.mkdir(parents=True, exist_ok=True)
    generate_project()
    generate_schematic()
    generate_board()
    generate_bom()
    print(f"Generated {OUT}")


if __name__ == "__main__":
    main()
