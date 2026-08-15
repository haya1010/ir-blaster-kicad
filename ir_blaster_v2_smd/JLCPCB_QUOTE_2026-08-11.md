# JLCPCB preliminary quote — 2026-08-11

Configuration: 74 x 74 mm, 2-layer FR-4, white solder mask, 5 boards, Economic PCBA, top-side SMT.

## Quote observed in JLCPCB portal

- PCB: USD 2.00
- Economic PCBA: USD 12.37
  - Setup fee: USD 8.18
  - Stencil: USD 1.53
  - Components (5 BOM line items / 80 placed parts): USD 1.50
  - SMT assembly: USD 0.26
  - Nitrogen reflow: USD 0.90
- Total: USD 14.37
- Shipping and tax: not included in the final PCBA total above
- Separate PCB-only screen showed an estimated USD 8.95 UPS shipping charge at the time of the check.

## Confirmed JLCPCB parts

| Function | Designators | JLC/LCSC | Part | Portal component cost for 5 boards |
|---|---|---:|---|---:|
| LED current resistors | R1-R12 | C17901 | 100 ohm, 1206, 250 mW | USD 0.7380 |
| Gate resistor | RG | C22962 | 220 ohm, 0603 | USD 0.0425 |
| Gate pull-down | RPD | C25804 | 10 kohm, 0603 | USD 0.2055 |
| MOSFET | Q1 | C20917 | AO3400A, SOT-23 | USD 0.4205 |
| Decoupling capacitor | Cdec | C14663 | 100 nF, 50 V, X7R, 0603 | USD 0.0925 |

LEDs, ESP32 pin sockets, and the 1000 uF bulk capacitor are excluded from PCBA and intended for user hand soldering in this cost-optimized quote.

## Important

This is a preliminary cost check, not an order release. JLCPCB accepted the Gerber/BOM/CPL and matched all 16 designators groups. The generated PCB still needs a final KiCad connectivity/zone-fill review and visual placement review before purchase.
