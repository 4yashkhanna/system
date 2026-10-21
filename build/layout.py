"""Global ring layout by stress majorisation, zones as territories.

* Every loop (inside a zone or across zones) is a rigid circle: each pair of its boxes gets the chord
  of a regular polygon and a virtual centre point (the loop marker) sits one radius from each box.
  Shared boxes therefore sit exactly where rings meet.
* Each zone has a virtual hub that pulls its boxes together; hubs are spaced on the planned grid,
  so the topics stay segmented but rings that cross zones sit on the borders between them.
* Zone territories are the union of each box's Voronoi cell (clipped to a disc), smoothed.
"""
import os, json, math, sys
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point, MultiPolygon, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
SRC = HERE + 'source/'
SP = HERE + 'out/'
os.makedirs(SP, exist_ok=True)
M = json.load(open(SP + 'model.json'))
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
rng = np.random.default_rng(seed)

nodes = M['nodes']
idx = {n['id']: i for i, n in enumerate(nodes)}
N = len(nodes)
zone = np.array([n['zone'] for n in nodes])
W = np.array([184.0 if n['kind'] == 'var' else 168.0 for n in nodes])
H = np.array([72.0 if n['kind'] == 'var' else 62.0 for n in nodes])
loops = M['loops']
LM = [np.array([idx[x] for x in l['nodes']]) for l in loops]
NL = len(LM)
CHORD = float(sys.argv[2]) if len(sys.argv) > 2 else 380.0
HUBK = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0


def radius(n):
    return CHORD / (2 * math.sin(math.pi / n))


GRID = {8: (0, 0), 11: (1, 0), 7: (2, 0),
        17: (0, 1), 2: (1, 1), 12: (2, 1), 9: (3, 1),
        1: (0, 2), 6: (1, 2), 3: (2, 2), 10: (3, 2),
        14: (0, 3), 5: (1, 3), 13: (2, 3), 4: (3, 3),
        16: (0, 4), 15: (1, 4)}
if len(sys.argv) > 8:
    GRID = {int(k): tuple(v) for k, v in json.loads(sys.argv[8]).items()}
GRIDPOS = {z: (c + 0.0, r * 0.9) for z, (c, r) in GRID.items()}
ZONES = sorted(GRIDPOS)
NZ = len(ZONES)

# points: nodes, loop centres, zone hubs
n_all = N + NL + NZ
hub = {z: N + NL + i for i, z in enumerate(ZONES)}
INF = 1e9
acc = np.zeros((n_all, n_all))
cnt = np.zeros((n_all, n_all))
kind = np.zeros((n_all, n_all), int)  # 0 none, 1 ring, 2 edge, 3 hub, 4 hub-hub


def add(a, b, d, k):
    acc[a, b] += d
    acc[b, a] += d
    cnt[a, b] += 1
    cnt[b, a] += 1
    kind[a, b] = kind[b, a] = max(kind[a, b], k) if k != 1 else 1


for li, m in enumerate(LM):
    n = len(m)
    r = radius(n)
    for p in range(n):
        for q in range(p + 1, n):
            add(m[p], m[q], 2 * r * math.sin(math.pi * (q - p) / n), 1)
        add(m[p], N + li, r, 1)
inloop = set()
for m in LM:
    for k in range(len(m)):
        inloop.add((m[k], m[(k + 1) % len(m)]))
for e in M['edges']:
    a, b = idx[e['s']], idx[e['t']]
    if (a, b) not in inloop and (b, a) not in inloop:
        add(a, b, 240.0 if e['driver'] else 330.0, 2)
SPREAD = float(os.environ.get('SPREAD', 2900))
for z in ZONES:
    mem = np.where(zone == z)[0]
    rz = 190 * math.sqrt(len(mem))
    for i in mem:
        add(i, hub[z], rz, 3)
for i, a in enumerate(ZONES):
    for b in ZONES[i + 1:]:
        d = math.dist(GRIDPOS[a], GRIDPOS[b])
        add(hub[a], hub[b], d * SPREAD, 4)

G = np.full((n_all, n_all), INF)
has = cnt > 0
G[has] = acc[has] / cnt[has]
np.fill_diagonal(G, 0)
from scipy.sparse.csgraph import shortest_path
Gs = np.where(has, G, 0)
D = shortest_path(Gs, method='D', directed=False)
D[~np.isfinite(D)] = D[np.isfinite(D)].max()
# segmentation: unrelated boxes in different zones keep apart in proportion to their zones' grid distance;
# unrelated boxes in the same zone are held together
SEG = float(sys.argv[4]) if len(sys.argv) > 4 else 0.8
zall = np.concatenate([zone, [loops[li]['zone'] for li in range(NL)], ZONES])
gp = np.array([GRIDPOS[z] for z in zall], float)
hubd = np.hypot(*(gp[:, None, :] - gp[None, :, :]).transpose(2, 0, 1)) * SPREAD
same = zall[:, None] == zall[None, :]
unrel = kind == 0
D = np.where(unrel & ~same, np.maximum(D, SEG * hubd), D)
zsize = {z: 190 * math.sqrt((zone == z).sum()) * 2 for z in ZONES}
zcap = np.array([zsize[z] for z in zall])
D = np.where(unrel & same, np.minimum(D, np.maximum(zcap[:, None], 400)), D)
Wt = 1.0 / np.maximum(D, 1.0) ** 2
Wt[kind == 1] *= float(os.environ.get('RINGW', 16))
Wt[kind == 2] *= 2
Wt[kind == 3] *= 0.6 * HUBK
Wt[unrel & same] *= 1.5
Wt[kind == 4] *= float(sys.argv[7]) if len(sys.argv) > 7 else 100
# pairs in different zones without a direct relation: only care if they are too close
np.fill_diagonal(Wt, 0)


