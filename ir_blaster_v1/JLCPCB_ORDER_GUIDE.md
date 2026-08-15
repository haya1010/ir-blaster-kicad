# JLCPCB order guide

## PCB

- Upload: `manufacturing/ir_blaster_v1_gerbers.zip`
- Base material: FR-4
- Layers: 2
- Dimensions: 74.0 × 74.0 mm（円形外形をViewerで確認）
- PCB Qty: 5（初回推奨）
- Thickness: 1.6 mm
- Copper weight: 1 oz
- Solder mask: White
- Silkscreen: Black
- Surface finish: LeadFree HASL（好みでENIG）
- Via covering: Tented
- Confirm production file: Yes（初回推奨）

## PCBA

- Assembly side: Top
- LED D1–D12: Do not place / DNP
- ESP32 sockets J1/J2: Do not place / DNP
- Q1: exact MPNをGlobal sourcingまたはconsignedで確保できない場合はDNPに変更
- THT passives: portal上で`wave soldering`またはmanual assembly対象になっているexact partを割当
- `TBD_AT_ORDER`を残したまま注文しない

## Viewerで見る箇所

1. 円形Edge.Cutsが1本で閉じている。
2. LED 12個の各1番穴がA、2番穴がK/共通Drain。
3. ESP32の2列が25.40 mm、各19穴。
4. `USB ↓` と手元ボードのUSB側が一致。
5. Cbulkの`+`表示とBOMの極性が一致。
6. Q1のシルクが左からS/D/G。

## 到着後

LED/ESP32ソケットを付ける前に、5V–GND短絡がないこと、GPIO25–Gate、Drain busの導通を確認します。次に電流制限付き5 V電源で1灯相当から試験し、最後に全灯38 kHzパルスを確認します。

