"""Assemble the interactive system map page from model.json, layout.json and render.json."""
import os, json, re, math, html, sys
from shapely.geometry import Polygon, Point
from shapely.ops import nearest_points
from shapely.geometry import LineString

HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
SRC = HERE + 'source/'
SP = HERE + 'out/'
os.makedirs(SP, exist_ok=True)
OUT = sys.argv[1] if len(sys.argv) > 1 else SP + 'map.html'
M = json.load(open(SP + 'model.json'))
LY = json.load(open(SP + 'layout.json'))
R = json.load(open(SP + 'render.json'))
ice = open(SRC + 'iceberg.txt').read().split('\n')
table = open(SRC + 'all86_table.txt').read().strip().split('\n')[1:]
esc = lambda t: html.escape(t, quote=True)

# ---------- iceberg ----------
iceberg = {}
for row in table:
    parts = row.split(' | ')
    m = re.match(r'^(#\d+) (.*)$', parts[0])
    iceberg[m.group(1)] = dict(title=m.group(2), event=parts[1], pattern=parts[2], hyp=parts[3])
layers = {'events': [], 'structures': [], 'mental': []}
for line in ice:
    m = re.match(r'^\[\d+:\d+\] (.*?) → (#\d+(?:, #\d+)*)$', line)
    if m and m.group(1).startswith('"'):
        layers['mental'].append(dict(text=m.group(1), refs=m.group(2).split(', '), star=False))
# the events block ends where the first structure starts ("No channel ...")
ev, st = [], []
seen_struct = False
for line in ice:
    m = re.match(r'^\[\d+:\d+\] (.*?) → (#\d+(?:, #\d+)*)$', line)
    if not m:
        continue
    text, refs = m.group(1), m.group(2).split(', ')
    star = text.startswith('★ ')
    text = text[2:] if star else text
    if text.startswith('"'):
        continue
    if 'No channel for private adaptation' in text:
        seen_struct = True
    (st if seen_struct else ev).append(dict(text=text, refs=refs, star=star))
layers['events'], layers['structures'] = ev, st

# ---------- texts ----------
T = M['texts']
act = []
for m in re.finditer(r'★(\d+) (.*?)(?= ★\d+ |$)', T['WHERE TO ACT']):
    body = m.group(2).strip()
    act.append(dict(n=int(m.group(1)), text=body, codes=re.findall(r'\b[RB]\d+\b', body)))
MEADOWS = {1: (6, 'Information flows'), 2: (5, 'Rules'), 3: (6, 'Information flows'), 4: (5, 'Rules'),
           5: (9, 'Delays'), 6: (6, 'Information flows'), 7: (8, 'Balancing feedback'), 8: (10, 'Physical structure'),
           9: (4, 'Self-organisation'), 10: (10, 'Physical structure'), 11: (5, 'Rules')}
for a in act:
    a['meadows'] = MEADOWS[a['n']]
mental = [dict(belief=m.group(1), codes=re.findall(r'[RB]\d+', m.group(2)))
          for m in re.finditer(r'"([^"]+)": ((?:[RB]\d+(?:, )?)+)', T['MENTAL MODELS HOLDING'])]
arche = []
names = ['Limits to growth', 'Fixes that fail', 'Shifting the burden', 'Eroding goals', 'Success to the successful']
txt = T['ARCHETYPES WE THINK WE SEE']
for i, n in enumerate(names):
    a = txt.index(n + ':')
    b = min([txt.index(x + ':') for x in names if txt.index(x + ':') > a] + [len(txt)])
    body = txt[a + len(n) + 1:b].strip()
    arche.append(dict(name=n, text=body, codes=re.findall(r'\b[RB]\d+\b', body)))
