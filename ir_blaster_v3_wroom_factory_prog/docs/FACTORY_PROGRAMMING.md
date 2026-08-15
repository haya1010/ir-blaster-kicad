# Factory programming

## Interfaces

The same six nets are available on both interfaces:

| Order | Pogo pad | J_PROG | Function |
|---:|---|---|---|
| 1 | TP_PROG_3V3 | pin 1 | 3.3 V supply/measurement |
| 2 | TP_PROG_GND | pin 2 | Ground |
| 3 | TP_PROG_TX | pin 3 | ESP32 TXD0 |
| 4 | TP_PROG_RX | pin 4 | ESP32 RXD0 |
| 5 | TP_PROG_EN | pin 5 | Chip enable/reset |
| 6 | TP_PROG_IO0 | pin 6 | Boot-mode control |

Connect programmer TX to board RX and programmer RX to board TX.

## Recommended safe connection

When the finished board is powered through USB-C, connect only programmer GND,
TX, RX, EN and IO0. Leave the programmer's 3V3 output disconnected. This avoids
two regulators driving the same 3.3 V rail.

To power the entire board from the programmer instead, disconnect USB-C first.
The programmer's 3.3 V output must support ESP32 Wi-Fi current peaks and the
load of the rest of the board. A low-current USB-UART adapter may brown out or
be damaged and must not be assumed suitable.

## Manual download sequence

1. Remove all other power sources or use the five-wire connection above.
2. Connect GND, TX/RX crossed, EN and IO0.
3. Hold IO0 low.
4. Pulse EN low, then release EN high.
5. Release IO0 after the ROM bootloader starts.
6. Flash with `esptool` or an equivalent ESP32 programmer.
7. Reset with IO0 high/floating to boot the application.

Do not leave EN or IO0 driven above 3.3 V. The programmer and board must share
ground before UART or control signals are applied.

## Fixture notes

- Six bottom pads are in a straight 1x6 line at 3.81 mm pitch.
- Exposed copper diameter: 2.4 mm.
- Pad 1 is rectangular and marked `PIN1`/`3V3` on bottom silkscreen.
- Use spring probes appropriate for flat ENIG/HASL pads.
- Add mechanical locating pins to the fixture; do not use pogo pins alone to
  locate the PCB.

