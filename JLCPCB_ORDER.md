# JLCPCB 注文チェックリスト

## アップロード

`manufacturing/m5_ir_blaster_revA_gerbers.zip`

## 設定

- FR-4
- 2 Layers
- 52 × 40 mm
- 5 pcs
- 1.6 mm
- 1 oz
- Green solder mask
- White silkscreen
- LeadFree HASL
- Tented vias
- PCB Assembly: 必要に応じて選択
- Panel by JLCPCB: No

### 表面実装だけを依頼する場合

- PCBAタイプ: Economic
- 組立面: Top
- PCBA数量: 5
- BOM: `assembly/BOM_JLCPCB_SMD_ONLY.csv`
- CPL: `assembly/CPL_JLCPCB_SMD_ONLY.csv`
- J1、D1〜D4、U2は実装データから除外済み（手はんだ用）
- R3〜R5は33Ω・0805・0.5W以上または同等の耐パルス品を指定する
- ステンシルは注文しない

## Gerber Viewerで見る場所

- 外形が52 × 40 mmの長方形
- 四隅に3.2 mmの取付穴
- 上辺側に5 mm IR LEDが3個
- 左側に3ピンIR受信器
- 下辺側に4ピンJSTコネクタ
- F.Cu / B.Cu / F.Mask / B.Mask / F.Silkscreen / Edge.Cuts が認識されている
- PTHとNPTHのドリルが認識されている

## 到着後

最初は電流制限付き電源を使い、部品を付ける前に5 V-GND間の短絡がないことを確認します。
次にU1とC1/C2だけを実装して3.3 Vを確認し、その後IR受信部、最後に送信部の順で実装すると安全です。
