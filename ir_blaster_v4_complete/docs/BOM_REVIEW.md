# BOM review

The production BOM contains only SMT items with confirmed JLC/LCSC identifiers.

| Function | JLC/LCSC | PCBA status | Qty/board | Substitution rule |
| --- | --- | --- | ---: | --- |
| ESP32-WROOM-32E-N16 | C701343 | Extended, Standard only, X-ray | 1 | No flash-size or footprint substitution |
| USB-C TYPE-C-31-M-12 | C165948 | Extended, Economic/Standard | 1 | No mechanical substitution |
| AMS1117-3.3 | C6186 | Basic, Economic/Standard | 1 | Same SOT-223 pinout only |
| AO3400A | C20917 | JLC stock SMT | 1 | Pin 1=G, 2=S, 3=D and logic-level gate required |
| 100R 1206 0.25W | C17901 | JLC stock SMT | 12 | 0.25W minimum |
| TS-1088R-02026 | C455280 | JLC stock SMT | 3 | Same land pattern and height |
| Remaining R/C/status LED | BOM identifiers | JLC stock SMT | see BOM | Value, package and voltage rating must match |

Hybrid DNP items: exact OptoSupply LEDs, OSRB38C9AA, 1000uF radial capacitor and
J_PROG header. Do not substitute their polarity or pin ordering.

Inventory and live pricing can change. Re-open every Extended part in the JLCPCB
placement step and do not accept an automatic substitute with a different pinout,
flash size, connector land pattern or MOSFET pin mapping.

## FULL versus HYBRID PCBA

FULL PCBA is not released for ordering: the specified OptoSupply LEDs require
outward lead forming, which is not guaranteed by the standard assembly flow, and
the exact receiver/capacitor mechanical substitutions still require approval.
HYBRID PCBA is the released configuration: JLCPCB installs all SMT parts and the
user installs D1-D12, U_RX, C_BULK and optional J_PROG.

## Price status (USD, 2026-08-16)

The unauthenticated JLCPCB Gerber quote shows PCB fabrication for 5 boards at
$2.00 promotional price and DHL Express (DDP) shipping estimate of $28.57. PCBA,
components, Extended-part fees and X-ray are not included until the authenticated
BOM/CPL step. A practical planning range for 5 HYBRID boards is about $65–80
delivered, but the authenticated cart is authoritative. Do not use this range as
a purchase approval.
