#!/usr/bin/env python3
"""Refill zones in a KiCad PCB using KiCad's bundled pcbnew Python API."""

import sys
from pathlib import Path

import pcbnew


pcb_path = Path(sys.argv[1]).resolve()
board = pcbnew.LoadBoard(str(pcb_path))
for zone in board.Zones():
    zone.SetIslandRemovalMode(1)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(pcb_path), board)
print(f"Filled zones: {pcb_path}")
