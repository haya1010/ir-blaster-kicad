# IR Blaster V2 SMD

Cost-optimized derivative of `ir_blaster_v1`.

- User hand solder: D1-D12 IR LEDs, J1/J2 ESP32 DevKit sockets, Cbulk 1000 uF
- JLCPCB top-side SMT: R1-R12, RG, RPD, Q1, Cdec
- R1-R12 use 1206 250 mW parts for LED-current resistor power margin
- Q1 changes from the THT INK021ABS1 to the 3.3 V logic-level AO3400A (SOT-23)
- Electrical control remains GPIO25 through 220 ohm gate resistance with 10 kohm pull-down

Manufacturing uploads:

- `manufacturing/ir_blaster_v2_smd_gerbers_jlc.zip`
- `assembly/BOM_JLCPCB.csv`
- `assembly/CPL_JLCPCB.csv`

Do not place an order until the final KiCad zone-fill/connectivity and JLCPCB placement preview have been reviewed.
