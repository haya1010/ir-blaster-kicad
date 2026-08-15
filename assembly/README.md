# JLCPCB 表面実装データ

このフォルダのBOM/CPLは、表面実装部品だけをJLCPCBへ依頼するためのデータです。

## アップロードするファイル

- BOM: `BOM_JLCPCB_SMD_ONLY.csv`
- CPL: `CPL_JLCPCB_SMD_ONLY.csv`

## JLCPCBで実装する部品

- R1〜R7
- C1〜C4
- Q1
- U1

## 自分ではんだ付けするため、BOM/CPLから除外した部品

- J1: JST-PH 4ピン
- D1〜D3: 5mm IR LED
- D4: 3mm表示LED
- U2: TSOP38238（挿入型IR受信器）

## 部品選択時の注意

- Q1はLCSC `C20917`（AO3400A）を指定しています。
- U1はLCSC `C39051`（Microchip MCP1700T-3302E/TT）を指定しています。
- R3〜R5はIR LEDのパルス電流制限抵抗です。通常の0.125W品ではなく、33Ω・0805・0.5W以上または同等の耐パルス品を選びます。該当品がJLCPCB在庫にない場合、この3点だけ未実装にして手はんだします。
- 抵抗・コンデンサのLCSC番号は固定していません。在庫と基本部品区分を見て、JLCPCBの部品選択画面で同等品を選びます。
- CPLの座標はKiCadが出力する基板座標です。部品配置確認画面で、シルクの向きとパッド位置が一致することを必ず確認します。

## 推奨注文設定

- PCBAタイプ: Economic
- 組立面: Top
- PCBA数量: 5
- 部品選択: 顧客による（セルフサービス）
- ステンシル: 注文しない
- Through-hole assembly: なし
