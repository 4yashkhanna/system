"""Turn model.json + layout.json into the SVG body of the map (arcs, boxes, loop markers, zones)."""
import os, json, math, html, re

HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
SRC = HERE + 'source/'
SP = HERE + 'out/'
os.makedirs(SP, exist_ok=True)
M = json.load(open(SP + 'model.json'))
LY = json.load(open(SP + 'layout.json'))
NP = LY['nodes']
nodes = {n['id']: n for n in M['nodes']}
loops = M['loops']
LP = LY['loops']

# which loops each edge belongs to
edge_loops = {}
for l in loops:
    ns = l['nodes']
    for k in range(len(ns)):
        edge_loops.setdefault((ns[k], ns[(k + 1) % len(ns)]), []).append(l['id'])
loop_by_id = {l['id']: l for l in loops}
node_loops = {}
for l in loops:
    for n in l['nodes']:
        node_loops.setdefault(n, []).append(l['id'])


def ring_centre(lid):
    p = LP[lid]
    return p['cx'], p['cy']
    ns = loop_by_id[lid]['nodes']
    return sum(NP[n]['x'] for n in ns) / len(ns), sum(NP[n]['y'] for n in ns) / len(ns)


def orientation(lid):
    ns = loop_by_id[lid]['nodes']
    s = 0
    for k in range(len(ns)):
        a, b = NP[ns[k]], NP[ns[(k + 1) % len(ns)]]
        s += a['x'] * b['y'] - b['x'] * a['y']
    return 1 if s > 0 else -1  # 1 = clockwise on screen


def rect_contains(nid, x, y, m=7):
    p = NP[nid]
    return abs(x - p['x']) <= p['w'] / 2 + m and abs(y - p['y']) <= p['h'] / 2 + m


def f(v):
    return f'{v:.1f}'


def arc_path(a, b, cx, cy, gentle=False):
    """Circular arc a->b that goes the short way round the ring centre (cx,cy), bulging outward."""
    ax, ay, bx, by = NP[a]['x'], NP[a]['y'], NP[b]['x'], NP[b]['y']
    mx, my = (ax + bx) / 2, (ay + by) / 2
    dx, dy = bx - ax, by - ay
    ch = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / ch, dx / ch
    s = (cx - mx) * nx + (cy - my) * ny  # signed offset of the ring centre from the chord
    sgn = 1 if s >= 0 else -1
    if gentle:
        s = sgn * ch * 1.6
    else:
        s = sgn * min(max(abs(s), ch * 0.22), ch * 3.0)
    ox, oy = mx + s * nx, my + s * ny
    R = math.hypot(ax - ox, ay - oy)
    aa = math.atan2(ay - oy, ax - ox)
    ab = math.atan2(by - oy, bx - ox)
    d = (ab - aa + math.pi) % (2 * math.pi) - math.pi
    n = 60
    return [(ox + R * math.cos(aa + d * i / n), oy + R * math.sin(aa + d * i / n)) for i in range(n + 1)]


def quad_path(a, b, bend=0.12):
    ax, ay, bx, by = NP[a]['x'], NP[a]['y'], NP[b]['x'], NP[b]['y']
    mx, my = (ax + bx) / 2, (ay + by) / 2
    dx, dy = bx - ax, by - ay
    cx, cy = mx - dy * bend, my + dx * bend
    n = 40
    return [((1 - t) ** 2 * ax + 2 * (1 - t) * t * cx + t * t * bx, (1 - t) ** 2 * ay + 2 * (1 - t) * t * cy + t * t * by)
            for t in (i / n for i in range(n + 1))]


def clip(pts, a, b):
    i = 0
    while i < len(pts) - 2 and rect_contains(a, *pts[i]):
        i += 1
    j = len(pts) - 1
    while j > i + 1 and rect_contains(b, *pts[j], m=9):
        j -= 1
    return pts[max(i - 1, 0):][: j - max(i - 1, 0) + 2] if False else pts[i:j + 1]


