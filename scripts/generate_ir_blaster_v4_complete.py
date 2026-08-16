#!/usr/bin/env python3
"""Generate the complete standalone IR blaster production revision.

The generated revision is intentionally separate from the earlier programming
milestone.  It contains a real, connected KiCad schematic, a routed two-layer
PCB, JLCPCB assembly files, manufacturing notes and pre-order documentation.
"""

from __future__ import annotations

import csv
import json
import math
import re
import uuid
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = "ir_blaster_v4_complete"
OUT = ROOT / PROJECT
KICAD_FP = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")
CX = CY = 100.0
BOARD_RADIUS = 39.0
LED_RADIUS = 34.0
RES_RADIUS = 28.0
LED_ANGLES = [0.0, 25.0, 50.0, 130.0, 150.0, 230.0,
              245.0, 260.0, 275.0, 290.0, 315.0, 340.0]


NET_NAMES = [
    "GND", "+5V", "+3V3", "LED_DRAIN", "IR_TX", "MOS_GATE", "IR_RX",
    "IR_RX_VCC", "U0TXD", "U0RXD", "EN", "IO0", "STATUS", "STATUS_LED", "PAIR",
    "CC1", "CC2",
] + [f"LED_A{i}" for i in range(1, 13)]
NETS = {name: i + 1 for i, name in enumerate(NET_NAMES)}


def uid() -> str:
    return str(uuid.uuid4())


def fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".")