_V = -Wt.copy()
np.fill_diagonal(_V, 0)
np.fill_diagonal(_V, -_V.sum(1))
Vp = np.linalg.pinv(_V)


def smacof(X, iters):
    for _ in range(iters):
        dx = X[:, None, :] - X[None, :, :]
        dist = np.sqrt((dx ** 2).sum(-1)) + 1e-9
        B = -Wt * D / dist
        np.fill_diagonal(B, 0)
        np.fill_diagonal(B, -B.sum(1))
        X = Vp @ B @ X
    dx = X[:, None, :] - X[None, :, :]
    dist = np.sqrt((dx ** 2).sum(-1))
    return X, (Wt * (dist - D) ** 2).sum() / 2


best = None
for trial in range(int(os.environ.get('TRIALS', 2))):
    X0 = np.zeros((n_all, 2))
    for i in range(n_all):
        if i < N:
            z = zone[i]
        elif i < N + NL:
            z = zone[LM[i - N][0]]
        else:
            z = ZONES[i - N - NL]
        X0[i] = np.array(GRIDPOS[z]) * SPREAD + rng.normal(size=2) * 500
    X, s = smacof(X0, 500)
    print('trial', trial, 'stress', round(s, 1))
    if best is None or s < best[1]:
        best = (X, s)
X = best[0]

# ---------- alternate: stress steps, zone cohesion, territorial spacing, overlap removal ----------
w = np.concatenate([W, np.full(NL, 104.0), np.zeros(NZ)])
h = np.concatenate([H, np.full(NL, 104.0), np.zeros(NZ)])
act = np.arange(N + NL)
related = (kind > 0)
zact = zall[act]
diffz = zact[:, None] != zact[None, :]
COH = float(sys.argv[5]) if len(sys.argv) > 5 else 0.15
TGAP = float(sys.argv[6]) if len(sys.argv) > 6 else 220


def remove_overlap(X, iters, extra_gap):
    for it in range(iters):
        X[act] += rng.normal(size=(len(act), 2)) * 0.05
        Xa = X[act]
        dx = Xa[:, 0][:, None] - Xa[:, 0][None, :]
        dy = Xa[:, 1][:, None] - Xa[:, 1][None, :]
        gap = 44 + np.where(diffz & ~related[np.ix_(act, act)], extra_gap, 0)
        gx = (w[act][:, None] + w[act][None, :]) / 2 + gap - np.abs(dx)
        gy = (h[act][:, None] + h[act][None, :]) / 2 + gap * 0.8 - np.abs(dy)
        ov = (gx > 0) & (gy > 0)
        np.fill_diagonal(ov, False)
        if not ov.any():
            break
        horiz = gx < gy * 1.6
        F = np.zeros_like(Xa)
        F[:, 0] = np.where(ov & horiz, np.where(dx >= 0, 1, -1) * gx, 0).sum(1) * 0.2
        F[:, 1] = np.where(ov & ~horiz, np.where(dy >= 0, 1, -1) * gy, 0).sum(1) * 0.2
        X[act] += np.clip(F, -40, 40)
    return X


for rnd in range(14):
    X, _ = smacof(X, 25)
    for z in ZONES:
        m = act[zact == z]
        c = X[m].mean(0)
        X[m] += COH * (c - X[m])
    X = remove_overlap(X, 250, TGAP * (1 - rnd / 16))
X = remove_overlap(X, 1500, 0)

