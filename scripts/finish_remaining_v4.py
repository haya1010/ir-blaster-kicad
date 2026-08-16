#!/usr/bin/env python3
"""Close the final USB VBUS and ground-shell connections after autorouting."""

from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "ir_blaster_v4_complete" / "ir_blaster_v4_complete.kicad_pcb"


def p(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


board = pcbnew.LoadBoard(str(BOARD))


def path(net_name: str, coords: list[tuple[float, float]], width: float, layer: int) -> None:
    for a, b in zip(coords, coords[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(p(*a)); t.SetEnd(p(*b))
        t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(layer)
        t.SetNet(board.FindNet(net_name)); board.Add(t)


def via(net_name: str, xy: tuple[float, float]) -> None:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(p(*xy)); v.SetWidth(pcbnew.FromMM(0.60))
    v.SetDrill(pcbnew.FromMM(0.30)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(board.FindNet(net_name)); board.Add(v)


# The inner side of J1 A4/B9 is boxed in by the adjacent USB contacts and the
# connector locating hole. Fan out toward the board edge instead, then change
# layers in the clear space in front of the receptacle. This keeps VBUS away
# from every data contact and uses an ordinary 0.30 mm finished via.
vbus_via = (102.45, 137.30)
path("+5V", [(102.45, 136.045), vbus_via], 0.25, pcbnew.F_Cu)
via("+5V", vbus_via)
path("+5V", [vbus_via, (101.90, 135.60), (99.7632, 134.3761)], 0.30, pcbnew.B_Cu)

# Tie the bottom-side programming GND pad to the router's nearby front-side
# GND endpoint without putting a via in the pogo contact itself.
prog_gnd_track_end = (106.00, 116.3756)
prog_gnd_via = (107.00, 116.3756)
via("GND", prog_gnd_via)
path("GND", [prog_gnd_track_end, prog_gnd_via], 0.35, pcbnew.F_Cu)
path("GND", [prog_gnd_via, (107.20, 118.00), (107.81, 120.00)], 0.35, pcbnew.B_Cu)

# Join the two right-hand shield stakes directly. All shield and receiver GND
# through-hole pads use solid B.Cu zone connections to prevent starved thermals.
path("GND", [(104.32, 130.95), (104.32, 135.13)], 0.50, pcbnew.F_Cu)
for fp in board.GetFootprints():
    if fp.GetReference() == "J1":
        for pad in fp.Pads():
            if pad.GetNumber() == "S1":
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    elif fp.GetReference() == "U_RX":
        for pad in fp.Pads():
            if pad.GetNumber() == "2":
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    elif fp.GetReference() == "TP_PROG_GND":
        # Keep the pogo contact flat (no via-in-pad); connect it solidly to the
        # continuous bottom ground plane instead.
        for pad in fp.Pads():
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD), board)
print(f"Finished final two connections and saved {BOARD}")
