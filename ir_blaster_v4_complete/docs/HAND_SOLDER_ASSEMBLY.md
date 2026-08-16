# Hand-solder assembly

JLCPCBから届いた基板へ、次のDNP部品だけを後付けします。

| Reference | Part | Important orientation |
|---|---|---|
| D1, D4, D7, D10 | OSI5LA7WA1B wide-angle | pin 1 = A（四角パッド）、pin 2 = K（丸パッド） |
| Other D1–D12 | OSI5LA5A33A-B narrow-angle | pin 1 = A、pin 2 = K |
| U_RX | OSRB38C9AA | 1=OUT, 2=GND, 3=VCC |
| C_BULK | 1000 uF, 10 V radial | `+`表示側へ正極。定格10 V以上 |
| J_PROG | 1x6, 2.54 mm straight male header | 四角パッドがpin 1=3V3 |

LEDは基板面から2–4 mm浮かせ、外周方向へ30–45°傾けてからはんだ付けします。
隣接LEDやケースへ触れないこと、余ったリードが裏面配線へ短絡しないことを確認します。

U_RXは基板に対して立てて実装します。受光面をケースの開口へ向け、C_BULKやPAIRボタンへ
接触しない高さにします。

組立後、電源投入前に5V-GNDと3V3-GNDの短絡がないこと、LED極性、C_BULK極性を
テスターで確認してください。