ADDED_ARCH = [
    ('Limits to growth', 'Added from v2: coverage grows the festival (R31) until the same coverage turns into public pressure and rules (B39); belonging grows it (R32) until tolerance runs out (B36).', ['R31', 'B39', 'R32', 'B36']),
    ('Fixes that fail', 'Added from v2: barricades put up for crowd safety (B41) feed the diversion ripple (R11) and the transport squeeze (R35).', ['B41', 'R11', 'R35']),
    ('Shifting the burden', 'Added from v2: bigger festivals load the permission system, which thins enforcement and lets more road be taken (R36).', ['R36']),
    ('Success to the successful', 'Added from v2: rivalry and patronage feed the mandals that already draw coverage and money (R30, R33).', ['R30', 'R33']),
]
for n, t, c in ADDED_ARCH:
    arche.append(dict(name=n, text=t, codes=c, added=True))
unknowns = [s.strip() + '?' if not s.strip().endswith(')') else s.strip()
            for s in re.split(r'(?<=\))\s(?=[A-Z])', T["WHAT WE STILL DON'T KNOW"]) if s.strip()]

# ---------- boundary flows ----------
NP = LY['nodes']
nid = {n['label']: n['id'] for n in M['nodes']}


def ids(*labels):
    out = []
    for l in labels:
        hit = [n['id'] for n in M['nodes'] if n['label'].startswith(l)]
        assert hit, l
        out.append(hit[0])
    return out


