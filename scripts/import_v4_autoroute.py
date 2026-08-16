#!/usr/bin/env python3
"""Import the completed Specctra session into the KiCad production board."""

from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "ir_blaster_v4_complete" / "ir_blaster_v4_complete.kicad_pcb"
SES = ROOT / "ir_blaster_v4_complete" / "manufacturing" / "ir_blaster_v4_complete.ses"

board = pcbnew.LoadBoard(str(BOARD))
ok = pcbnew.ImportSpecctraSES(board, str(SES))
if not ok:
    raise SystemExit("Specctra session import failed")
pcbnew.SaveBoard(str(BOARD), board)
print(f"Imported {SES}")
print(f"Saved {BOARD}")
