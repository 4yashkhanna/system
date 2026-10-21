# Festivals × City System Map (v7)

An interactive systems map of how Pune's Ganeshotsav festival and everyday city life shape each other. Open `index.html` in a browser.

It merges every loop and finding from the team's *Systems thinking* FigJam board into one connected picture:

- **144 feedback loops** (68 reinforcing, 76 balancing), including all 86 iceberg loops. Each loop is drawn as its own ring with its name circle in the middle.
- **409 boxes, 710 signed links.** Every box appears once, so where loops share a box their rings meet there (40 merge points).
- **17 zones** drawn as territories: local pandals, space and the site, crowds and emergency access, traffic and transport, shops and street trade, the festival engine, residents who absorb it, permissions and coordination, immersion and the river, police capacity, after the festival, noise and the rules, getting there (parking, metro and walking), time and the daily rhythm, the supply chain and festival trade, homes and families, and mandals, patrons and civic networks.
- **An open-system boundary** with the flows that cross it: visitors, money, rules, materials, flowers, power, borrowed capacity and other city events coming in; traffic, waste, noise, stretched services, coverage, departing customers and precedent going out.
- **Trends**: the board's year-on-year data (mandals, nirmalya, immersions, 1.5-day celebrations, procession length, noise monitoring and readings) as charts.

Light theme only.

## What it is built from

| Source on the board | What it contributes |
| --- | --- |
| System Map v5 (Rings in zones) | The 63 loops and which boxes make up each ring, read off v5's layout |
| System Map v4 (Merged) | Every box once, all links, goals, capacities and mental models, the loop descriptions, archetypes, where to act and open questions |
| System Map v3 and the Expanded map | Link signs (+ / −), evidence tags (E, H, ?), source codes and delays |
| System Map v2 (Deep) | 14 loops and 21 boxes the later maps dropped (patronage, media, crowd safety, buses and autos, vendors, DJs, goodwill, bins, VIP visits) |
| The 86 iceberg loop sections | The 34 loops v4/v5 left out, read from their own sections with the board's signs (duplicate pairs #2/#31, #6/#66, #10/#50, #11/#54, #27/#52 merged) |
| Field research (K.P., Dagdusheth), stakeholder and ecosystem maps, empathy maps, dependency map, rich picture, cause and effect | 20 loops built in v7 (parking, time of day, peth retail, hospitals, confrontation, self-regulation, SWaCH, patrons, monitoring and more), the missing stakeholders, four new places to act (★12 to ★15) and the trend data |
| Iceberg and the 86 loops table | Events, structures and mental models, and the event / pattern / hypothesis behind each loop |

Every loop was checked: an R loop has an even number of negative links and a B loop an odd number.

## Using the map

- Drag to move, scroll or pinch to zoom. Zoomed out, the zone labels show; zoom in to read boxes, signs and loop names.
- Click a loop circle to light up its ring and read it round in the panel, with its evidence, iceberg loops, archetype, mental models and where to act.
- Click a box to see every loop it sits on and every link in and out.
- The panel tabs cover the guide and legend, all loops by zone, the zones, where to act (with Meadows' leverage levels), the iceberg, archetypes and mental models, the open-system boundary, trends, open questions and the method.
- Any loop code in the text (R15, B13, ...) is a link. A loop can be opened directly with `index.html#R15`, a zone with `index.html#zone7`.

## Rebuilding

The `build/` folder holds the pipeline and the extracts it reads (`build/source/`).

```
pip install numpy scipy shapely
build/build.sh
```

`model.py` merges the loops (with `additions.py` holding the v7 additions) and checks their signs, `layout.py` places the rings (stress majorisation, with each loop held as a regular ring and each zone kept together), `render.py` draws the arcs, and `build_page.py` writes the page from `page_template.html`. The extraction scripts (`v5parse.py`, `v5loops.py`, `graph.py`, `signs2.py`, `extract34.py`, `dump.py`) regenerate `build/source/` from a fresh FigJam export of the board.
