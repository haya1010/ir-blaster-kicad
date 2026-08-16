#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h:h}"
PROJECT_DIR="$ROOT/ir_blaster_v4_complete"
PROJECT="$PROJECT_DIR/ir_blaster_v4_complete"
KICAD="/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
GERBER_DIR="$PROJECT_DIR/manufacturing/gerbers"
RELEASE_DIR="$PROJECT_DIR/release"

mkdir -p "$GERBER_DIR" "$PROJECT_DIR/images" "$RELEASE_DIR"

"$KICAD" sch erc --severity-error --exit-code-violations \
  --output "$PROJECT_DIR/erc-report-errors.txt" "$PROJECT.kicad_sch"
"$KICAD" pcb drc --severity-error --exit-code-violations \
  --output "$PROJECT_DIR/drc-report-errors.txt" "$PROJECT.kicad_pcb"

"$KICAD" pcb export gerbers \
  --output "$GERBER_DIR/" \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts \
  --subtract-soldermask "$PROJECT.kicad_pcb"
"$KICAD" pcb export drill --output "$GERBER_DIR/" --format excellon \
  --excellon-units mm --excellon-zeros-format decimal --excellon-oval-format route \
  --excellon-separate-th --generate-map --map-format pdf "$PROJECT.kicad_pcb"

(
  cd "$GERBER_DIR"
  zip -q -FS ../ir_blaster_v4_complete_gerbers.zip \
    ./*.gtl ./*.gbl ./*.gto ./*.gbo ./*.gts ./*.gbs ./*.gm1 ./*.drl
)

"$KICAD" sch export pdf --black-and-white \
  --output "$PROJECT_DIR/docs/ir_blaster_v4_complete_schematic.pdf" "$PROJECT.kicad_sch"
"$KICAD" pcb export pdf --mode-single --black-and-white \
  --sketch-pads-on-fab-layers --crossout-DNP-footprints-on-fab-layers \
  --layers F.Fab,F.SilkS,F.Courtyard,Edge.Cuts \
  --output "$PROJECT_DIR/docs/ir_blaster_v4_complete_assembly_drawing.pdf" \
  "$PROJECT.kicad_pcb"
"$KICAD" pcb render --output "$PROJECT_DIR/images/pcb_top_3d.png" \
  --quality basic --width 1800 --height 1800 --side top --background transparent "$PROJECT.kicad_pcb"
"$KICAD" pcb render --output "$PROJECT_DIR/images/pcb_bottom_3d.png" \
  --quality basic --width 1800 --height 1800 --side bottom --background transparent "$PROJECT.kicad_pcb"

(
  cd "$PROJECT_DIR"
  zip -q -FS "$RELEASE_DIR/ir_blaster_v4_complete_order_bundle.zip" \
    manufacturing/ir_blaster_v4_complete_gerbers.zip \
    assembly/BOM_JLCPCB.csv assembly/CPL_JLCPCB.csv \
    docs/JLCPCB_ORDER_GUIDE.md docs/PRE_ORDER_CHECKLIST.md \
    docs/FACTORY_PROGRAMMING.md docs/HAND_SOLDER_ASSEMBLY.md \
    docs/ASSEMBLY_DRAWING.md docs/VALIDATION.md \
    docs/ir_blaster_v4_complete_schematic.pdf \
    docs/ir_blaster_v4_complete_assembly_drawing.pdf
)

shasum -a 256 \
  "$PROJECT_DIR/manufacturing/ir_blaster_v4_complete_gerbers.zip" \
  "$PROJECT_DIR/assembly/BOM_JLCPCB.csv" \
  "$PROJECT_DIR/assembly/CPL_JLCPCB.csv" \
  "$RELEASE_DIR/ir_blaster_v4_complete_order_bundle.zip" \
  > "$RELEASE_DIR/SHA256SUMS.txt"

echo "Release bundle built: $RELEASE_DIR/ir_blaster_v4_complete_order_bundle.zip"
