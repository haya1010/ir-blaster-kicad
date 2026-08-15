# IR Blaster V3 — WROOM Factory Programming Interface

This is a separate KiCad revision. It does not overwrite `ir_blaster_v1` or
`ir_blaster_v2_smd`.

## Scope

This revision implements the section-8 programming interface milestone:

- ESP32-WROOM-32E-N16 footprint and UART0 programming nets
- bottom-side six-pad factory pogo interface
- separate 2.54 mm 1x6 prototype header, marked DNP
- pin-1 and per-signal silkscreen labels
- JLCPCB BOM/CPL and fabrication outputs
- safe programming instructions

It is an integration milestone, not yet the complete standalone product. USB-C,
the regulator, IR LED drivers, IR receiver, bulk capacitor, buttons and final
case/3D interference checks still need to be merged from the master specification
before a production order.

## Pinout

| Pin | Net | Board label |
|---:|---|---|
| 1 | +3V3 | 3V3 |
| 2 | GND | GND |
| 3 | ESP32 TXD0 | TX |
| 4 | ESP32 RXD0 | RX |
| 5 | EN | EN |
| 6 | IO0 | IO0 |

The bottom pogo pads use the same order in a straight 1x6 array at 3.81 mm
pitch. Pad diameter is 2.4 mm and pad 1 is rectangular.

## Verification status

- PCB DRC: 0 electrical errors, 0 unconnected pads
- Schematic ERC: 0 violations
- Remaining DRC warnings: embedded custom pogo footprint library entries and
  the intentional WROOM footprint change described below

The official KiCad `ESP32-WROOM-32E` land pattern is used. Its 0.20 mm exposed-
pad thermal-via drills were enlarged to 0.30 mm with 0.70 mm pads to fit the
normal JLCPCB manufacturing capability/cost class. This intentional difference
is why KiCad reports a library mismatch warning for U1.

## Manufacturing files

- `manufacturing/gerbers/`: Gerber and drill files
- `manufacturing/ir_blaster_v3_wroom_factory_prog_gerbers.zip`: PCB upload ZIP
- `assembly/BOM_JLCPCB.csv`: assembled parts only
- `assembly/CPL_JLCPCB.csv`: placement data
- `BOM.csv`: engineering BOM including DNP items

`J_PROG` and all pogo pads are PCB-only/DNP and are excluded from the JLCPCB
production BOM and placement file.