FLOWS = [
    ('in', 'Visitors from across Pune and beyond', 'Over 15 lakh devotees in the central peths by 21 Sep.', ids('VISITOR FOOTFALL', 'TRIPS TO THE BIG CENTRAL')),
    ('in', 'Money from outside', 'State festival grants (2025), patrons, sponsors and election season.', ids('STATE FESTIVAL GRANTS', 'DONATIONS, VARGANI', 'POLITICAL PATRONAGE')),
    ('in', 'Rules made elsewhere', 'Courts, NGT and MPCB orders; noise limits; PMC three-day removal rule.', ids('RULES AND COURT ORDERS', 'GOAL: 55 DB', 'GOAL: STREET RESTORED')),
    ('in', 'Idols, materials and hired crews', '10 to 12 lakh idols installed in homes and mandals; decor, sound and light crews.', ids('IDOLS INSTALLED', 'TEMPORARY DECOR', 'HIRED CREWS')),
    ('in', 'City capacity on loan', 'One day of police capacity, 3,970 PMC workers, the metro running till 2 am.', ids('CAPACITY: ONE DAY', 'CAPACITY: PMC WORKERS', 'CAPACITY: METRO')),
    ('in', 'VIP visits on peak evenings', 'Outside events that bend enforcement and close roads.', ids('VIP VISITS')),
    ('out', 'Traffic spilled onto the wider city', 'Side-road bottlenecks, rerouted buses and circling autos.', ids('CONGESTION ON SURROUNDING', 'NEW BOTTLENECKS', 'BUSES REROUTED')),
    ('out', 'Waste and nirmalya into the Mula-Mutha', '68.6 tonnes of nirmalya collected in six days; 11,331 idols at collection centres.', ids('WASTE, NIRMALYA', 'IDOLS IMMERSED')),
    ('out', 'Noise past the festival street', 'Rehearsals for weeks before, DJs and loudspeakers on the five exempt nights.', ids('NOISE NEAR HOMES', 'AMPLIFIED SOUND')),
    ('out', 'Thinner services elsewhere in the city', 'Officers and PMC staff borrowed from routine work.', ids('ROUTINE CIVIC AND POLICE', 'STAFF AND SERVICES DIVERTED')),
    ('out', 'Image and coverage', 'Media and social media carry the festival, and its harms, to the whole city.', ids('MEDIA AND SOCIAL MEDIA', 'PUBLIC AND POLITICAL PRESSURE')),
    ('out', 'Precedent carried into next year', 'The time boundary: sites, layouts and lessons (or their absence) roll over.', ids('SITE CARRY-OVER', 'LESSONS CARRIED', 'CHANGES TO FESTIVAL ARRANGEMENTS')),
]
bpoly = Polygon(LY['boundary_pts'])
bc = bpoly.centroid
flows, fsvg = [], []
placed = []
for k, (d, title, detail, targets) in enumerate(FLOWS):
    cx = sum(NP[t]['x'] for t in targets) / len(targets)
    cy = sum(NP[t]['y'] for t in targets) / len(targets)
    # ray from the map centre through the targets, to the boundary
    vx, vy = cx - bc.x, cy - bc.y
    L = math.hypot(vx, vy) + 1e-6
    vx, vy = vx / L, vy / L
    best = None
    for off in [0, 0.12, -0.12, 0.24, -0.24, 0.36, -0.36, 0.5, -0.5, 0.65, -0.65, 0.8, -0.8]:
        a = math.atan2(vy, vx) + off
        ux, uy = math.cos(a), math.sin(a)
        far = Point(bc.x + ux * 20000, bc.y + uy * 20000)
        hit = LineString([(bc.x, bc.y), (far.x, far.y)]).intersection(bpoly.exterior)
        pts = [hit] if hit.geom_type == 'Point' else list(getattr(hit, 'geoms', []))
        if not pts:
            continue
        bp = max(pts, key=lambda p: p.distance(bc))
        px, py = bp.x + ux * 470, bp.y + uy * 470
        if all(abs(px - qx) > 600 or abs(py - qy) > 230 for qx, qy in placed):
            best = (bp, px, py, ux, uy)
            break
    bp, px, py, ux, uy = best
    placed.append((px, py))
    ax0, ay0 = (px - ux * 210, py - uy * 120)
    ax1, ay1 = (bp.x + ux * 18, bp.y + uy * 18)
    if d == 'out':
        ax0, ay0, ax1, ay1 = bp.x + ux * 18, bp.y + uy * 18, px - ux * 210, py - uy * 120
    fsvg.append(f'<g class="flow {d}" data-flow="{k}" tabindex="0" role="button" aria-label="{esc(title)}">'
                f'<path class="farrow" d="M{ax0:.0f} {ay0:.0f} L{ax1:.0f} {ay1:.0f}" marker-end="url(#ah-flow)"/>'
                f'<rect x="{px - 260:.0f}" y="{py - 90:.0f}" width="520" height="180" rx="22"/>'
                f'<text class="ftag" x="{px - 232:.0f}" y="{py - 44:.0f}">{"INFLOW" if d == "in" else "OUTFLOW"}</text>')
    words, lines, cur = title.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > 26:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    for i, l in enumerate(lines[:2]):
        fsvg.append(f'<text class="ftitle" x="{px - 232:.0f}" y="{py + 6 + i * 40:.0f}">{esc(l)}</text>')
    fsvg.append('</g>')
    flows.append(dict(dir=d, title=title, detail=detail, targets=targets))

# boundary label along the top
bx0, by0, bx1, by1 = bpoly.bounds
top = min(LY['boundary_pts'], key=lambda p: p[1])
bound_svg = (f'<g id="boundary"><path class="bound" d="{LY["boundary"]}"/>'
             f'<text class="btitle" x="{top[0]:.0f}" y="{top[1] - 90:.0f}">SYSTEM BOUNDARY</text>'
             f'<text class="bsub" x="{top[0]:.0f}" y="{top[1] - 52:.0f}">The festival streets of Dagdusheth and Koregaon Park, their surrounding routes, and the agencies, courts and river they touch</text></g>')

# ---------- node / loop / edge data for the page ----------
loop_nodes = {}
for l in M['loops']:
    for n in l['nodes']:
        loop_nodes.setdefault(n, []).append(l['id'])
nodes = [dict(id=n['id'], label=n['label'], zone=n['zone'], kind=n['kind'], fam=n['fam'], star=n['star'], v2=n['v2'],
              loops=loop_nodes.get(n['id'], [])) for n in M['nodes']]
