# Validation record

- Tool: KiCad CLI 9.0.6
- Board: `ir_blaster_v4_complete.kicad_pcb`
- Schematic: `ir_blaster_v4_complete.kicad_sch`
- Electrical rules: 0 blocking errors
- Board rules: 0 blocking errors
- Unconnected items: 0
- Final board: 78 mm circular, 2 copper layers, 1.6 mm nominal thickness
- DNP mechanical review: LED ring, U_RX, C_BULK and J_PROG have separate footprints
- Programming review: 1x6 header plus bottom 2x3 pogo pads share all six nets
- JLCPCB Gerber upload: accepted on 2026-08-16; detected 2 layers and 78 x 78 mm
- JLCPCB part status: C701343 is Extended, Standard-PCBA-only and requires X-ray

Reports are stored as `erc-report-errors.txt` and `drc-report-errors.txt`.
The remaining manufacturing gate is the authenticated JLCPCB BOM/CPL placement,
substitution viewer and cart quote. Payment is intentionally excluded.
