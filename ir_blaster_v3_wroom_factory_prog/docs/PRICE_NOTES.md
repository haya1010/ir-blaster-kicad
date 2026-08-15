# Price notes

The programming interface itself has almost no PCBA assembly cost:

- the pogo pads are copper features in the PCB artwork;
- J_PROG is DNP and absent from the production BOM/CPL;
- the extra through holes normally do not create a separate assembly charge.

The expected increase comes mainly from replacing the user-supplied DevKit with
an assembled ESP32-WROOM-32E-N16 module. JLCPCB lists C701343 as an Extended
part for Standard PCBA, so the quote can include the module price, an Extended-
part loading fee and any module inspection/X-ray requirements. Shipping, tax,
stencil and fixture costs are separate.

## 2026-08-12 live cart quote

The V3 Gerbers, BOM and corrected CPL were uploaded to JLCPCB as a five-piece,
top-side Standard PCBA order. JLCPCB detected a 2-layer 74 x 74 mm board and
matched U1 to C701343 (ESP32-WROOM-32E-N16, Extended). The component-placement
viewer was checked after correcting the CPL Y-coordinate sign.

| Item | Live quote |
|---|---:|
| PCB fabrication, five pieces | US$2.00 |
| Standard PCBA | US$69.50 |
| Setup fee | US$25.56 |
| Stencil | US$8.21 |
| Panel / large-size surcharge | US$0.00 |
| Five ESP32 modules | US$25.13 |
| Feeder loading | US$1.53 |
| SMT assembly | US$0.38 |
| X-ray inspection | US$8.20 |
| Packaging | US$0.49 |
| PCB + PCBA merchandise total | **US$71.50** |
| Current shipping estimate | US$8.95 |
| Current cart subtotal | **US$80.45** |

The selected normal build time was 24 hours for PCB fabrication and 3–4 days
for assembly. The cart showed 497.70 g. Shipping is an estimate and taxes,
currency conversion, coupons and any later engineering-review adjustments are
not included. No separate fixture or panel charge appeared in this live quote.
The order was added to the cart but was not submitted or paid.

## 2026-08-11 working estimate (superseded by the live quote above)

JLCPCB currently identifies C701343 as Extended, Standard-PCBA-only, and says an
assembly support fixture is required. The displayed module price was US$4.6528
at quantity 1+, with 15,984 units shown in stock. JLCPCB's published Standard
PCBA charges include US$25 one-side setup, US$7.86 one-side stencil, US$1.50 per
loaded Basic/Extended part, US$0.0016 per solder joint, and X-ray at US$1.57 per
piece for 1–10 pieces.

For five milestone boards with only U1 assembled, the published line items give
this lower-bound estimate:

| Item | Estimate |
|---|---:|
| Standard PCBA one-side setup | US$25.00 |
| Stencil | US$7.86 |
| One feeder load | US$1.50 |
| Five ESP32 modules | US$23.26 |
| X-ray, five pieces | US$7.85 |
| Placement/joint charge | about US$0.31 |
| Published-subtotal lower bound | about **US$65.79** |

PCB fabrication, the module support fixture, component attrition, packing,
shipping and tax are not included. The likely checkout total is therefore above
US$65.79. X-ray is a provisional assumption because the module has hidden
soldering areas; if JLCPCB does not apply it, subtract US$7.85 (US$57.94 before
the excluded items). A US$7.81 panel charge may also appear if JLCPCB requires
assembly panelization. The module fixture price is not published on the part
page and can only be confirmed by the live order review.

This milestone quote is not the final full-product price because USB-C power
and IR output components are not yet present.