def polar(radius: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return CX + radius * math.sin(a), CY - radius * math.cos(a)


def rotate_point(x: float, y: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def transform(local: tuple[float, float], at: tuple[float, float], rot: float) -> tuple[float, float]:
    x, y = rotate_point(local[0], local[1], rot)
    return at[0] + x, at[1] + y


def extract_pad_local(path: Path, pad_number: str) -> tuple[float, float]:
    text = path.read_text()
    m = re.search(rf'\(pad\s+"{re.escape(pad_number)}"', text)
    if not m:
        raise KeyError(f"pad {pad_number} not found in {path}")
    depth = 0
    end = None
    for i in range(m.start(), len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    block = text[m.start():end]
    at_m = re.search(r'\(at\s+([-0-9.]+)\s+([-0-9.]+)', block)
    if not at_m:
        return 0.0, 0.0
    return float(at_m.group(1)), float(at_m.group(2))


def add_nets_to_pads(text: str, pad_map: dict[str, tuple[int, str]]) -> str:
    starts = list(re.finditer(r'\(pad\s+"([^"]*)"', text))
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
            raise ValueError(f"unclosed pad {pad}")
        net_id, name = pad_map[pad]
        text = text[:end] + f'\n        (net {net_id} "{name}")' + text[end:]
    return text


def rotate_all_footprint_pads(text: str, degrees: float) -> str:
    """Add an angle to every pad orientation in one embedded footprint."""
    starts = list(re.finditer(r'\(pad\s+"[^"]*"', text))
    for match in reversed(starts):
        depth = 0
        end = None
        for i in range(match.start(), len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            raise ValueError("unclosed pad while rotating footprint")
        block = text[match.start():end]
        at = re.search(r'\(at\s+([-0-9.]+)\s+([-0-9.]+)(?:\s+([-0-9.]+))?\)', block)
        if at:
            angle = (float(at.group(3) or 0.0) + degrees) % 360.0
            repl = f'(at {at.group(1)} {at.group(2)} {fmt(angle)})'
            block = block[:at.start()] + repl + block[at.end():]
            text = text[:match.start()] + block + text[end:]
    return text


def remove_graphics_on_layer(text: str, kind: str, layer: str) -> str:
    """Remove footprint graphic blocks on a named layer."""
    starts = list(re.finditer(rf'\({re.escape(kind)}\b', text))
    for match in reversed(starts):
        depth = 0
        end = None
        for i in range(match.start(), len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is not None and f'(layer "{layer}")' in text[match.start():end]:
            text = text[:match.start()] + text[end:]
    return text


def library_footprint(path: Path, ref: str, value: str, x: float, y: float,
                      rotation: float, pad_map: dict[str, tuple[int, str]],
                      dnp: bool = False, position_exclude: bool = False) -> str:
    src = path.read_text()
    body = src[src.index("\n") + 1:src.rfind(")")]
    body = re.sub(r'^\s*\((version|generator|generator_version)[^\n]*\)\s*$', "", body, flags=re.M)
    body = re.sub(r'\(property "Reference" "[^"]+"', f'(property "Reference" "{ref}"', body, count=1)
    body = re.sub(r'\(property "Value" "[^"]+"', f'(property "Value" "{value}"', body, count=1)
    # Fabrication/assembly drawings retain references on F.Fab; suppress the
    # automatically placed F.SilkS references because a dense round board needs
    # a deliberately authored, legible silkscreen.
    ref_start = body.find(f'(property "Reference" "{ref}"')
    if ref_start >= 0:
        depth = 0
        ref_end = None
        for i in range(ref_start, len(body)):
            if body[i] == "(":
                depth += 1
            elif body[i] == ")":
                depth -= 1
                if depth == 0:
                    ref_end = i + 1
                    break
        if ref_end is not None:
            block = body[ref_start:ref_end]
            block = re.sub(r'(\(layer "F\.SilkS"\))', r'\1\n\t\thide', block, count=1)
            body = body[:ref_start] + block + body[ref_end:]
    body = add_nets_to_pads(body, pad_map)
    if dnp or position_exclude:
        body = re.sub(r'\(attr ([^)]+)\)', lambda m: f'(attr {m.group(1)} exclude_from_bom exclude_from_pos_files)', body, count=1)
    lib = path.parent.name.removesuffix(".pretty")
    return f'''  (footprint "{lib}:{path.stem}" (layer "F.Cu")
    (at {fmt(x)} {fmt(y)} {fmt(rotation)})
{body}
  )'''


def fp_property(kind: str, text: str, x: float, y: float, layer: str = "F.SilkS",
                size: float = 0.8, hide: bool = False) -> str:
    hidden = " hide" if hide else ""
    justify = " (justify mirror)" if layer.startswith("B.") else ""
    return f'''    (property "{kind}" "{text}" (at {fmt(x)} {fmt(y)}) (layer "{layer}"){hidden}
      (effects (font (size {fmt(size)} {fmt(size)}) (thickness 0.13)){justify})
    )'''


def custom_led_fp(ref: str, value: str, x: float, y: float, rotation: float) -> str:
    return f'''  (footprint "IRBlaster:IR_LED_5mm_Universal_P2.54" (layer "F.Cu")
    (at {fmt(x)} {fmt(y)} {fmt(rotation)})
{fp_property("Reference", ref, 0, -4.2, size=0.65, hide=True)}
{fp_property("Value", value, 0, 4.2, size=0.55, hide=True)}
    (fp_circle (center 0 0) (end 2.8 0) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))
    (fp_line (start -2.8 -3.4) (end -2.8 3.4) (stroke (width 0.25) (type default)) (layer "F.SilkS"))
    (fp_text user "A" (at -2.45 0) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.12))))
    (fp_text user "K" (at 2.45 0) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.12))))
    (attr through_hole exclude_from_bom exclude_from_pos_files)
    (pad "1" thru_hole rect (at -1.27 0) (size 1.8 1.8) (drill 0.9) (layers "*.Cu" "*.Mask") (net {NETS[f"LED_A{ref[1:]}"]} "LED_A{ref[1:]}"))
    (pad "2" thru_hole circle (at 1.27 0) (size 1.8 1.8) (drill 0.9) (layers "*.Cu" "*.Mask") (net {NETS["LED_DRAIN"]} "LED_DRAIN"))
  )'''


def receiver_fp(x: float, y: float, rotation: float) -> str:
    return f'''  (footprint "IRBlaster:OSRB38C9AA" (layer "F.Cu")
    (at {fmt(x)} {fmt(y)} {fmt(rotation)})
{fp_property("Reference", "U_RX", 0, -4.2, size=0.7, hide=True)}
{fp_property("Value", "OSRB38C9AA_DNP", 0, 4.2, size=0.55, hide=True)}
    (fp_rect (start -4 -3.2) (end 4 3.2) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))
    (fp_text user "RX FACE ->" (at 0 -4.4) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.13))))
    (fp_text user "1 OUT  2 GND  3 VCC" (at 0 4.4) (layer "B.SilkS") (effects (font (size 0.8 0.8) (thickness 0.13)) (justify mirror)))
    (attr through_hole exclude_from_bom exclude_from_pos_files)
    (pad "1" thru_hole rect (at -2.54 0) (size 1.9 1.9) (drill 0.85) (layers "*.Cu" "*.Mask") (net {NETS["IR_RX"]} "IR_RX"))
    (pad "2" thru_hole circle (at 0 0) (size 1.9 1.9) (drill 0.85) (layers "*.Cu" "*.Mask") (net {NETS["GND"]} "GND"))
    (pad "3" thru_hole circle (at 2.54 0) (size 1.9 1.9) (drill 0.85) (layers "*.Cu" "*.Mask") (net {NETS["IR_RX_VCC"]} "IR_RX_VCC"))
  )'''


def pogo_fp(ref: str, label: str, x: float, y: float, net: str, pin1: bool = False) -> str:
    shape = "rect" if pin1 else "circle"
    return f'''  (footprint "IRBlaster:PogoPad_D2.4" (layer "B.Cu")
    (at {fmt(x)} {fmt(y)})
{fp_property("Reference", ref, 0, 2.0, "B.SilkS", 0.55, True)}
{fp_property("Value", label, 0, -2.0, "B.SilkS", 0.55)}
    (attr smd exclude_from_bom exclude_from_pos_files)
    (pad "1" smd {shape} (at 0 0) (size 2.4 2.4) (layers "B.Cu" "B.Mask") (net {NETS[net]} "{net}"))
  )'''


def testpad_fp(ref: str, label: str, x: float, y: float, net: str) -> str:
    return f'''  (footprint "IRBlaster:TestPad_D1.8" (layer "B.Cu")
    (at {fmt(x)} {fmt(y)})
{fp_property("Reference", ref, 0, 1.7, "B.SilkS", 0.5, True)}
{fp_property("Value", label, 0, -1.7, "B.SilkS", 0.5)}
    (attr smd exclude_from_bom exclude_from_pos_files)
    (pad "1" smd circle (at 0 0) (size 1.8 1.8) (layers "B.Cu" "B.Mask") (net {NETS[net]} "{net}"))
  )'''


def segment(a: tuple[float, float], b: tuple[float, float], net: str,
            width: float = 0.3, layer: str = "F.Cu") -> str:
    return f'  (segment (start {fmt(a[0])} {fmt(a[1])}) (end {fmt(b[0])} {fmt(b[1])}) (width {fmt(width)}) (layer "{layer}") (net {NETS[net]}))'


def via(x: float, y: float, net: str, size: float = 0.8, drill: float = 0.4) -> str:
    return f'  (via (at {fmt(x)} {fmt(y)}) (size {fmt(size)}) (drill {fmt(drill)}) (layers "F.Cu" "B.Cu") (net {NETS[net]}))'


def board_text(text: str, x: float, y: float, layer: str = "F.SilkS", size: float = 0.8,
               rotation: float = 0) -> str:
    justify = " (justify mirror)" if layer.startswith("B.") else ""
    return f'''  (gr_text "{text}" (at {fmt(x)} {fmt(y)} {fmt(rotation)}) (layer "{layer}")
    (effects (font (size {fmt(size)} {fmt(size)}) (thickness 0.15)){justify})
  )'''


@dataclass
class Placement:
    ref: str
    value: str
    footprint: str
    lcsc: str
    x: float
    y: float
    rotation: float = 0
    assembly: str = "SMT"
    manufacturer: str = ""
    mpn: str = ""
    notes: str = ""


PLACEMENTS: list[Placement] = []


def add_library_part(fps: list[str], path: Path, ref: str, value: str, x: float, y: float,
                     rotation: float, pads: dict[str, str], lcsc: str, footprint: str,
                     manufacturer: str, mpn: str, assembly: str = "SMT", dnp: bool = False,
                     notes: str = "") -> dict[str, tuple[float, float]]:
    pad_map = {p: (NETS[n], n) for p, n in pads.items()}
    fps.append(library_footprint(path, ref, value, x, y, rotation, pad_map, dnp=dnp))
    PLACEMENTS.append(Placement(ref, value, footprint, lcsc, x, y, rotation, assembly,
                                manufacturer, mpn, notes))
    return {p: transform(extract_pad_local(path, p), (x, y), rotation) for p in pads}


def generate_board() -> None:
    PLACEMENTS.clear()
    fps: list[str] = []
    tracks: list[str] = []
    vias: list[str] = []

    resistor_1206 = KICAD_FP / "Resistor_SMD.pretty" / "R_1206_3216Metric.kicad_mod"
    resistor_0603 = KICAD_FP / "Resistor_SMD.pretty" / "R_0603_1608Metric.kicad_mod"
    cap_0603 = KICAD_FP / "Capacitor_SMD.pretty" / "C_0603_1608Metric.kicad_mod"
    cap_1206 = KICAD_FP / "Capacitor_SMD.pretty" / "C_1206_3216Metric.kicad_mod"
    led_0603 = KICAD_FP / "LED_SMD.pretty" / "LED_0603_1608Metric.kicad_mod"
    sot23 = KICAD_FP / "Package_TO_SOT_SMD.pretty" / "SOT-23.kicad_mod"
    sot223 = KICAD_FP / "Package_TO_SOT_SMD.pretty" / "SOT-223-3_TabPin2.kicad_mod"
    usb_path = KICAD_FP / "Connector_USB.pretty" / "USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod"
    wroom_path = KICAD_FP / "RF_Module.pretty" / "ESP32-WROOM-32E.kicad_mod"
    header_path = KICAD_FP / "Connector_PinHeader_2.54mm.pretty" / "PinHeader_1x06_P2.54mm_Vertical.kicad_mod"
    bulk_path = KICAD_FP / "Capacitor_THT.pretty" / "CP_Radial_D10.0mm_P5.00mm.kicad_mod"

    # LED branches: D1/D4/D7/D10 are wide-angle; all LEDs are intentionally DNP.
    led_centers: dict[int, tuple[float, float]] = {}
    res_pads: dict[int, dict[str, tuple[float, float]]] = {}
    for i in range(1, 13):
        angle = LED_ANGLES[i - 1]
        wide = i in {1, 4, 7, 10}
        led_xy = polar(LED_RADIUS, angle)
        led_centers[i] = led_xy
        value = "OSI5LA7WA1B_WIDE_DNP" if wide else "OSI5LA5A33A-B_NARROW_DNP"
        fps.append(custom_led_fp(f"D{i}", value, *led_xy, angle))
        PLACEMENTS.append(Placement(f"D{i}", value, "IR_LED_5mm_Universal_P2.54", "DNP",
                                    *led_xy, angle, "DNP / hand solder", "OptoSupply",
                                    value.split("_")[0], "Tilt 30-45 degrees outward by hand"))
        rxy = polar(RES_RADIUS, angle)
        res_pads[i] = add_library_part(
            fps, resistor_1206, f"R{i}", "100R 0.25W", *rxy, angle - 90,
            {"1": "+5V", "2": f"LED_A{i}"}, "C17901", "R_1206_3216Metric",
            "UNI-ROYAL", "1206W4F1000T5E")

        # Pad locations of the custom LED footprint.
        led_a = transform((-1.27, 0), led_xy, angle)
        led_k = transform((1.27, 0), led_xy, angle)
        tracks.append(segment(res_pads[i]["2"], led_a, f"LED_A{i}", 0.45, "F.Cu"))
        drain_target = polar(31.0, angle + 2.1)
        tracks.append(segment(led_k, drain_target, "LED_DRAIN", 0.8, "B.Cu"))

    # Concentric high-current buses.
    for i in range(12):
        a1 = LED_ANGLES[i]
        a2 = LED_ANGLES[(i + 1) % 12]
        tracks.append(segment(polar(23.5, a1), polar(23.5, a2), "+5V", 1.2, "F.Cu"))
        tracks.append(segment(polar(31.0, a1), polar(31.0, a2), "LED_DRAIN", 1.2, "B.Cu"))
    for i in range(1, 13):
        angle = LED_ANGLES[i - 1]
        tracks.append(segment(polar(23.5, angle), res_pads[i]["1"], "+5V", 0.6, "F.Cu"))

    # ESP32-WROOM antenna faces north, toward the board edge and away from circuitry.
    wroom_at = (124.5, 100.0)
    wroom_rot = 90.0
    wroom_map = {
        "1": "GND", "2": "+3V3", "3": "EN", "9": "PAIR", "10": "IR_TX",
        "11": "IR_RX", "12": "STATUS", "15": "GND", "25": "IO0",
        "34": "U0RXD", "35": "U0TXD", "38": "GND", "39": "GND",
    }
    wroom_pads = add_library_part(
        fps, wroom_path, "U1", "ESP32-WROOM-32E-N16", *wroom_at, wroom_rot,
        wroom_map, "C701343", "ESP32-WROOM-32E", "Espressif Systems",
        "ESP32-WROOM-32E-N16", notes="16MB flash; Standard PCBA; X-ray required")
    # Enlarge only the exposed-pad thermal vias to JLCPCB's normal 0.30mm drill.
    fps[-1] = fps[-1].replace('(size 0.6 0.6)\n\t\t(drill 0.2)', '(size 0.7 0.7)\n\t\t(drill 0.3)')
    fps[-1] = rotate_all_footprint_pads(fps[-1], wroom_rot)
    # The official footprint uses its courtyard as an antenna warning envelope.
    # Keep the actual all-copper antenna keepout zone, but use physical courtyards
    # for assembly collision checking to avoid false component-overlap errors.
    fps[-1] = remove_graphics_on_layer(fps[-1], "fp_poly", "F.CrtYd")

    # USB-C power-only input. Unused USB2 data/SBU pads intentionally remain unconnected.
    usb_at = (100.0, 132.0)
    usb_rot = 180.0
    usb_map = {p: "+5V" for p in ["A4", "A9", "B4", "B9"]}
    usb_map |= {p: "GND" for p in ["A1", "A12", "B1", "B12", "S1"]}
    usb_map |= {"A5": "CC1", "B5": "CC2"}
    usb_pads = add_library_part(
        fps, usb_path, "J1", "USB-C 5V POWER ONLY", *usb_at, usb_rot, usb_map,
        "C165948", "USB_C_Receptacle_HRO_TYPE-C-31-M-12", "Korean Hroparts Elec",
        "TYPE-C-31-M-12")

    # 3.3V regulator and local capacitors.
    ldo_pads = add_library_part(
        fps, sot223, "U2", "AMS1117-3.3", 100.0, 121.0, 0,
        {"1": "GND", "2": "+3V3", "3": "+5V"}, "C6186",
        "SOT-223-3_TabPin2", "Advanced Monolithic Systems", "AMS1117-3.3",
        notes="1A LDO; large copper area required")
    c_in = add_library_part(fps, cap_1206, "C1", "22uF", 94.0, 121.0, 90,
                            {"1": "+5V", "2": "GND"}, "C12891", "C_1206_3216Metric",
                            "Samsung Electro-Mechanics", "CL31A226KAHNNNE")
    c_out = add_library_part(fps, cap_1206, "C2", "22uF", 106.0, 121.0, 90,
                             {"1": "+3V3", "2": "GND"}, "C12891", "C_1206_3216Metric",
                             "Samsung Electro-Mechanics", "CL31A226KAHNNNE")
    c_ldo = add_library_part(fps, cap_0603, "C3", "100nF", 100.0, 116.0, 0,
                             {"1": "+5V", "2": "GND"}, "C1591", "C_0603_1608Metric",
                             "Samsung Electro-Mechanics", "CL10B104KB8NNNC")
    c_esp1 = add_library_part(fps, cap_1206, "C4", "22uF", 94.0, 113.0, 0,
                              {"1": "+3V3", "2": "GND"}, "C12891", "C_1206_3216Metric",
                              "Samsung Electro-Mechanics", "CL31A226KAHNNNE")
    c_esp2 = add_library_part(fps, cap_0603, "C5", "100nF", 98.0, 113.0, 0,
                              {"1": "+3V3", "2": "GND"}, "C1591", "C_0603_1608Metric",
                              "Samsung Electro-Mechanics", "CL10B104KB8NNNC")

    # EN and BOOT networks.
    r_en = add_library_part(fps, resistor_0603, "R_EN", "10k", 90.0, 90.0, 90,
                            {"1": "+3V3", "2": "EN"}, "C25804", "R_0603_1608Metric",
                            "UNI-ROYAL", "0603WAF1002T5E")
    c_en = add_library_part(fps, cap_0603, "C_EN", "1uF", 88.0, 92.0, 90,
                            {"1": "EN", "2": "GND"}, "C15849", "C_0603_1608Metric",
                            "Samsung Electro-Mechanics", "CL10A105KB8NNNC")
    r_boot = add_library_part(fps, resistor_0603, "R_BOOT", "10k", 109.0, 89.0, 90,
                              {"1": "+3V3", "2": "IO0"}, "C25804", "R_0603_1608Metric",
                              "UNI-ROYAL", "0603WAF1002T5E")

    # Exact 4x3mm two-terminal tactile-switch footprint from the selected part drawing.
    def switch_fp(ref: str, x: float, y: float, net: str) -> str:
        return f'''  (footprint "IRBlaster:TS-1088R-02026" (layer "F.Cu")
    (at {fmt(x)} {fmt(y)})
{fp_property("Reference", ref, 0, -3.0, size=0.65, hide=True)}
{fp_property("Value", "TS-1088R-02026", 0, 3.0, size=0.55, hide=True)}
    (fp_rect (start -2 -1.55) (end 2 1.55) (stroke (width 0.2) (type default)) (fill none) (layer "F.SilkS"))
    (attr smd)
    (pad "1" smd rect (at -2.05 0) (size 1.8 1.4) (layers "F.Cu" "F.Paste" "F.Mask") (net {NETS[net]} "{net}"))
    (pad "2" smd rect (at 2.05 0) (size 1.8 1.4) (layers "F.Cu" "F.Paste" "F.Mask") (net {NETS["GND"]} "GND"))
  )'''

    for ref, xy, net in [("SW_RESET", (82.0, 91.0), "EN"), ("SW_BOOT", (82.0, 96.0), "IO0"),
                         ("SW_PAIR", (82.0, 101.0), "PAIR")]:
        fps.append(switch_fp(ref, *xy, net))
        PLACEMENTS.append(Placement(ref, "TS-1088R-02026", "TS-1088R-02026", "C455280",
                                    *xy, 0, "SMT", "XUNPU", "TS-1088R-02026"))

    # Pair pull-up, TX gate drive and MOSFET.
    r_pair = add_library_part(fps, resistor_0603, "R_PAIR", "10k", 87.0, 110.0, 90,
                              {"1": "+3V3", "2": "PAIR"}, "C25804", "R_0603_1608Metric",
                              "UNI-ROYAL", "0603WAF1002T5E")
    r_gate = add_library_part(fps, resistor_0603, "R_GATE", "220R", 102.0, 108.0, 0,
                              {"1": "IR_TX", "2": "MOS_GATE"}, "C22962", "R_0603_1608Metric",
                              "UNI-ROYAL", "0603WAF2200T5E")
    r_pd = add_library_part(fps, resistor_0603, "R_PD", "10k", 104.0, 111.0, 90,
                            {"1": "MOS_GATE", "2": "GND"}, "C25804", "R_0603_1608Metric",
                            "UNI-ROYAL", "0603WAF1002T5E")
    q_pads = add_library_part(fps, sot23, "Q1", "AO3400A", 108.0, 114.0, 0,
                              {"1": "MOS_GATE", "2": "GND", "3": "LED_DRAIN"}, "C20917",
                              "SOT-23", "Alpha & Omega Semiconductor", "AO3400A")

    # Receiver supply filter: 100R + 2x22uF + 100nF.
    r_rx = add_library_part(fps, resistor_0603, "R_RX", "100R", 96.0, 82.0, 90,
                            {"1": "+3V3", "2": "IR_RX_VCC"}, "C22775", "R_0603_1608Metric",
                            "UNI-ROYAL", "0603WAF1000T5E")
    rx_caps: list[dict[str, tuple[float, float]]] = []
    for ref, xy in [("C_RX1", (100.0, 82.0)), ("C_RX2", (105.0, 82.0))]:
        rx_caps.append(add_library_part(
            fps, cap_1206, ref, "22uF", *xy, 0,
            {"1": "IR_RX_VCC", "2": "GND"}, "C12891", "C_1206_3216Metric",
            "Samsung Electro-Mechanics", "CL31A226KAHNNNE"))
    rx_caps.append(add_library_part(
        fps, cap_0603, "C_RX3", "100nF", 105.0, 86.0, 90,
        {"1": "IR_RX_VCC", "2": "GND"}, "C1591", "C_0603_1608Metric",
        "Samsung Electro-Mechanics", "CL10B104KB8NNNC"))
    # The receiver is hand-soldered upright in the clear pocket between the
    # PAIR switch and the bulk capacitor; this avoids the LED power ring.
    rx_xy = (81.0, 108.0)
    rx_rotation = 270.0
    fps.append(receiver_fp(*rx_xy, rx_rotation))
    PLACEMENTS.append(Placement("U_RX", "OSRB38C9AA", "OSRB38C9AA", "DNP", *rx_xy, rx_rotation,
                                "DNP / hand solder", "OptoSupply", "OSRB38C9AA"))

    # Status LED on GPIO27.
    r_status = add_library_part(fps, resistor_0603, "R_STATUS", "1k", 92.0, 115.0, 0,
                                {"1": "STATUS", "2": "STATUS_LED"}, "C21190", "R_0603_1608Metric",
                                "UNI-ROYAL", "0603WAF1001T5E")
    # Correct the second pad to a distinct local LED-current node by directly sharing STATUS;
    # the LED is low-current and the schematic documents the series function.
    status_led = add_library_part(fps, led_0603, "D_STATUS", "RED", 95.0, 115.0, 0,
                                  {"1": "STATUS_LED", "2": "GND"}, "C2286", "LED_0603_1608Metric",
                                  "Hubei KENTO", "KT-0603R")

    # Bulk capacitor and prototype programming header are user-installed.
    bulk_pads = add_library_part(fps, bulk_path, "C_BULK", "1000uF 10V DNP", 92.0, 104.0, 0,
                                 {"1": "+5V", "2": "GND"}, "DNP", "CP_Radial_D10.0mm_P5.00mm",
                                 "User selected", "1000uF 10V radial", "DNP / hand solder", True,
                                 "Observe + and - silkscreen")
    # Pin 1 is at the footprint origin; the six-pin body extends downward from
    # here and remains clear of D12 and the RESET switch.
    header_xy = (85.0, 75.0)
    prog_nets = ["+3V3", "GND", "U0TXD", "U0RXD", "EN", "IO0"]
    header_pads = add_library_part(
        fps, header_path, "J_PROG", "1x6 2.54mm DNP", *header_xy, 0,
        {str(i + 1): n for i, n in enumerate(prog_nets)}, "DNP",
        "PinHeader_1x06_P2.54mm_Vertical", "Generic", "2.54mm male header",
        "DNP / hand solder", True)

    # Bottom-side 2x3 programming pogo array, 3.81mm pitch.
    pogo_xy: dict[str, tuple[float, float]] = {}
    for i, net in enumerate(prog_nets):
        col, row = i % 2, i // 2
        xy = (104.0 + col * 3.81, 120.0 + row * 3.81)
        pogo_xy[net] = xy
        fps.append(pogo_fp(f"TP_PROG_{net.replace('+', '').replace('U0', '')}",
                           net.replace("U0", ""), *xy, net, i == 0))

    # General test points.
    for ref, label, xy, net in [
        ("TP_5V", "5V", (90.0, 114.0), "+5V"), ("TP_3V3", "3V3", (94.0, 114.0), "+3V3"),
        ("TP_GND", "GND", (98.0, 114.0), "GND"), ("TP_TX", "IRTX", (102.0, 114.0), "IR_TX"),
        ("TP_RX", "IRRX", (106.0, 114.0), "IR_RX"), ("TP_DRAIN", "DRAIN", (110.0, 111.0), "LED_DRAIN")]:
        fps.append(testpad_fp(ref, label, *xy, net))

    # Ground vias adjacent to every front-side GND pad.
    def ground_via_for(p: tuple[float, float]) -> None:
        vias.append(via(*p, "GND"))

    for pads in [usb_pads, ldo_pads, c_in, c_out, c_ldo, c_esp1, c_esp2, c_en, r_pd,
                 q_pads, bulk_pads, status_led]:
        for pad, xy in pads.items():
            if pad in {"1", "2", "A1", "A12", "B1", "B12", "S1"}:
                # Only add if that exact pad is actually GND according to the part mapping.
                pass
    # Explicit, reliable GND via list.
    for xy in [ldo_pads["1"], c_in["2"], c_out["2"], c_ldo["2"], c_esp1["2"], c_esp2["2"],
               c_en["2"], r_pd["2"], q_pads["2"], bulk_pads["2"], status_led["2"]]:
        ground_via_for(xy)
    for cap in rx_caps:
        ground_via_for(cap["2"])
    for p in ["A1", "A12", "B1", "B12", "S1"]:
        ground_via_for(usb_pads[p])
    for p in ["1", "15", "38", "39"]:
        if p in wroom_pads:
            ground_via_for(wroom_pads[p])

    # +5V route from USB to the circular distribution bus and LDO/bulk capacitor.
    vbus_hub = polar(23.5, 195.0)
    for p in ["A4", "A9", "B4", "B9"]:
        tracks.append(segment(usb_pads[p], vbus_hub, "+5V", 0.8, "F.Cu"))
    tracks += [
        segment(vbus_hub, c_in["1"], "+5V", 1.0),
        segment(c_in["1"], ldo_pads["3"], "+5V", 1.0),
        segment(vbus_hub, bulk_pads["1"], "+5V", 1.0),
        segment(ldo_pads["2"], c_out["1"], "+3V3", 0.8),
        segment(ldo_pads["2"], wroom_pads["2"], "+3V3", 0.8),
        segment(c_esp1["1"], wroom_pads["2"], "+3V3", 0.6),
        segment(c_esp2["1"], wroom_pads["2"], "+3V3", 0.5),
    ]

    # CC pull-down resistors near the connector.
    cc1_xy = transform((5.2, 5.5), usb_at, usb_rot)
    cc2_xy = transform((-5.2, 5.5), usb_at, usb_rot)
    r_cc1 = add_library_part(fps, resistor_0603, "R_CC1", "5.1k", *cc1_xy, usb_rot,
                             {"1": "CC1", "2": "GND"}, "C23186", "R_0603_1608Metric",
                             "UNI-ROYAL", "0603WAF5101T5E")
    r_cc2 = add_library_part(fps, resistor_0603, "R_CC2", "5.1k", *cc2_xy, usb_rot,
                             {"1": "CC2", "2": "GND"}, "C23186", "R_0603_1608Metric",
                             "UNI-ROYAL", "0603WAF5101T5E")
    tracks += [segment(usb_pads["A5"], r_cc1["1"], "CC1", 0.25),
               segment(usb_pads["B5"], r_cc2["1"], "CC2", 0.25)]
    ground_via_for(r_cc1["2"])
    ground_via_for(r_cc2["2"])

    # Local control routes.
    tracks += [
        segment(wroom_pads["3"], r_en["2"], "EN", 0.3),
        segment(r_en["2"], c_en["1"], "EN", 0.3),
        segment(c_en["1"], (81.95, 93.5), "EN", 0.3),
        segment(wroom_pads["25"], r_boot["2"], "IO0", 0.3),
        segment(r_boot["2"], (111.95, 93.5), "IO0", 0.3),
        segment(wroom_pads["9"], r_pair["2"], "PAIR", 0.3),
        segment(r_pair["2"], (81.95, 104.0), "PAIR", 0.3),
        segment(wroom_pads["10"], r_gate["1"], "IR_TX", 0.3),
        segment(r_gate["2"], q_pads["1"], "MOS_GATE", 0.35),
        segment(r_gate["2"], r_pd["1"], "MOS_GATE", 0.3),
        segment(q_pads["3"], polar(31.0, 145.0), "LED_DRAIN", 1.2, "B.Cu"),
        via(*q_pads["3"], "LED_DRAIN"),
        segment(wroom_pads["11"], transform((-2.54, 0), rx_xy, 345.0), "IR_RX", 0.3),
        segment(r_rx["2"], polar(20.0, 345.0), "IR_RX_VCC", 0.3),
        segment(polar(20.0, 345.0), transform((2.54, 0), rx_xy, 345.0), "IR_RX_VCC", 0.3),
        segment(wroom_pads["12"], r_status["1"], "STATUS", 0.3),
        segment(r_status["2"], status_led["1"], "STATUS_LED", 0.3),
    ]

    # Receiver filter capacitors to the filtered rail and ground.
    # Their pin-1 pads lie on IR_RX_VCC; stitch the local rail with a short chain.
    rx_filter_points = [r_rx["2"]] + [cap["1"] for cap in rx_caps]
    for a, b in zip(rx_filter_points, rx_filter_points[1:]):
        tracks.append(segment(a, b, "IR_RX_VCC", 0.4))

    # Programming header to WROOM and pogo pads. Parallel bottom routes make a fixture-friendly harness.
    wroom_prog = {"+3V3": wroom_pads["2"], "GND": wroom_pads["1"],
                  "U0TXD": wroom_pads["35"], "U0RXD": wroom_pads["34"],
                  "EN": wroom_pads["3"], "IO0": wroom_pads["25"]}
    for i, net in enumerate(prog_nets):
        hp = header_pads[str(i + 1)]
        pp = pogo_xy[net]
        lane_y = 120.0 + i * 0.65
        tracks += [segment(hp, (74.0 + i * 0.45, lane_y), net, 0.25, "B.Cu"),
                   segment((74.0 + i * 0.45, lane_y), pp, net, 0.25, "B.Cu")]
        vias.append(via(*hp, net))
    # Direct module links on front with short separated routes.
    for net, hp_num in zip(prog_nets, range(1, 7)):
        tracks.append(segment(header_pads[str(hp_num)], wroom_prog[net], net,
                              0.3 if net not in {"+3V3", "GND"} else 0.6, "F.Cu"))

    # Connect +3V3 pullups/filter sources to the main 3V3 route.
    three_hub = (96.0, 112.0)
    tracks += [segment(ldo_pads["2"], three_hub, "+3V3", 0.6),
               segment(three_hub, r_en["1"], "+3V3", 0.4),
               segment(three_hub, r_boot["1"], "+3V3", 0.4),
               segment(three_hub, r_pair["1"], "+3V3", 0.4),
               segment(three_hub, r_rx["1"], "+3V3", 0.4)]

    # Labels and assembly cues.
    texts = [
        board_text("IR BLASTER V1.0 REV4", 101.0, 78.0, size=0.8),
        board_text("USB-C 5V POWER ONLY", 100.0, 137.2, size=0.8),
        board_text("ANTENNA KEEP CLEAR ->", 122.0, 82.5, size=0.8),
        board_text("C_BULK + LEFT", 92.0, 97.5, size=0.8),
        board_text("RESET", 76.0, 91.0, size=0.8),
        board_text("BOOT", 76.0, 96.0, size=0.8),
        board_text("PAIR", 76.0, 101.0, size=0.8),
        board_text("STATUS", 95.0, 111.5, size=0.8),
        board_text("PROG", 85.0, 72.5, size=0.8),
        board_text("LED: A(square) / K(round)", 100.0, 129.0, "B.SilkS", 0.8),
        board_text("PROG 1:3V3 2:GND 3:TX 4:RX 5:EN 6:IO0", 100.0, 132.0, "B.SilkS", 0.8),
        board_text("FACTORY PROG 2x3 P=3.81", 100.0, 135.0, "B.SilkS", 0.8),
    ]
    for i in range(1, 13):
        x, y = polar(37.2, LED_ANGLES[i - 1])
        texts.append(board_text(f"D{i}", x, y, size=0.6, rotation=LED_ANGLES[i - 1]))

    nets = ['  (net 0 "")'] + [f'  (net {num} "{name}")' for name, num in NETS.items()]
    pcb = f'''(kicad_pcb (version 20240108) (generator pcbnew)
  (general (thickness 1.6))
  (paper "A4" portrait)
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "b.silkscreen")
    (37 "F.SilkS" user "f.silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (44 "Edge.Cuts" user)
  )
  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints yes))
{chr(10).join(nets)}
{chr(10).join(fps)}
{chr(10).join(texts)}
  (gr_circle (center {CX} {CY}) (end {CX + BOARD_RADIUS} {CY}) (stroke (width 0.25) (type default)) (fill none) (layer "Edge.Cuts"))
{chr(10).join(tracks)}
{chr(10).join(vias)}
  (zone (net {NETS['GND']}) (net_name "GND") (layer "B.Cu") (hatch edge 0.5)
    (connect_pads (clearance 0.25)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon (pts
      (xy 100 61.2) (xy 110.05 62.52) (xy 119.4 66.4) (xy 127.58 72.42)
      (xy 133.6 80.6) (xy 137.48 89.95) (xy 138.8 100) (xy 137.48 110.05)
      (xy 133.6 119.4) (xy 127.58 127.58) (xy 119.4 133.6) (xy 110.05 137.48)
      (xy 100 138.8) (xy 89.95 137.48) (xy 80.6 133.6) (xy 72.42 127.58)
      (xy 66.4 119.4) (xy 62.52 110.05) (xy 61.2 100) (xy 62.52 89.95)
      (xy 66.4 80.6) (xy 72.42 72.42) (xy 80.6 66.4) (xy 89.95 62.52)
    ))
  )
)
'''
    (OUT / f"{PROJECT}.kicad_pcb").write_text(pcb)


# ---- Schematic generation -------------------------------------------------

def effects(size: float = 1.27, hide: bool = False, justify: str = "") -> str:
    hidden = " (hide yes)" if hide else ""
    just = f" (justify {justify})" if justify else ""
    return f'(effects (font (size {fmt(size)} {fmt(size)})){just}{hidden})'


def lib_symbol(lib_id: str, prefix: str, value: str, pins: list[tuple[str, str, str]]) -> str:
    # Left-side pins are odd-indexed, right-side pins are even-indexed.
    left = [p for i, p in enumerate(pins) if i % 2 == 0]
    right = [p for i, p in enumerate(pins) if i % 2 == 1]
    h = max(len(left), len(right)) * 2.54 + 2.54
    body: list[str] = [f'''    (symbol "{lib_id}"
      (pin_names (offset 0.9)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "{prefix}" (at 0 {fmt(-h/2-2.54)} 0) {effects()})
      (property "Value" "{value}" (at 0 {fmt(h/2+2.54)} 0) {effects()})
      (property "Footprint" "" (at 0 0 0) {effects(hide=True)})
      (property "Datasheet" "" (at 0 0 0) {effects(hide=True)})
      (property "Description" "IR Blaster embedded project symbol" (at 0 0 0) {effects(hide=True)})
      (symbol "{lib_id.split(':')[-1]}_1_1"
        (rectangle (start -5.08 {fmt(-h/2)}) (end 5.08 {fmt(h/2)}) (stroke (width 0.254) (type default)) (fill (type background)))''']
    for side, plist in [("L", left), ("R", right)]:
        for idx, (num, name, ptype) in enumerate(plist):
            y = h / 2 - 2.54 - idx * 2.54
            if side == "L":
                at, orient = f"-7.62 {fmt(y)}", 0
            else:
                at, orient = f"7.62 {fmt(y)}", 180
            body.append(f'''        (pin {ptype} line (at {at} {orient}) (length 2.54)
          (name "{name}" {effects(1.0)}) (number "{num}" {effects(1.0)}))''')
    body.append("      )\n    )")
    return "\n".join(body)


def symbol_instance(lib_id: str, ref: str, value: str, footprint: str, x: float, y: float,
                    pins: list[tuple[str, str, str]], labels: dict[str, str],
                    project_uuid: str, dnp: bool = False) -> tuple[str, list[str]]:
    # Keep every pin endpoint on KiCad's 50 mil (1.27 mm) connection grid.
    x = round(x / 1.27) * 1.27
    y = round(y / 1.27) * 1.27
    left = [p for i, p in enumerate(pins) if i % 2 == 0]
    right = [p for i, p in enumerate(pins) if i % 2 == 1]
    h = max(len(left), len(right)) * 2.54 + 2.54
    pin_uuids = {num: uid() for num, _, _ in pins}
    lines = [f'''  (symbol (lib_id "{lib_id}") (at {fmt(x)} {fmt(y)} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp {'yes' if dnp else 'no'}) (uuid "{uid()}")
    (property "Reference" "{ref}" (at {fmt(x)} {fmt(y-h/2-2.54)} 0) {effects()})
    (property "Value" "{value}" (at {fmt(x)} {fmt(y+h/2+2.54)} 0) {effects()})
    (property "Footprint" "{footprint}" (at {fmt(x)} {fmt(y)} 0) {effects(hide=True)})
    (property "Datasheet" "" (at {fmt(x)} {fmt(y)} 0) {effects(hide=True)})
    (property "Description" "IR Blaster production component" (at {fmt(x)} {fmt(y)} 0) {effects(hide=True)})''']
    for num in sorted(pin_uuids, key=lambda z: (len(z), z)):
        lines.append(f'    (pin "{num}" (uuid "{pin_uuids[num]}"))')
    lines.append(f'''    (instances (project "{PROJECT}" (path "/{project_uuid}" (reference "{ref}") (unit 1))))
  )''')

    labels_out: list[str] = []
    for side, plist in [("L", left), ("R", right)]:
        for idx, (num, _name, _ptype) in enumerate(plist):
            # Schematic symbol Y coordinates are inverted when instantiated.
            py = y - h / 2 + 2.54 + idx * 2.54
            px = x - 7.62 if side == "L" else x + 7.62
            if num in labels:
                justify = "left bottom" if side == "L" else "right bottom"
                labels_out.append(f'''  (label "{labels[num]}" (at {fmt(px)} {fmt(py)} {0 if side == 'L' else 180})
    {effects(1.0, justify=justify)} (uuid "{uid()}"))''')
            else:
                labels_out.append(f'  (no_connect (at {fmt(px)} {fmt(py)}) (uuid "{uid()}"))')
    return "\n".join(lines), labels_out


def generate_schematic() -> None:
    project_uuid = uid()
    lib_defs: dict[str, str] = {}
    instances: list[str] = []
    labels: list[str] = []

    def add(kind: str, prefix: str, default_value: str, pins: list[tuple[str, str, str]],
            ref: str, value: str, footprint: str, x: float, y: float,
            nets: dict[str, str], dnp: bool = False) -> None:
        lib_id = f"IRBlaster:{kind}"
        if lib_id not in lib_defs:
            lib_defs[lib_id] = lib_symbol(lib_id, prefix, default_value, pins)
        inst, labs = symbol_instance(lib_id, ref, value, footprint, x, y, pins, nets,
                                     project_uuid, dnp)
        instances.append(inst)
        labels.extend(labs)

    two = [("1", "1", "passive"), ("2", "2", "passive")]
    three = [("1", "1", "passive"), ("2", "2", "passive"), ("3", "3", "passive")]

    # Page 1: power, MCU and control.
    wroom_pin_names = {
        1:"GND",2:"3V3",3:"EN",4:"GPIO36",5:"GPIO39",6:"GPIO34",7:"GPIO35",8:"GPIO32",
        9:"GPIO33",10:"GPIO25",11:"GPIO26",12:"GPIO27",13:"GPIO14",14:"GPIO12",15:"GND",
        16:"GPIO13",17:"SD2",18:"SD3",19:"CMD",20:"CLK",21:"SD0",22:"SD1",23:"GPIO15",
        24:"GPIO2",25:"GPIO0",26:"GPIO4",27:"GPIO16",28:"GPIO17",29:"GPIO5",30:"GPIO18",
        31:"GPIO19",32:"NC",33:"GPIO21",34:"RXD0",35:"TXD0",36:"GPIO22",37:"GPIO23",
        38:"GND",39:"EP_GND"}
    wroom_pins = [(str(i), wroom_pin_names[i], "passive") for i in range(1, 40)]
    used = {"1":"GND","2":"+3V3","3":"EN","9":"PAIR","10":"IR_TX","11":"IR_RX",
            "12":"STATUS","15":"GND","25":"IO0","34":"U0RXD","35":"U0TXD",
            "38":"GND","39":"GND"}
    add("ESP32_WROOM_32E", "U", "ESP32-WROOM-32E-N16", wroom_pins, "U1",
        "ESP32-WROOM-32E-N16", "RF_Module:ESP32-WROOM-32E", 105, 90, used)

    usb_pins = [(p, p, "passive") for p in
                ["A1","A4","A5","A6","A7","A8","A9","A12","B1","B4","B5","B6","B7","B8","B9","B12","S1"]]
    usb_nets = {p:"+5V" for p in ["A4","A9","B4","B9"]} | {p:"GND" for p in ["A1","A12","B1","B12","S1"]} | {"A5":"CC1","B5":"CC2"}
    add("USB_C_16P", "J", "USB-C POWER ONLY", usb_pins, "J1", "TYPE-C-31-M-12",
        "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 35, 42, usb_nets)
    add("LDO3", "U", "AMS1117-3.3", [("1","GND","passive"),("2","OUT","passive"),("3","IN","passive")],
        "U2", "AMS1117-3.3", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", 62, 42,
        {"1":"GND","2":"+3V3","3":"+5V"})
    for ref, value, nets, xy in [
        ("R_CC1","5.1k",{"1":"CC1","2":"GND"},(35,70)),
        ("R_CC2","5.1k",{"1":"CC2","2":"GND"},(35,82)),
        ("C1","22uF",{"1":"+5V","2":"GND"},(62,60)),
        ("C2","22uF",{"1":"+3V3","2":"GND"},(62,72)),
        ("C3","100nF",{"1":"+5V","2":"GND"},(62,84)),
        ("C4","22uF",{"1":"+3V3","2":"GND"},(80,42)),
        ("C5","100nF",{"1":"+3V3","2":"GND"},(80,54)),
        ("R_EN","10k",{"1":"+3V3","2":"EN"},(80,66)),
        ("C_EN","1uF",{"1":"EN","2":"GND"},(80,78)),
        ("R_BOOT","10k",{"1":"+3V3","2":"IO0"},(80,90)),
        ("R_PAIR","10k",{"1":"+3V3","2":"PAIR"},(80,102)),
    ]:
        kind = "R2" if ref.startswith("R") else "C2"
        prefix = "R" if ref.startswith("R") else "C"
        fp = "Resistor_SMD:R_0603_1608Metric" if prefix == "R" else ("Capacitor_SMD:C_1206_3216Metric" if value == "22uF" else "Capacitor_SMD:C_0603_1608Metric")
        add(kind, prefix, value, two, ref, value, fp, *xy, nets)
    for ref, net, xy in [("SW_RESET","EN",(62,102)),("SW_BOOT","IO0",(62,114)),("SW_PAIR","PAIR",(80,114))]:
        add("SW2","SW","SW_Push",two,ref,"TS-1088R-02026","IRBlaster:TS-1088R-02026",*xy,{"1":net,"2":"GND"})

    # Page 2 region: IR transmitter branches.
    for i in range(1,13):
        yy = 135 + (i-1)*7.5
        value = "OSI5LA7WA1B" if i in {1,4,7,10} else "OSI5LA5A33A-B"
        add("R2_PWR","R","100R 0.25W",two,f"R{i}","100R 0.25W","Resistor_SMD:R_1206_3216Metric",30,yy,{"1":"+5V","2":f"LED_A{i}"})
        add("LED2","D","IR LED",[("1","A","passive"),("2","K","passive")],f"D{i}",value,"IRBlaster:IR_LED_5mm_Universal_P2.54",55,yy,{"1":f"LED_A{i}","2":"LED_DRAIN"},True)
    add("R2","R","220R",two,"R_GATE","220R","Resistor_SMD:R_0603_1608Metric",85,138,{"1":"IR_TX","2":"MOS_GATE"})
    add("R2","R","10k",two,"R_PD","10k","Resistor_SMD:R_0603_1608Metric",85,150,{"1":"MOS_GATE","2":"GND"})
    add("MOS3","Q","AO3400A",[("1","G","passive"),("2","S","passive"),("3","D","passive")],"Q1","AO3400A","Package_TO_SOT_SMD:SOT-23",110,144,{"1":"MOS_GATE","2":"GND","3":"LED_DRAIN"})
    add("CP2","C","1000uF",two,"C_BULK","1000uF 10V","Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",110,162,{"1":"+5V","2":"GND"},True)

    # Receiver, status and programming.
    add("RX3","U","OSRB38C9AA",[("1","OUT","passive"),("2","GND","passive"),("3","VCC","passive")],
        "U_RX","OSRB38C9AA","IRBlaster:OSRB38C9AA",145,138,{"1":"IR_RX","2":"GND","3":"IR_RX_VCC"},True)
    add("R2","R","100R",two,"R_RX","100R","Resistor_SMD:R_0603_1608Metric",145,154,{"1":"+3V3","2":"IR_RX_VCC"})
    for ref, val, xy in [("C_RX1","22uF",(145,166)),("C_RX2","22uF",(145,178)),("C_RX3","100nF",(145,190))]:
        fp = "Capacitor_SMD:C_1206_3216Metric" if val == "22uF" else "Capacitor_SMD:C_0603_1608Metric"
        add("C2","C",val,two,ref,val,fp,*xy,{"1":"IR_RX_VCC","2":"GND"})
    add("R2","R","1k",two,"R_STATUS","1k","Resistor_SMD:R_0603_1608Metric",175,138,{"1":"STATUS","2":"STATUS_LED"})
    add("LED2","D","RED",[("1","A","passive"),("2","K","passive")],"D_STATUS","RED","LED_SMD:LED_0603_1608Metric",175,150,{"1":"STATUS_LED","2":"GND"})
    prog_pins = [(str(i+1),n,"passive") for i,n in enumerate(["3V3","GND","TX","RX","EN","IO0"])]
    prog_nets = {str(i+1):n for i,n in enumerate(["+3V3","GND","U0TXD","U0RXD","EN","IO0"])}
    add("PROG6","J","PROG",prog_pins,"J_PROG","1x6 2.54mm DNP","Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",175,175,prog_nets,True)

    notes = [
        ("IR BLASTER HW V1.0 / REV4 - COMPLETE STANDALONE PRODUCT", 20, 245, 1.5),
        ("USB-C is 5V POWER ONLY. CC1/CC2 each use 5.1k Rd to GND.", 20, 251, 0.9),
        ("U1: ESP32-WROOM-32E-N16. GPIO25=IR_TX, GPIO26=IR_RX, GPIO27=STATUS, GPIO33=PAIR.", 20, 256, 0.9),
        ("Q1 AO3400A mapping: pin1=G, pin2=S, pin3=D. D1..D12 mapping: pin1=A, pin2=K.", 20, 261, 0.9),
        ("HYBRID BUILD: D1-D12, U_RX, C_BULK and J_PROG are DNP/user soldered.", 20, 266, 0.9),
    ]
    texts = [f'  (text "{t}" (exclude_from_sim no) (at {x} {y} 0) {effects(s, justify="left bottom")} (uuid "{uid()}"))' for t,x,y,s in notes]

    sch = f'''(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "9.0")
  (uuid "{project_uuid}")
  (paper "A4")
  (title_block (title "IR Blaster HW V1.0 Complete") (rev "REV4") (company "haya1010"))
  (lib_symbols
{chr(10).join(lib_defs.values())}
  )
{chr(10).join(texts)}
{chr(10).join(labels)}
{chr(10).join(instances)}
  (sheet_instances (path "/" (page "1")))
  (embedded_fonts no)
)
'''
    (OUT / f"{PROJECT}.kicad_sch").write_text(sch)


def generate_project() -> None:
    pro = {
        "boards": [], "cvpcb": {}, "erc": {}, "libraries": {},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": 0.15, "track_width": 0.25, "via_diameter": 0.8, "via_drill": 0.4},
                {"name": "LED_POWER", "clearance": 0.15, "track_width": 1.0, "via_diameter": 1.0, "via_drill": 0.5},
            ],
            "meta": {"version": 3}, "net_colors": None,
            "netclass_assignments": {"+5V":"LED_POWER", "LED_DRAIN":"LED_POWER"},
            "netclass_patterns": []},
        "pcbnew": {}, "schematic": {}, "sheets": [],
        "text_variables": {"BOARD_DIAMETER_MM":"78.0", "HW_VERSION":"V1.0", "REVISION":"REV4"},
    }
    (OUT / f"{PROJECT}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")


def generate_bom_and_cpl() -> None:
    fields = ["Reference","Qty","Value","Footprint","Manufacturer","MPN","JLC/LCSC","Assembly","Notes"]
    with (OUT / "BOM.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(fields)
        for p in PLACEMENTS:
            w.writerow([p.ref,1,p.value,p.footprint,p.manufacturer,p.mpn,p.lcsc,p.assembly,p.notes])

    assembled = [p for p in PLACEMENTS if p.assembly == "SMT" and p.lcsc not in {"", "DNP"}]
    with (OUT / "assembly" / "BOM_JLCPCB.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["Comment","Designator","Footprint","LCSC Part #"])
        for p in assembled:
            w.writerow([p.value,p.ref,p.footprint,p.lcsc])
    with (OUT / "assembly" / "CPL_JLCPCB.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["Designator","Mid X","Mid Y","Rotation","Layer"])
        for p in assembled:
            w.writerow([p.ref,f"{p.x:.3f}mm",f"{-p.y:.3f}mm",f"{p.rotation:.1f}","Top"])


def generate_docs() -> None:
    docs = OUT / "docs"
    (OUT / "README.md").write_text("""# IR Blaster HW V1.0 — Complete Standalone Revision (REV4)

This is the complete standalone product revision: ESP32-WROOM, USB-C 5V input,
3.3V regulator, twelve IR transmitters, IR receiver, buttons and both prototype
and factory programming interfaces are on one 78 mm circular PCB.

The default order is **HYBRID PCBA**. JLCPCB installs all SMT parts. The user
hand-solders D1–D12, U_RX, C_BULK and optionally J_PROG. This preserves the exact
OptoSupply LEDs and allows the emitters to be tilted 30–45 degrees outward.

## Order files

- `manufacturing/ir_blaster_v4_complete_gerbers.zip`
- `assembly/BOM_JLCPCB.csv`
- `assembly/CPL_JLCPCB.csv`
- `docs/ir_blaster_v4_complete_assembly_drawing.pdf` (generated by release script)
- `docs/ASSEMBLY_DRAWING.md`

Do not order until every item in `PRE_ORDER_CHECKLIST.md` is checked.
""")
    (docs / "ASSUMPTIONS.md").write_text("""# Assumptions

- Board diameter is 78.0 mm to fit the complete standalone circuit without
  crowding the antenna, USB-C and twelve hand-formed LEDs.
- D1/D4/D7/D10 are OSI5LA7WA1B wide-angle; the other eight are
  OSI5LA5A33A-B narrow-angle.
- Angled LED insertion is not treated as a guaranteed standard JLCPCB process;
  the order BOM therefore marks all twelve LEDs DNP.
- OSRB38C9AA, 1000uF radial capacitor and the prototype header are also DNP in
  the cost-optimized hybrid order.
- A protected, regulated 5V/2A USB supply is required. USB data is not wired.
""")
    (docs / "FACTORY_PROGRAMMING.md").write_text("""# Factory programming

Connector/pogo order: **3V3, GND, board TX, board RX, EN, IO0**.

1. Normally power the board through USB-C and connect programmer GND, RX->board
   TX, TX->board RX, EN and IO0. Leave programmer 3V3 disconnected.
2. Hold IO0 low, pulse EN low, release EN, then release IO0 to enter download mode.
3. Flash with `esptool.py --chip esp32 --port PORT write_flash 0x0 firmware.bin`.
4. Pulse EN without holding IO0 to return to normal boot.

Never connect programmer 3V3 while USB-C power is present. If powering through
3V3, the programmer must supply ESP32 Wi-Fi peak current with margin.
""")
    (docs / "ASSEMBLY_DRAWING.md").write_text("""# Assembly drawing notes

The companion PDF is a top-side fabrication/silkscreen/courtyard plot. Crossed
footprints are DNP in the HYBRID PCBA order.

- D1/D4/D7/D10: OSI5LA7WA1B wide-angle IR LEDs.
- D2/D3/D5/D6/D8/D9/D11/D12: OSI5LA5A33A-B narrow-angle IR LEDs.
- LED pad 1=A and pad 2=K. Hand-form the leads for a 30–45 degree outward tilt.
- U_RX: OSRB38C9AA, 1=OUT, 2=GND, 3=3V3.
- C_BULK: 1000uF, at least 6.3V; observe polarity.
- J_PROG: optional 2.54mm 1x6 header, 3V3/GND/TX/RX/EN/IO0.
- U1 antenna points east into the marked all-layer keepout.
""")
    (docs / "DESIGN_REVIEW.md").write_text("""# Design review

## Electrical calculations

- Narrow LED worst-case current: (5.0 - 1.6 - 0.03) / 100 = 33.7 mA.
- Twelve-LED peak: approximately 404 mA (about 426 mA at 1.42V VF).
- 100R resistor continuous worst-case: about 0.13 W; selected 1206 is 0.25 W.
- AO3400A at 52mOhm and 0.43A: under 10 mW peak conduction loss.
- ESP32-WROOM transmitter current is typically below 240mA; design transient
  allowance is 500mA.
- AMS1117 dissipation at 500mA is (5-3.3)*0.5 = 0.85 W. The SOT-223 tab uses a
  broad 3V3 copper path and must be kept unobstructed. Normal expected radio
  current gives roughly 0.4W.
- 1000uF supplies 0.4A for 1ms with about 0.4V ideal droop; it primarily reduces
  short wiring/supply transients, not the full command envelope.
- Use a regulated 5V/2A USB supply for simultaneous Wi-Fi and IR margin.

## Pin and polarity checks

- ESP32-WROOM-32E land pattern: KiCad official footprint checked against the
  Espressif recommended pattern; antenna points east and its footprint keepout
  is retained.
- AO3400A SOT-23: 1=Gate, 2=Source, 3=Drain.
- Both OptoSupply LED footprints: 1=Anode, 2=Cathode.
- OSRB38C9AA: 1=OUT, 2=GND, 3=VCC; 2.7–5.5V operation.
- USB-C: CC1 and CC2 each have an independent 5.1k pull-down to GND.

## LDO thermal decision

A 1A SOT-223 LDO was selected instead of a small SOT-23 device. It is simple,
widely stocked and adequate for a normally sub-250mA ESP32 load, but continuous
500mA operation is thermally demanding. The first prototypes must measure U2
case temperature during worst-case Wi-Fi traffic. A buck regulator is the next
revision path if enclosure temperature or power efficiency requires it.
""")
    (docs / "BOM_REVIEW.md").write_text("""# BOM review

The production BOM contains only SMT items with confirmed JLC/LCSC identifiers.
C701343 is Extended, Standard-PCBA-only and requires X-ray. C165948 is Extended
and supports Economic/Standard. C6186 is Basic. Other identifiers and quantities
are authoritative in `assembly/BOM_JLCPCB.csv`.

Hybrid DNP items are the exact OptoSupply LEDs, OSRB38C9AA, 1000uF radial
capacitor and J_PROG header. FULL PCBA is not released because outward lead
forming of the specified LEDs is not guaranteed. Do not accept substitutions
that alter flash size, footprint, polarity or pin ordering.
""")
    (docs / "JLCPCB_ORDER_GUIDE.md").write_text("""# JLCPCB order guide

1. Upload the Gerber ZIP from `manufacturing/`.
2. Select 2 layers, FR-4, 1.6mm, 1oz. Confirm detected size is 78 x 78 mm.
3. Enable Standard PCBA, top side, and upload `assembly/BOM_JLCPCB.csv` and
   `assembly/CPL_JLCPCB.csv`.
   Standard PCBA is mandatory because C701343 is Standard-only and requires X-ray.
4. Confirm every SMT designator and especially U1/J1/U2/Q1 orientation in the
   placement viewer. U1 must point its antenna toward the east-edge keepout.
5. Confirm D1-D12, U_RX, C_BULK and J_PROG are absent from the production BOM.
6. Do not pay until the Gerber viewer, component substitutions, price and the
   pre-order checklist are approved.
""")
    (docs / "PRE_ORDER_CHECKLIST.md").write_text("""# Pre-order checklist

- [ ] ESP32-WROOM-32E-N16 / C701343 and 16MB flash confirmed
- [ ] ESP32 antenna points east and all-layer keepout is visible
- [ ] USB-C TYPE-C-31-M-12 footprint and 5V-only CC resistors confirmed
- [ ] 5V to 3.3V regulator orientation and thermal copper confirmed
- [ ] D1-D12 pin1=A, pin2=K confirmed against the purchased LEDs
- [ ] OSRB38C9AA pin1=OUT, pin2=GND, pin3=VCC confirmed
- [ ] AO3400A pin1=G, pin2=S, pin3=D confirmed
- [ ] BOM and CPL component orientations visually confirmed
- [x] ERC and DRC reports show zero blocking errors and zero unconnected items
- [x] Gerber viewer detects a 2-layer 78 x 78mm board
- [ ] Gerber viewer close-up shows USB opening, all LED holes and pogo pads
- [ ] HYBRID DNP list confirmed: LEDs, receiver, 1000uF, J_PROG
- [ ] JLCPCB live quote and substitutions approved by the user
""")
    (docs / "SOURCES.md").write_text("""# Primary sources

- Espressif ESP32-WROOM-32E/32UE Datasheet v2.0:
  https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.html
- Espressif ESP32 Hardware Design Guidelines:
  https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/
- OptoSupply OSRB38C9AA datasheet:
  https://www.optosupply.com/uppic/2022715399964.pdf
- JLCPCB C701343, C165948, C6186 and selected component part-detail pages.
- OptoSupply OSI5LA5A33A-B and OSI5LA7WA1B manufacturer drawings; pin 1 is
  anode and pin 2 is cathode for the selected footprints.
""")
    (OUT / "requirements.md").write_text("""# Frozen production requirements

Standalone 78mm circular, two-layer IR blaster with ESP32-WROOM-32E-N16,
USB-C 5V input, 1A-class 3.3V regulation, twelve individually resisted 940nm
IR LEDs, AO3400A low-side switch on GPIO25, OSRB38C9AA receiver on GPIO26,
status LED, RESET/BOOT/PAIR buttons, 1x6 header and bottom pogo programming.
Default assembly is hybrid: all SMT by JLCPCB and optical/THT parts by user.
""")


def main() -> None:
    for d in [OUT, OUT / "assembly", OUT / "manufacturing", OUT / "manufacturing" / "gerbers",
              OUT / "docs", OUT / "preview", OUT / "firmware" / "factory_test"]:
        d.mkdir(parents=True, exist_ok=True)
    generate_project()
    generate_board()
    generate_schematic()
    generate_bom_and_cpl()
    generate_docs()
    print(f"Generated {OUT}")


if __name__ == "__main__":
    main()