zone_of = {n['id']: n['zone'] for n in M['nodes']}
loops = []
for l in M['loops']:
    loops.append(dict(id=l['id'], type=l['type'], name=l['name'], zone=l['zone'],
                      zones=sorted(set(zone_of[n] for n in l['nodes'])), nodes=l['nodes'], text=l.get('text', ''),
                      refs=l.get('refs', []), refs_full=l.get('refs_full', ''), src=l['src'], unknown=l['unknown']))
edges = R['edges']
DATA = dict(zones=M['zones'], nodes=nodes, loops=loops, edges=edges, iceberg=iceberg, layers=layers, act=act,
            mental=mental, arche=arche, unknowns=unknowns, sentences=T['THE SYSTEM IN SENTENCES'],
            merge=T['HOW THE LOOPS MERGE'], flows=flows,
            pos={k: [round(v['x']), round(v['y'])] for k, v in NP.items()},
            lpos={k: [round(v['cx']), round(v['cy'])] for k, v in LY['loops'].items()},
            zb={k: v['bounds'] for k, v in LY['zones'].items()},
            zc={str(z): [round(sum(NP[n['id']]['x'] for n in M['nodes'] if n['zone'] == z) / max(1, sum(1 for n in M['nodes'] if n['zone'] == z))),
                         round(sum(NP[n['id']]['y'] for n in M['nodes'] if n['zone'] == z) / max(1, sum(1 for n in M['nodes'] if n['zone'] == z)))] for z in range(1, 13)},
            zshort={'1': 'Local pandals', '2': 'Space and the site', '3': 'Crowds and emergency access', '4': 'Traffic and transport',
                    '5': 'Shops and street trade', '6': 'Festival engine', '7': 'Residents who absorb it', '8': 'Permissions and coordination',
                    '9': 'Immersion and the river', '10': 'Police capacity', '11': 'After the festival', '12': 'Noise and the rules'},
            bounds=[bx0 - 760, by0 - 300, bx1 + 760, by1 + 300])

defs = '<defs>' + ''.join(
    f'<marker id="ah-{k}" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="{s}" markerHeight="{s}" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="ah ah-{k}"/></marker>'
    for k, s in [('r', 6.2), ('b', 6.2), ('both', 6.2), ('free', 7), ('drv', 7), ('turn-r', 5), ('turn-b', 5), ('flow', 5)]) + '</defs>'
W, H = LY['width'], LY['height']
svg = (f'<svg id="map" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="System map: 77 feedback loops across 12 zones">'
       f'{defs}<g id="world">{bound_svg}{R["svg"]}<g id="flows">{"".join(fsvg)}</g></g></svg>')
minisvg = (f'<svg id="mini" viewBox="0 0 {W:.0f} {H:.0f}" aria-hidden="true"><path class="mbound" d="{LY["boundary"]}"/>'
           + ''.join(f'<path class="mz z{z}" d="{b["path"]}"/>' for z, b in LY['zones'].items())
           + '<rect id="minivp" x="0" y="0" width="10" height="10"/></svg>')

tpl = open(HERE + 'page_template.html').read()
page = (tpl.replace('/*__DATA__*/', 'const D = ' + json.dumps(DATA, ensure_ascii=False, separators=(',', ':')) + ';')
        .replace('<!--__SVG__-->', svg).replace('<!--__MINI__-->', minisvg))
open(OUT, 'w').write(page)
# standalone copy for the repository: same page inside a full document
head, body = page.split('<div class="app">', 1)
full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);box-sizing:border-box}[hidden]{display:none!important}</style>\n'
        + head + '</head>\n<body>\n<div class="app">' + body + '\n</body>\n</html>\n')
open(OUT.replace('.html', '.standalone.html'), 'w').write(full)
print('wrote', OUT, len(page) // 1024, 'KB')
