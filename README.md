# M5 / ESP32 High-Power IR Blaster — Rev A

M5 Atom または ESP32 から家電を操作するための、赤外線送受信ボードです。
既存の `m5-ir-remote-studio` の初期設定に合わせ、送信は GPIO26、受信は GPIO32 を想定しています。

## できること

- 940 nm 高出力IR LEDを3灯同時にパルス駆動
- AO3400A MOSFETでESP32のGPIOを保護
- TSOP38238（38 kHz）でリモコン信号を受信
- 受信部を3.3 Vで動かし、ESP32入力へ安全な電圧で返す
- TX動作確認用の可視LED
- JST-PH 4ピンでM5 Atom／ESP32へ接続
- 52 × 40 mm、M3穴4個

## 接続

| J1 pin | 信号 | M5 Atom / ESP32 |
|---|---|---|
| 1 | IR_TX | GPIO26 |
| 2 | IR_RX | GPIO32 |
| 3 | +5V | 5V |
| 4 | GND | GND |

J1のシルク面表記は左から `TX / RX / 5V / GND` です。Groveケーブルは製品により信号線の割り当てが異なるため、色だけで判断せず導通を確認してください。

## 電気的な目安

IR LED 1灯あたりのピーク電流は、5 V、順方向電圧約1.35 V、33 Ωとして約111 mAです。
3灯合計は送信パルス中に約333 mAとなります。38 kHz変調かつ短いリモコン送信を前提としています。

連続点灯はしないでください。IR LEDにはパルス定格に余裕のある部品（TSAL6200相当）を使い、R3〜R5はパルス負荷に耐える0.5 W品を推奨します。

## KiCadで開く

`m5_ir_blaster.kicad_pro` または `m5_ir_blaster.kicad_pcb` を開いてください。
フットプリントはPCBファイル内に埋め込んであるため、追加ライブラリは不要です。

## JLCPCBで基板だけ注文する

アップロードするファイルは `manufacturing/m5_ir_blaster_revA_gerbers.zip` です。
KiCadプロジェクトZIPではなく、Gerber ZIPの方を使ってください。

推奨する初回設定:

| 項目 | 設定 |
|---|---|
| Base Material | FR-4 |
| Layers | 2 |
| Dimensions | 52 × 40 mm（自動認識を確認） |
| PCB Qty | 5 |
| Thickness | 1.6 mm |
| Copper Weight | 1 oz |
| PCB Color | Green（好みで変更可） |
| Silkscreen | White |
| Surface Finish | LeadFree HASL |
| Via Covering | Tented |
| Remove Order Number | 見た目優先なら Yes |
| PCB Assembly | No（部品は手はんだ） |

アップロード後のGerber Viewerで、外形、M3穴4個、IR LED穴3組、J1の4ピン穴、表面シルクを確認してください。

## 製造前の確認

これは試作Rev Aです。発注前に次を確認してください。

1. 使用するJSTコネクタの実物とピン順
2. 選んだIR LEDの極性と最大パルス電流
3. TSOP38238互換品のピン配列（OUT / GND / VS）
4. KiCadのDRC
5. 実機の5 V供給能力

## データシート確認済みの要点

- MCP1700 SOT-23: 1=GND、2=VOUT、3=VIN
- TSOP38238: 1=OUT、2=GND、3=VS
- TSAL6200: 940 nm、連続100 mA、規定条件でピーク200 mA
- AO3400A: 2.5 Vゲート駆動時のオン抵抗が規定されたロジックレベルMOSFET

メーカー資料:

- https://www.microchip.com/en-us/product/mcp1700
- https://www.vishay.com/docs/82491/tsop382.pdf
- https://www.vishay.com/docs/81010/tsal6200.pdf
- https://www.aosmd.com/products/mosfets/low-voltage-mosfets-12v-30v/ao3400a

## ファームウェア

既存スケッチの設定をそのまま使用できます。

```cpp
static const uint16_t IR_RX_PIN = 32;
static const uint16_t IR_TX_PIN = 26;
```
