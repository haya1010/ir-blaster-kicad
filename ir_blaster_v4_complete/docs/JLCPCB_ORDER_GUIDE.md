# JLCPCB order guide

1. Upload the Gerber ZIP from `manufacturing/`.
2. Select 2 layers, FR-4, 1.6mm, 1oz. Confirm detected size is 78 x 78 mm.
3. Enable Standard PCBA, top side, and upload `assembly/BOM_JLCPCB.csv` and
   `assembly/CPL_JLCPCB.csv`.
   Standard PCBA is mandatory because C701343 is Standard-only and requires X-ray.
4. Confirm every SMT designator and especially U1/J1/U2/Q1 orientation in the
   placement viewer. U1 must point its antenna toward the east-edge keepout.
5. Confirm D1-D12, U_RX, C_BULK and J_PROG are absent from the production BOM.
6. Do not pay until the Gerber viewer, component substitutions, price and the
   pre-order checklist are approved.

The PCB is intentionally larger than JLCPCB's small-board promotional tier, and
C701343 is an Extended part. Treat the web cart total as authoritative because
setup, Extended-part, X-ray, shipping and tax charges can change independently.
