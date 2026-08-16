# Factory programming

ピン順はヘッダ、ポゴパッドとも同じネットです：
**3V3, GND, board TX, board RX, EN, IO0**。

## 推奨接続（安全）

1. 基板はUSB-Cから5 Vで給電する。
2. Programmerの3V3は接続しない。
3. Programmer GND、RX→board TX、TX→board RX、EN、IO0だけを接続する。
4. IO0をLowに保持し、ENをLow→High、最後にIO0を開放してdownload modeへ入る。
5. 書き込み後はIO0を保持せずENをLow→Highして通常起動する。

Arduino/PlatformIOの個別バイナリ例：

```text
esptool.py --chip esp32 --port PORT --baud 460800 write_flash \
  0x1000 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin
```

0x0から書く場合は、事前に結合したmerged imageだけを使用してください。

## 禁止事項

- USB-C給電中にProgrammerの3V3出力をつながない。
- 3.3 V端子へ5 Vを入れない。
- Programmerから基板全体を3.3 V給電する場合、ESP32のWi-Fiピーク電流まで供給できない
  小電流Programmerを使わない。

初回は`firmware/factory_test/`を書き込み、STATUS、PAIR、IR送信、IR受信、シリアル出力を確認します。
