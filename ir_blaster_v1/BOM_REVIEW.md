# BOM / JLCPCB review

確認日: 2026-08-11。JLCPCBの在庫は変動するため、発注画面で再確認してください。

| 部品 | MPN | 状態 | 組立方法 | 代替 |
|---|---|---|---|---|
| Wide IR LED ×4 | OptoSupply OSI5LA7WA1B | exact partのJLC在庫を確認できず | **DNP / user solder** | 無断置換しない |
| Narrow IR LED ×8 | OptoSupply OSI5LA5A33A-B | exact partのJLC在庫を確認できず | **DNP / user solder** | 無断置換しない |
| ESP32 socket ×2 | 1×19, 2.54 mm | ユーザー手配 | **DNP / user solder** | 実物のピン寸法で選定 |
| Q1 | ISAHAYA INK021ABS1-T112 | exact partのJLC在庫を確認できず | Global sourcing / consigned候補 | 3.3 V保証品は次版候補 |
| R1–R12 | 100 Ω axial 1/4 W | JLCにTHT抵抗カテゴリあり。発注時にMPN固定 | Wave/manual candidate | 値・定格・外形一致品のみ |
| RG | 220 Ω axial 1/4 W | 同上 | Wave/manual candidate | 同上 |
| RPD | 10 kΩ axial 1/4 W | 同上 | Wave/manual candidate | 同上 |
| Cbulk | 1000 µF, 10 V以上, radial P5.0 | 発注時に外径8 mm以下の在庫品を固定 | Wave/manual candidate | 容量・耐圧・極性・径を維持 |
| Cdec | 100 nF leaded P2.54 | 発注時に在庫品を固定 | Wave/manual candidate | THT維持。SMD化は別承認 |

JLCPCBの公開FAQでは、parts libraryで`wave soldering`指定されたTHTを手作業で組立可能としています。顧客支給部品（consigned parts）も受け付けています。ただしLEDの指定角度は標準保証として確認できないため、本注文データからLEDを除外しています。

参考:

- https://jlcpcb.com/help/article/pcb-assembly-faqs
- https://jlcpcb.com/help/article/jlcpcb-supported-personalized-services
- https://jlcpcb.com/help/article/difference-and-tolerance-explanation-between-via-and-pad-holes

