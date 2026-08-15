# Manufacturing notes

## PCB

- Shape: circular, 74.0 mm diameter
- Layers: 2
- Thickness: 1.6 mm
- Minimum designed signal clearance: 0.25 mm
- Signal track width: 0.25–0.30 mm
- Standard vias: 0.40 mm drill / 0.80 mm pad
- WROOM thermal vias: 0.30 mm drill / 0.70 mm pad
- Bottom GND copper pour

## Assembly

- U1: ESP32-WROOM-32E-N16, JLC/LCSC C701343
- J_PROG: DNP; user-installed 2.54 mm straight male header if needed
- Pogo pads: bare PCB features, not components

J_PROG uses KiCad's standard `PinHeader_1x06_P2.54mm_Vertical` footprint:
1.00 mm finished hole and 1.70 mm pad. This provides a 0.35 mm annular ring and
accepts common 0.64 mm square pins.

The ESP32 antenna end is placed at the board perimeter. Do not add copper,
components, metal case parts or wiring within the marked antenna keepout in the
full-product merge.

## Release limitation

This package validates the programming-interface architecture only. It must not
be ordered as the final blaster until the remaining power and IR circuitry from
the master specification is integrated and a complete mechanical/3D review is
performed.

