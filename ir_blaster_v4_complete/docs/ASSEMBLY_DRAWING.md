# Assembly drawing notes

The companion drawing is `ir_blaster_v4_complete_assembly_drawing.pdf`. It is a
top-side fabrication/silkscreen/courtyard plot; crossed footprints are DNP in the
recommended HYBRID PCBA order.

## JLCPCB-installed SMT parts

- Install every designator listed in `assembly/BOM_JLCPCB.csv` on the top side.
- U1 antenna points toward the east board edge. No copper, trace, component or
  metal enclosure is allowed in the marked antenna keepout.
- J1 is a 5 V power-only USB-C connector. U2 tab is 3V3. Q1 pinout is
  1=Gate, 2=Source, 3=Drain.

## User-installed DNP parts

- D1/D4/D7/D10: OSI5LA7WA1B wide-angle IR LEDs.
- D2/D3/D5/D6/D8/D9/D11/D12: OSI5LA5A33A-B narrow-angle IR LEDs.
- Every IR LED uses pad 1=A and pad 2=K. Insert radially outward and hand-form
  the leads so the optical axis tilts approximately 30–45 degrees away from the
  PCB normal. Keep all LED bodies at a consistent height before soldering.
- U_RX: OSRB38C9AA, pad 1=OUT, pad 2=GND, pad 3=3V3.
- C_BULK: 1000 uF, at least 6.3 V radial electrolytic; observe the `+` marking.
- J_PROG: optional 2.54 mm 1x6 header, pin 1=3V3 followed by GND, TX, RX, EN,
  IO0. Leave uninstalled for production.

The bottom-side 2x3 pogo array exposes the same six programming nets and is not
an assembled component. See `FACTORY_PROGRAMMING.md` before applying power.
