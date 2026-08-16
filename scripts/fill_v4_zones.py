#!/usr/bin/env python3
"""Refill copper zones after importing the routed Specctra session."""

from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "ir_blaster_v4_complete" / "ir_blaster_v4_complete.kicad_pcb"

board = pcbnew.LoadBoard(str(BOARD))
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD), board)
print(f"Filled zones and saved {BOARD}")
