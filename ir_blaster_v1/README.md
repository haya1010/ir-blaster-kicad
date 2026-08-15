# IR Blaster V1 — ESP32 DevKitC 38-pin shield

写真のユニバーサル基板版を、74.0 mm円形・2層PCBとして再構成したKiCad 9プロジェクトです。12灯のLEDとESP32用1×19ピンソケット2本は、ユーザーの指定により **DNP（未実装）** とし、スルーホール、極性表示、外向き矢印だけを用意しています。

## 確定仕様

- `BOARD_DIAMETER_MM = 74.0`
- 2-layer FR-4、1.6 mm、1 oz
- 推奨色: White solder mask / Black silkscreen
- ESP32 DevKitC V4: 2.54 mmピッチ×19、2列間隔25.40 mm、基板幅27.94 mm
- IR LED: 12個。広角4個（0/90/180/270°）、狭角8個（その間の30°刻み）
- LED/ESP32ソケット: DNP、ユーザー手はんだ
- GPIO25 → 220 Ω → INK021ABS1 gate、10 kΩ pull-down
- 5 V–GND: 1000 µF + 100 nF

## ファイル

- `ir_blaster_v1.kicad_pro/.kicad_sch/.kicad_pcb`: KiCadプロジェクト
- `manufacturing/`: Gerber、Excellon、製造ZIP
- `assembly/`: BOM/CPL候補（LEDとソケットは除外）
- `docs/`: 回路図、基板PDF、組立図
- `preview/`: Top/Bottom/3D PNG
- `BOM.csv`, `BOM_REVIEW.md`, `DESIGN_REVIEW.md`, `JLCPCB_ORDER_GUIDE.md`, `ASSUMPTIONS.md`

## 検証結果

- KiCad ERC: 0 error / 0 warning
- KiCad PCB DRC: 0 DRC violations
- KiCad 9.0.6では、塗り潰し済み+5Vゾーンが自分自身の同一点を指す `1 unconnected pads` 診断を出します。部品パッド間の未配線ではなく、Gerberと銅箔PDFでゾーン連続性を確認しています。

## 発注前に必ず確認

1. 手元のESP32ボードが公式DevKitC V4互換の25.40 mm列間隔・19ピンであること。
2. 使用するメスソケットのピンが1.0 mm完成穴を通ること。
3. LEDは1番穴=A、2番穴=K。全12個を外向き30〜45°程度に手はんだすること。
4. Q1の3.3 V動作はメーカー保証値ではないため、最初は電流制限付き電源で確認すること。
5. JLCPCB注文画面でQ1およびTHT受動部品の実在庫・フットプリントを再確認すること。

## 公式資料

- Espressif DevKitC V4: https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html
- DevKitC寸法PDF: https://dl.espressif.com/dl/schematics/esp32_devkitc_v4_dimensions.pdf
- OSI5LA5A33A-B datasheet: https://akizukidenshi.com/goodsaffix/OSI5LA5A33A-B.pdf
- OSI5LA7WA1B datasheet: https://akizukidenshi.com/goodsaffix/OSI5LA7WA1B.pdf
- INK021ABS1 datasheet: https://www.idc-com.co.jp/product/Search/Pdf/en/121/INK021ABS1/0/

