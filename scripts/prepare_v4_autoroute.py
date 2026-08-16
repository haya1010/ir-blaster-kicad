#!/usr/bin/env python3
"""Remove provisional routing and export a Specctra DSN for production routing."""

from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "ir_blaster_v4_complete" / "ir_blaster_v4_complete.kicad_pcb"
DSN = ROOT / "ir_blaster_v4_complete" / "manufacturing" / "ir_blaster_v4_complete.dsn"

board = pcbnew.LoadBoard(str(BOARD))
for item in list(board.GetTracks()):
    board.Remove(item)
pcbnew.SaveBoard(str(BOARD), board)
pcbnew.ExportSpecctraDSN(board, str(DSN))
print(f"Prepared {BOARD}")
print(f"Exported {DSN}")