def to_d(pts):
    # smooth polyline (points are dense)
    s = 'M' + f(pts[0][0]) + ' ' + f(pts[0][1])
    step = max(1, len(pts) // 18)
    keep = pts[step::step]
    if keep[-1] != pts[-1]:
        keep.append(pts[-1])
    # quadratic smoothing through midpoints
    prev = pts[0]
    for k in range(len(keep)):
        p = keep[k]
        if k < len(keep) - 1:
            q = keep[k + 1]
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            s += f' Q{f(p[0])} {f(p[1])} {f(m[0])} {f(m[1])}'
        else:
            s += f' L{f(p[0])} {f(p[1])}'
    return s


def esc(t):
    return html.escape(t, quote=True)


def wrap(label, width_chars):
    words = label.split()
    lines, cur = [], ''
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width_chars:
            cur = (cur + ' ' + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


out = []
# ---------- zones ----------
ZCOL = {1: 'z1', 2: 'z2', 3: 'z3', 4: 'z4', 5: 'z5', 6: 'z6', 7: 'z7', 8: 'z8', 9: 'z9', 10: 'z10', 11: 'z11', 12: 'z12', 13: 'z13'}
zg = ['<g id="zones">']
zt = ['<g id="ztitles">']
for z, b in LY['zones'].items():
    zi = M['zones'][z]
    zg.append(f'<path class="zone {ZCOL[int(z)]}" data-zone="{z}" d="{b["path"]}"/>')
    zt.append(f'<g class="zt {ZCOL[int(z)]}" data-zone="{z}"><text class="znum" x="{f(b["tx"])}" y="{f(b["ty"])}">{z}</text>'
              f'<text class="ztitle" x="{f(b["tx"])}" y="{f(b["ty"] + 34)}">{esc(zi["name"].upper())}</text></g>')
zt.append('</g>')
zg.append('</g>')
zg.append('</g>')

# ---------- edges ----------
eg = ['<g id="edges">']
lg = ['<g id="elabels">']
edata = []
for k, e in enumerate(M['edges']):
    a, b = e['s'], e['t']
    ls = edge_loops.get((a, b), [])
    types = set(loop_by_id[x]['type'] for x in ls)
    if ls:
        # draw on the smallest in-zone loop's circle
        best = sorted(ls, key=lambda x: (LP[x]['cross'], len(loop_by_id[x]['nodes'])))[0]
        rc = ring_centre(best)
        pts = arc_path(a, b, rc[0], rc[1], gentle=False)
        cls = 'both' if types == {'R', 'B'} else ('r' if 'R' in types else 'b')
    else:
        pts = quad_path(a, b)
        cls = 'drv' if e['driver'] else 'free'
    pts = clip(pts, a, b)
    if len(pts) < 2:
        continue
    d = to_d(pts)
    dash = ' unk' if e['ev'] == '?' else ''
    eid = f'e{k}'
    loops_attr = ' '.join(ls)
    eg.append(f'<path id="{eid}" class="edge {cls}{dash}" d="{d}" data-s="{a}" data-t="{b}" data-loops="{loops_attr}" marker-end="url(#ah-{cls})"/>')
    # sign near the arrowhead (CLD convention), evidence tag beside it
    pi = max(0, len(pts) - 1 - max(3, len(pts) // 7))
    px, py = pts[pi]
    qx, qy = pts[min(pi + 1, len(pts) - 1)]
    tx, ty = qx - px, qy - py
    tl = math.hypot(tx, ty) + 1e-6
    ox, oy = -ty / tl * 11, tx / tl * 11
    sg = e['sign']
    tag = e['ev']
    lg.append(f'<g class="elab {cls}" data-edge="{eid}"><text class="sg" x="{f(px + ox)}" y="{f(py + oy + 4)}">{sg}</text>'
              + (f'<text class="ev" x="{f(px + ox + 8)}" y="{f(py + oy + 4)}">{esc(tag)}</text>' if tag else '') + '</g>')
    if e['delay']:
        mi = len(pts) // 2
        mx, my = pts[mi]
        nx_, ny_ = pts[min(mi + 1, len(pts) - 1)]
        tx, ty = nx_ - mx, ny_ - my
        tl = math.hypot(tx, ty) + 1e-6
        ux, uy = tx / tl, ty / tl
        vx, vy = -uy, ux
        dd = ''
        for o in (-3, 3):
            cx_, cy_ = mx + ux * o, my + uy * o
            dd += f'M{f(cx_ - vx * 8)} {f(cy_ - vy * 8)} L{f(cx_ + vx * 8)} {f(cy_ + vy * 8)} '
        lg.append(f'<path class="delay" data-edge="{eid}" d="{dd}"/>')
    edata.append(dict(id=eid, s=a, t=b, sign=sg, ev=e['ev'], src=e['src'], delay=e['delay'], loops=ls, driver=e['driver'], origin=e['origin']))
eg.append('</g>')
lg.append('</g>')

# ---------- nodes ----------
ng = ['<g id="nodes">']
for nid, n in nodes.items():
    p = NP[nid]
    x, y, w, h = p['x'], p['y'], p['w'], p['h']
    nl = node_loops.get(nid, [])
    cls = ['node', 'k-' + n['kind'], 'f-' + n['fam']]
    if len(nl) >= 3 and n['kind'] == 'var':
        cls.append('merge')
    if n['star']:
        cls.append('star')
    label = n['label']
    tag = ''
    if n['kind'] == 'mental':
        label = label.replace('MENTAL MODEL: ', '')
        tag = 'MENTAL MODEL'
    elif n['kind'] == 'goal':
        label = label.replace('GOAL: ', '')
        tag = 'GOAL'
    elif n['kind'] == 'capacity':
        label = label.replace('CAPACITY: ', '')
        tag = 'CAPACITY'
    elif n['kind'] == 'outside':
        tag = 'OUTSIDE PUSH'
    cw = 27 if n['kind'] == 'var' else 26
    lines = wrap(label, cw)
    fs = 11.2
    if len(lines) > (4 if n['kind'] == 'var' else 3):
        lines = wrap(label, cw + 6)
        fs = 9.6
    lh = fs * 1.2
    total = len(lines) * lh + (12 if tag else 0)
    ty0 = y - total / 2 + lh * 0.8 + (12 if tag else 0)
    g = [f'<g class="{" ".join(cls)}" id="n-{nid}" data-id="{nid}" transform="translate(0,0)">',
         f'<rect x="{f(x - w / 2)}" y="{f(y - h / 2)}" width="{f(w)}" height="{f(h)}" rx="{16 if n["kind"] == "var" else 6}"/>']
    if tag:
        g.append(f'<text class="ntag" x="{f(x)}" y="{f(y - total / 2 + 8)}">{tag}</text>')
    for k, line in enumerate(lines):
        g.append(f'<text class="nl" x="{f(x)}" y="{f(ty0 + k * lh)}" style="font-size:{fs}px">{esc(line)}</text>')
    if n['star']:
        g.append(f'<g class="starb"><circle cx="{f(x + w / 2 - 4)}" cy="{f(y - h / 2 + 2)}" r="11"/><text x="{f(x + w / 2 - 4)}" y="{f(y - h / 2 + 6)}">★{n["star"]}</text></g>')
    g.append('</g>')
    ng.extend(g)
ng.append('</g>')

# ---------- loop markers ----------
mg = ['<g id="markers">']
for l in loops:
    p = LP[l['id']]
    cx, cy = p['cx'], p['cy']
    t = l['type'].lower()
    nm = wrap(l['name'], 15)
    rr = 27
    # clockwise turning arrow around the identifier (Sterman convention)
    cwise = orientation(l['id'])
    a0, a1 = (-2.2, 1.9) if cwise == 1 else (1.9 - math.pi, -2.2 - math.pi)
    ar = rr + 6
    sx, sy = cx + ar * math.cos(a0), cy + ar * math.sin(a0)
    ex, ey = cx + ar * math.cos(a1), cy + ar * math.sin(a1)
    mg.append(f'<g class="lm {t}{" xz" if p["cross"] else ""}" id="m-{l["id"]}" data-loop="{l["id"]}">'
              f'<circle class="halo" cx="{f(cx)}" cy="{f(cy)}" r="{rr + 12}"/>'
              f'<path class="turn" d="M{f(sx)} {f(sy)} A{ar} {ar} 0 1 {1 if cwise == 1 else 0} {f(ex)} {f(ey)}" marker-end="url(#ah-turn-{t})"/>'
              f'<circle class="disc" cx="{f(cx)}" cy="{f(cy)}" r="{rr}"/>'
              f'<text class="code" x="{f(cx)}" y="{f(cy + 5)}">{l["id"]}</text>')
    for k, line in enumerate(nm[:3]):
        mg.append(f'<text class="lname" x="{f(cx)}" y="{f(cy + rr + 22 + k * 12)}">{esc(line)}</text>')
    mg.append('</g>')
mg.append('</g>')

WIDTH, HEIGHT = LY['width'], LY['height']
json.dump(dict(svg='\n'.join(zg + zt + eg + ng + lg + mg), width=WIDTH, height=HEIGHT, edges=edata),
          open(SP + 'render.json', 'w'))
print('svg chars', sum(len(s) for s in zg + eg + ng + lg + mg), WIDTH, HEIGHT)
