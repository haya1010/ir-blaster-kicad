# Factory test firmware

Arduino-ESP32向けの簡易検査スケッチです。Boardは一般的なESP32 Dev Module、Flash sizeは
16 MBを選択します。GPIOは基板回路と固定で、25=IR TX、26=IR RX、27=STATUS、33=PAIRです。

起動後、STATUSが1秒周期で変化し、115200 bpsへ状態を出力します。PAIRを押すと12灯へ
100 msの38 kHzバーストを出します。スマートフォンのカメラまたはIR検出カードで発光を確認し、
別のリモコンをU_RXへ向けて`IR_RX`の変化を確認します。