P = X[:N]
C = X[N:N + NL]
# ---------- territories ----------
pts = P.copy()
lo = pts.min(0) - 700
hi = pts.max(0) + 700
frame = np.array([[lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [lo[0], hi[1]]])
# seeds: boxes (corners help the cells hug the box), loop centres belong to their home zone
seeds, sz = [], []
for i in range(N):
    for ox, oy in ((0, 0), (-W[i] / 2, -H[i] / 2), (W[i] / 2, -H[i] / 2), (-W[i] / 2, H[i] / 2), (W[i] / 2, H[i] / 2)):
        seeds.append((P[i, 0] + ox, P[i, 1] + oy))
        sz.append(zone[i])
for li in range(NL):
    seeds.append(tuple(C[li]))
    sz.append(loops[li]['zone'])
for p in np.linspace(lo, hi, 12):
    for q in ((p[0], lo[1] - 2000), (p[0], hi[1] + 2000), (lo[0] - 2000, p[1]), (hi[0] + 2000, p[1])):
        seeds.append(q)
        sz.append(-1)
seeds = np.array(seeds)
vor = Voronoi(seeds)
cells = {z: [] for z in ZONES}
for si, reg_i in enumerate(vor.point_region):
    z = sz[si]
    if z == -1:
        continue
    reg = vor.regions[reg_i]
    if -1 in reg or not reg:
        continue
    poly = Polygon(vor.vertices[reg])
    if not poly.is_valid:
        continue
    cells[z].append(poly.intersection(Point(seeds[si]).buffer(250 if si < 5 * N else 190)))
terr = {}
for z in ZONES:
    u = unary_union(cells[z])
    u = u.buffer(-36).buffer(70).buffer(-34)  # smooth corners, keep a gutter between zones
    parts = [u] if isinstance(u, Polygon) else list(u.geoms)
    keep = [g for g in parts if any(g.contains(Point(*P[i])) for i in np.where(zone == z)[0])]
    terr[z] = unary_union(keep).simplify(4)


def path_of(g):
    polys = [g] if isinstance(g, Polygon) else list(g.geoms)
    d = ''
    for p in polys:
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)
            d += 'M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in cs) + 'Z '
    return d


shift = -np.min([np.array(t.bounds[:2]) for t in terr.values()], axis=0) + np.array([1250, 1250])
P += shift
C += shift
from shapely import affinity
terr = {z: affinity.translate(t, *shift) for z, t in terr.items()}
W_, H_ = np.max([np.array(t.bounds[2:]) for t in terr.values()], axis=0) + 1250

# title anchors: the highest free spot inside each territory
obst = [sbox(P[i, 0] - W[i] / 2 - 20, P[i, 1] - H[i] / 2 - 20, P[i, 0] + W[i] / 2 + 20, P[i, 1] + H[i] / 2 + 20) for i in range(N)]
obst += [Point(*C[li]).buffer(80) for li in range(NL)]
obst_u = unary_union(obst)
anchors = {}
for z, t in terr.items():
    name = M['zones'][str(z)]['name']
    tw = max(len(name) * 25 + 40, 420)
    th = 120
    mem = P[zone == z]
    cx = mem[:, 0].mean()
    x0, y0, x1, y1 = t.bounds
    best = None
    for slack in (30, 260):
        tb = t.buffer(slack)
        for yy in np.arange(y0 - slack + 10, y1 - th, 24):
            for xx in np.arange(x0 - slack + tw / 2, x1 + slack - tw / 2, 24):
                r = sbox(xx - tw / 2, yy, xx + tw / 2, yy + th)
                if tb.contains(r) and not r.intersects(obst_u):
                    sc = yy + 0.35 * abs(xx - cx)
                    if best is None or sc < best[0]:
                        best = (sc, xx, yy)
        if best:
            break
    if best is None:
        best = (0, cx, mem[:, 1].min() - 130)
        print('title fallback', z)
    anchors[z] = dict(x=float(best[1]), y=float(best[2] + 70))
    obst_u = obst_u.union(sbox(best[1] - tw / 2 - 30, best[2] - 20, best[1] + tw / 2 + 30, best[2] + th + 20))

# open-system boundary around everything
allt = unary_union(list(terr.values())).buffer(170).buffer(-60).simplify(6)
if isinstance(allt, MultiPolygon):
    allt = max(allt.geoms, key=lambda g: g.area)
allt = Polygon(allt.exterior)

out = dict(nodes={nodes[i]['id']: dict(x=float(P[i, 0]), y=float(P[i, 1]), w=float(W[i]), h=float(H[i])) for i in range(N)},
           loops={loops[li]['id']: dict(cx=float(C[li, 0]), cy=float(C[li, 1]), r=float(radius(len(LM[li]))),
                                         cross=bool(len(set(zone[LM[li]])) > 1)) for li in range(NL)},
           zones={str(z): dict(path=path_of(terr[z]), tx=anchors[z]['x'], ty=anchors[z]['y'],
                               bounds=list(terr[z].bounds)) for z in ZONES},
           boundary=path_of(allt), boundary_pts=[list(map(float, c)) for c in allt.exterior.coords], width=float(W_), height=float(H_))
json.dump(out, open(SP + 'layout.json', 'w'), indent=0)
print('canvas', round(W_), round(H_))

# ---------- quality metrics ----------
from scipy.spatial import cKDTree
t = cKDTree(P)
_, nn = t.query(P, k=4)
purity = np.mean([(zone[nn[i, 1:]] == zone[i]).mean() for i in range(N)])
ring_err = []
for li, m in enumerate(LM):
    d = np.hypot(*(P[m] - C[li]).T)
    ring_err.append(np.abs(d - radius(len(m))).mean() / radius(len(m)))
zp = {z: round(np.mean([(zone[nn[i, 1:]] == z).mean() for i in np.where(zone == z)[0]]), 2) for z in ZONES}
print(zp)
print(f'METRIC purity={purity:.3f} ring_err={np.mean(ring_err):.3f} ring_err90={np.percentile(ring_err,90):.3f}')
