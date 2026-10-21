#!/usr/bin/env bash
# Rebuild ../index.html from the FigJam extracts in source/.
# Needs Python 3 with numpy, scipy and shapely (pip install numpy scipy shapely).
set -euo pipefail
cd "$(dirname "$0")"
python3 model.py        # merge v4/v5, v2 (Deep) and the v7 additions (additions.py), check every loop's sign
python3 layout.py        # ring layout (stress majorisation) and zone territories
python3 render.py       # arcs, boxes, loop markers as SVG
python3 build_page.py out/map.html
cp out/map.standalone.html ../index.html
echo "Built ../index.html"
