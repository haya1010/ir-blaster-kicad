# Design review

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
