"""Build the merged system model (v4/v5 loops + v2 deep loops) from the FigJam extracts."""
import os, json, re

HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
SRC = HERE + 'source/'
SP = HERE + 'out/'
os.makedirs(SP, exist_ok=True)
v4 = open(SRC + 'v4.txt').read().split('\n')
signs = json.load(open(SRC + 'signs_all.json'))
edges45 = json.load(open(SRC + 'edges.json'))['edges']
v5loops = json.load(open(SRC + 'v5loops.json'))


def canon(t):
    t = re.sub(r'◇.*$', '', t)
    t = re.sub(r'◆.*$', '', t)
    t = re.sub(r'^★\d+\s*', '', t).strip()
    return t.upper()


# ---------- zones ----------
ZONES = {
    1: ("Local pandals and belonging", "Residents take part, meet neighbours and grow attached; small pandals multiply because each makes the next easier, until street space and enforcement hold them down."),
    2: ("Space and the site", "Sites that worked are carried over, layouts are reused and a visible main-road spot pulls crowds, so the site locks in its own closures. Enforcement and overloaded authorities decide how much road the festival keeps."),
    3: ("Crowds, closures and emergency access", "Barricades clear the site and compact the crowd, volunteers and hired security stand in for signs and get tired, crowd risk calls for more barricades, and congestion slows ambulances."),
    4: ("Traffic, detours and transport", "Diversions push jams onto side roads and bus routes; drivers, autos and visitors steer around them with advisories, until everyone takes the same detour."),
    5: ("Shops, vendors and street trade", "Footfall brings income to shops facing the crowd and to seasonal vendors, while hawkers are moved on and shops behind the barricades lose customers."),
    6: ("The festival engine: patrons, media and procession", "A bigger festival is more visible, draws visitors, coverage and donations, raises expectations and funds the next one. Rivalry and patronage push it bigger; the procession grows on prestige until one day of police capacity caps it."),
    7: ("Residents who absorb it", "Most disruption is absorbed privately and never reaches planners. Familiarity lowers how much it is felt, and only visible pushback changes arrangements."),
    8: ("Permissions and coordination", "Permissions run through the chowki and the single window, clashes push joint plans, but agencies still plan one stage at a time and permission load thins enforcement."),
    9: ("Immersion, rituals, waste and the river", "Court and NGT rules brought tanks and eco idols, which moved community tasks to PMC until its load pushes some back. Waste and nirmalya bring rules, bins and clean-up."),
    10: ("Police and borrowed capacity", "Police go where crowds have been, borrowed staff stretch routine services until they are pulled back, and dedicated capacity is never built."),
    11: ("After the festival: clean-up and learning", "The festival ends before the system does: teardown slips past the three-day rule, and lessons change plans only if problems are seen and recorded."),
    12: ("Noise, complaints and the rules", "Programmes, DJs and rehearsals make noise near homes; past what residents tolerate, goodwill drains into complaints, public pressure and court orders that push back, a season late."),
}

# ---------- nodes from v4 ----------
nodes = {}
zone = None
for line in v4:
    m = re.match(r'^## Z(\d+)', line)
    if m:
        zone = int(m.group(1))
        continue
    if line.startswith('[841') or line.startswith('[844') or line.startswith('T:'):
        if line.startswith('T: SYSTEM MAP'):
            zone = None
        continue
    m = re.match(r'^\s+\[(\d+:\d+)\] (.*)$', line)
    if m and zone:
        raw = m.group(2)
        c = canon(raw)
        star = re.match(r'^★(\d+)', raw)
        nodes[c] = dict(label=c, zone=zone, star=int(star.group(1)) if star else None)

for a, b, _ in edges45:
    for n in (a, b):
        assert n in nodes, n

# v5 split noise into its own zone (12); use v5's home zone for every box it drew
_v5 = json.load(open(SRC + 'v5.json'))
for n in _v5['nodes'].values():
    if '◇' not in n['text']:
        c = canon(n['text'])
        if c in nodes:
            nodes[c]['zone'] = n['zone']
nodes["GOAL: 55 DB BY DAY, 45 DB AT NIGHT (NOISE RULES)"]['zone'] = 12


def kind_of(c):
    if c.startswith('GOAL:'):
        return 'goal'
    if c.startswith('CAPACITY:'):
        return 'capacity'
    if c.startswith('MENTAL MODEL:'):
        return 'mental'
    return 'var'


OUTSIDE = {
    "STATE FESTIVAL GRANTS (2025), PATRONS AND ELECTION SEASON",
    "IDOLS INSTALLED IN HOMES AND MANDALS (10 TO 12 LAKH IMMERSIONS)",
    "STAFF TURNOVER IN POLICE AND MANDALS",
    "FAMILIARITY: YEARS THE FESTIVAL HAS RUN HERE",
    "RESPONSIBILITY SPLIT ACROSS AGENCIES",
    "ACCESS AND TRAFFIC NEEDS IN THE THEME DECISION (#17)",
    "DESIGNATED SPOTS FOR DISPLACED HAWKERS (NONE YET)",
}
for c, n in nodes.items():
    n['kind'] = 'outside' if c in OUTSIDE else kind_of(c)

# zone 13 and re-homed boxes
nodes["COURT, NGT AND MPCB RULES"]['zone'] = 12
nodes["STATE FESTIVAL GRANTS (2025), PATRONS AND ELECTION SEASON"]['zone'] = 6
# Familiarity box lives with the residents it softens
nodes["FAMILIARITY: YEARS THE FESTIVAL HAS RUN HERE"]['zone'] = 7

# v2 (Deep) variables that v4/v5 dropped
V2NEW = {
    "POLITICAL PATRONAGE": (6, 'var'),
    "MANDAL RIVALRY": (6, 'var'),
    "MEDIA AND SOCIAL MEDIA COVERAGE": (6, 'var'),
    "PUBLIC AND POLITICAL PRESSURE": (12, 'var'),
    "VIP VISITS ON PEAK EVENINGS": (10, 'outside'),
    "PERMISSION LOAD ACROSS AUTHORITIES": (8, 'var'),
    "HIRED CREWS AND PRIVATE SECURITY": (3, 'var'),
    "CROWD SAFETY RISK": (3, 'var'),
    "VOLUNTEER FATIGUE": (3, 'var'),
    "CROWD MANAGEMENT ON THE GROUND": (3, 'var'),
    "VOLUNTEERS MOBILISED": (1, 'var'),
    "BUSES REROUTED, STOPS SHIFTED": (4, 'var'),
    "AUTOS AND CABS CIRCLING": (4, 'var'),
    "SEASONAL VENDORS ON THE STREET": (5, 'var'),
    "SEASONAL VENDOR INCOME": (5, 'var'),
    "CUSTOMER ACCESS TO SHOPS": (5, 'var'),
    "ESTABLISHED SHOP REVENUE": (5, 'var'),
    "AMPLIFIED SOUND AND DJ USE": (12, 'var'),
    "RESIDENT TOLERANCE AND GOODWILL": (12, 'var'),
    "TOILETS, WATER AND BINS PROVIDED": (9, 'var'),
    "USABLE OPEN GROUND NEARBY": (2, 'outside'),
}
for c, (z, k) in V2NEW.items():
    nodes[c] = dict(label=c, zone=z, star=None, kind=k, v2=True)

# display renames for boxes that now carry a merged v2 meaning
RENAME = {
    "COURT, NGT AND MPCB RULES": "RULES AND COURT ORDERS (COURTS, NGT, MPCB, NOISE LIMITS)",
    "RIVER POLLUTION (MULA-MUTHA)": "WASTE, NIRMALYA AND RIVER POLLUTION (MULA-MUTHA)",
    "DONATIONS AND SPONSORSHIP": "DONATIONS, VARGANI AND SPONSORSHIP",
    "ENFORCEMENT OF ROAD AND FOOTPATH RULES": "ENFORCEMENT ON THE GROUND (ROAD, FOOTPATH, SOUND)",
    "VISITOR FOOTFALL AT THE SITE": "VISITOR FOOTFALL AND CROWD ON THE STREET",
    "ATTACHMENT TO THE NEIGHBOURHOOD'S FESTIVAL": "ATTACHMENT, BELONGING AND CULTURAL PRIDE",
    "DISMANTLING AND CLEAN-UP CREWS AT WORK": "DISMANTLING AND CLEAN-UP CREWS AT WORK",
}

# families (v4 outline colours): festival / street / everyday / planning
FAM_BY_ZONE = {1: 'festival', 2: 'street', 3: 'street', 4: 'street', 5: 'everyday', 6: 'festival',
               7: 'everyday', 8: 'planning', 9: 'planning', 10: 'planning', 11: 'planning', 12: 'everyday'}
FAM_OVERRIDE = {
    "STREET SPACE TAKEN BY THE FESTIVAL": 'festival', "SITE CARRY-OVER AND PERMISSION PRECEDENT (2019 TO 2026)": 'festival',
    "PANDAL LAYOUT PLANNED FOR THE SITE": 'festival', "SAME LAYOUT REUSED EACH YEAR": 'festival',
    "PANDAL PLACED ON A MAIN ROAD": 'festival', "MANDAL VALUING THE VISIBLE SPOT": 'festival',
    "ENFORCEMENT OF ROAD AND FOOTPATH RULES": 'planning', "POLICE BARRICADES AND DIVERSIONS": 'planning',
    "ADVISORIES ISSUED BY TRAFFIC POLICE": 'planning', "POLICE PULLED TO NEW HOTSPOTS": 'planning',
    "PROTECTED EMERGENCY CORRIDORS": 'planning', "IDOLS IMMERSED IN THE RIVER": 'festival',
    "ECO IDOLS, TANKS": 'festival', "RESIDENTS' OWN ROLE AND KNOW-HOW": 'everyday', "COMMUNITY KNOW-HOW": 'everyday',
    "TEMPORARY DECOR, SOUND AND LIGHT CREWS HIRED": 'festival', "WORKERS SPECIALISING IN FESTIVAL WORK": 'festival',
    "MORE ELABORATE SETUPS POSSIBLE": 'festival', "PROGRAMMES AND THEMED DISPLAYS": 'festival',
    "AMPLIFIED SOUND AND DJ USE": 'festival', "MANDAL RIVALRY": 'festival', "POLITICAL PATRONAGE": 'festival',
    "MEDIA AND SOCIAL MEDIA COVERAGE": 'everyday', "PUBLIC AND POLITICAL PRESSURE": 'everyday',
    "HIRED CREWS AND PRIVATE SECURITY": 'festival', "VOLUNTEERS MOBILISED": 'festival', "VOLUNTEER FATIGUE": 'festival',
    "CROWD GUIDANCE BY VOLUNTEERS": 'festival', "VOLUNTEERS ACTING AS THE SIGNAGE": 'festival',
    "SHOPS FACING THE CROWD BACKING THE FESTIVAL": 'everyday', "DISPLACEMENT OF HAWKERS": 'street',
    "HAWKERS SETTING UP AT THE CROWD'S EDGE": 'street', "SEASONAL VENDORS ON THE STREET": 'street',
    "VISITOR FOOTFALL AT THE SITE": 'festival', "TRIPS TO THE BIG CENTRAL MANDALS": 'festival',
    "LOAD ON CIVIC SERVICES (WASTE, TRAFFIC, POLICE)": 'planning', "NOISE NEAR HOMES": 'everyday',
    "POLICE CHECKS ON SPEAKERS AND TIMINGS": 'planning', "ORGANISED COMPLAINTS (RESIDENTS' GROUPS, POLICE, PMC)": 'everyday',
    "CLEAN-UP AND DISMANTLING BACKLOG": 'street', "GAP TO A RESTORED STREET": 'street',
    "DISMANTLING AND CLEAN-UP CREWS AT WORK": 'planning', "WORK PUSHED LATER, INCLUDING DISMANTLING": 'festival',
    "CREWS BOOKED BEYOND THOSE AVAILABLE": 'festival', "RIVER POLLUTION (MULA-MUTHA)": 'everyday',
    "CROWD SAFETY RISK": 'street', "CROWD MANAGEMENT ON THE GROUND": 'street',
}

# ---------- edges ----------
def sign_lookup(a, b):
    labs = signs.get(f'{a}|||{b}')
    if not labs:
        return None
    lab = labs[0][1]
    return lab


def parse_label(lab):
    if lab is None:
        return dict(sign='', ev='', src='', delay=False)
    delay = '‖' in lab
    lab = lab.replace('‖', '').strip()
    m = re.match(r'^([+−?])\s*([EH?])?\s*(?:·\s*(.*))?$', lab)
    if not m:
        return dict(sign='?', ev='?', src=lab, delay=delay)
    s, ev, src = m.group(1), m.group(2) or '', (m.group(3) or '').strip()
    if s == '?':
        s, ev = '+', '?'
    return dict(sign=s, ev=ev, src=src, delay=delay)


E = {}


def add_edge(a, b, lab, origin):
    if a == b:
        return
    assert a in nodes, a
    assert b in nodes, b
    k = (a, b)
    d = parse_label(lab)
    d['from'] = sorted(set(E.get(k, {}).get('from', [])) | set(origin))
    if k in E and E[k].get('sign'):
        E[k]['from'] = d['from']
        return
    E[k] = d


MANUAL = {
    ("STAFF TURNOVER IN POLICE AND MANDALS", "LESSONS CARRIED INTO NEXT YEAR"): '− ?',
    ("GAP TO A SMOOTHER FESTIVAL EACH YEAR", "LESSONS CARRIED INTO NEXT YEAR"): '+ ?',
    ("CAPACITY: MANDAL VOLUNTEERS AVAILABLE (#13)", "VOLUNTEER WORKLOAD AT JUNCTIONS"): '− H',
    ("CAPACITY: PMC WORKERS AND SITES (3,970 WORKERS, 241 COLLECTION CENTRES)", "LOAD ON CIVIC SERVICES (WASTE, TRAFFIC, POLICE)"): '− E · PMC',
    ("CAPACITY: ONE DAY OF SECURITY AND TRAFFIC (POLICE)", "GAP BEYOND ONE DAY OF SECURITY AND TRAFFIC CAPACITY"): '− E · News',
}
for a, b, src in edges45:
    lab = sign_lookup(a, b) or MANUAL.get((a, b))
    add_edge(a, b, lab, src)

# v2 edges (mapped through the alias table in signs2.py -> signs_all)
v2edges = []
for k, labs in signs.items():
    for sid, lab in labs:
        if sid == '664:7900':
            a, b = k.split('|||')
            v2edges.append((a, b, lab))
SKIP_V2 = {("LENGTH AND DURATION OF THE PROCESSION", "RIVER POLLUTION (MULA-MUTHA)")}
for a, b, lab in v2edges:
    if (a, b) in SKIP_V2 or a == b:
        continue
    if a not in nodes or b not in nodes:
        print('v2 edge skipped (unknown node):', a, '->', b)
        continue
    add_edge(a, b, lab, ['v2'])
# v2 goal arrows have no sign in the data
for a, b, lab in [("GOAL: TRAFFIC KEEPS MOVING (POLICE)", "POLICE BARRICADES AND DIVERSIONS", None),
                  ("IDOLS IMMERSED IN THE RIVER", "RIVER POLLUTION (MULA-MUTHA)", None)]:
    if (a, b) not in E:
        add_edge(a, b, lab, ['v2'])

# links added so the v2 loops close through three or more boxes
NEWLINKS = [
    ("POLITICAL PATRONAGE", "DONATIONS AND SPONSORSHIP", '+ H'),
    ("VISITOR FOOTFALL AT THE SITE", "SEASONAL VENDOR INCOME", '+ H'),
    ("CROWD CHANNELLED INTO BARRICADED LANES", "CROWD SAFETY RISK", '− H'),
    ("RESIDENTS TAKING PART IN LOCAL CELEBRATIONS", "FESTIVAL SCALE AND SPECTACLE", '+ H'),
    ("FESTIVAL SCALE AND SPECTACLE", "ATTACHMENT TO THE NEIGHBOURHOOD'S FESTIVAL", '+ H'),
]
for a, b, lab in NEWLINKS:
    add_edge(a, b, lab, ['merge'])

# black (driver) arrows from yellow boxes carry no loop sign
for (a, b), d in E.items():
    if nodes[a]['kind'] in ('goal', 'capacity', 'mental', 'outside') and not d['sign']:
        d['sign'] = '+'
        d['ev'] = d['ev'] or ''
    d['driver'] = nodes[a]['kind'] in ('goal', 'capacity', 'mental', 'outside')

missing = [k for k, d in E.items() if not d['sign']]
assert not missing, missing

# ---------- loop descriptions from v4 ----------
def block_after(title):
    for i, l in enumerate(v4):
        if l.startswith('T: ' + title):
            return v4[i + 1][3:]
    raise KeyError(title)


loops_text = block_after('THE 63 LOOPS BY ZONE')
desc = {}
for m in re.finditer(r'((?:[RB]\d+)(?: · [RB]\d+)*) ([^():]+?) \(([^)]*)\): (.*?)(?=(?: \d+ [A-Z][A-Z ,:\-]+ )?(?:[RB]\d+(?: · [RB]\d+)* [A-Z][^():]+? \([^)]*\):)|$)', loops_text):
    codes = m.group(1).split(' · ')
    for c in codes:
        desc[c] = dict(title=m.group(2).strip(), refs=m.group(3).strip(), text=m.group(4).strip())

# ---------- loops ----------
def slug(c):
    return re.sub(r'[^a-z0-9]+', '-', c.lower()).strip('-')[:48]


loops = []
for name, l in v5loops.items():
    code = name.split()[0]
    nm = re.sub(r'\s*(#\d+.*|Raheja.*|\?)$', '', name[len(code) + 1:]).strip()
    refs = re.findall(r'#\d+', name)
    ns = [canon(n) for n in l['nodes']]
    # rotate so the loop starts at a box in its home zone
    loops.append(dict(id=code, type=code[0], name=nm, zone=l['zone'], nodes=ns, refs=refs,
                      unknown='?' in name, src='v5'))

V2LOOPS = [
    ('R30', 'Prestige escalation', 6, ["MANDAL RIVALRY", "FESTIVAL SCALE AND SPECTACLE", "MEDIA AND SOCIAL MEDIA COVERAGE", "DONATIONS AND SPONSORSHIP"],
     'Rivalry between mandals pushes scale; scale draws media and social-media coverage; coverage brings money; money feeds rivalry. (v2 R1)'),
    ('R31', 'Attention magnet', 6, ["FESTIVAL SCALE AND SPECTACLE", "MEDIA AND SOCIAL MEDIA COVERAGE", "VISITOR FOOTFALL AT THE SITE"],
     'Scale makes coverage, coverage pulls people onto the street, and the crowd itself becomes part of the spectacle (‖ next year). (v2 R2)'),
    ('R32', 'Belonging and pride', 1, ["RESIDENTS TAKING PART IN LOCAL CELEBRATIONS", "FESTIVAL SCALE AND SPECTACLE", "ATTACHMENT TO THE NEIGHBOURHOOD'S FESTIVAL"],
     'Households taking part make the celebration bigger, a bigger celebration deepens belonging and pride, and pride brings more households in. (v2 R3)'),
    ('R33', 'Patronage', 6, ["POLITICAL PATRONAGE", "DONATIONS AND SPONSORSHIP", "MANDAL RIVALRY"],
     'Politicians back mandals with money and favours, money sharpens rivalry, and rival mandals are worth courting, especially in election season. (v2 R4, closed through donations)'),
    ('R34', 'Festival marketplace', 5, ["VISITOR FOOTFALL AT THE SITE", "SEASONAL VENDOR INCOME", "SEASONAL VENDORS ON THE STREET"],
     'Crowds make seasonal selling pay, income brings more vendors back (‖ next season), and stalls add to the crowd and the street life. (v2 R5)'),
    ('R35', 'Transport squeeze', 4, ["CONGESTION ON SURROUNDING ROUTES", "BUSES REROUTED, STOPS SHIFTED", "AUTOS AND CABS CIRCLING"],
     'Congestion reroutes buses and shifts stops, riders turn to autos and cabs that circle looking for a way through, adding to the congestion. (v2 R8)'),
    ('R36', 'Overloaded enforcement', 2, ["FESTIVAL SCALE AND SPECTACLE", "PERMISSION LOAD ACROSS AUTHORITIES", "ENFORCEMENT OF ROAD AND FOOTPATH RULES", "STREET SPACE TAKEN BY THE FESTIVAL", "SITE CARRY-OVER AND PERMISSION PRECEDENT (2019 TO 2026)"],
     'Found when merging v2 into v5: a bigger festival means more permissions across authorities, which thins enforcement, so more road is taken, carried over and grown into. Every link is already on the board.'),
    ('B35', 'Noise restriction', 12, ["AMPLIFIED SOUND AND DJ USE", "NOISE NEAR HOMES", "GAP BEYOND WHAT THEY TOLERATE", "ORGANISED COMPLAINTS (RESIDENTS' GROUPS, POLICE, PMC)", "COURT, NGT AND MPCB RULES"],
     'DJs and amplified sound raise noise near homes; past tolerance it becomes organised complaints, complaints become rules and court orders (‖ a season later), and rules curb amplified sound. (v2 B2)'),
    ('B36', 'Tolerance depletion', 12, ["FESTIVAL SCALE AND SPECTACLE", "STREET SPACE TAKEN BY THE FESTIVAL", "EVERYDAY ACCESS (HOMES, SHOPS, DELIVERIES)", "DISRUPTION FELT BY NON-PARTICIPANTS", "RESIDENT TOLERANCE AND GOODWILL", "ORGANISED COMPLAINTS (RESIDENTS' GROUPS, POLICE, PMC)", "COURT, NGT AND MPCB RULES"],
     'Scale takes road, road taken cuts access, lost access is felt, felt disruption drains goodwill, low goodwill turns into complaints, complaints into rules, and rules cap scale (‖). (v2 B3)'),
    ('B37', 'Access and revenue', 5, ["FESTIVAL SCALE AND SPECTACLE", "STREET SPACE TAKEN BY THE FESTIVAL", "CUSTOMER ACCESS TO SHOPS", "ESTABLISHED SHOP REVENUE", "DONATIONS AND SPONSORSHIP"],
     'Road taken cuts customer access to established shops, revenue falls, and shops give less to the mandal next year (‖). (v2 B4)'),
    ('B38', 'Volunteer capacity', 3, ["FESTIVAL SCALE AND SPECTACLE", "VISITOR FOOTFALL AT THE SITE", "VOLUNTEER FATIGUE", "CROWD MANAGEMENT ON THE GROUND", "ORGANISED COMPLAINTS (RESIDENTS' GROUPS, POLICE, PMC)", "COURT, NGT AND MPCB RULES"],
     'Bigger crowds tire volunteers, crowd management slips, complaints rise, and rules eventually cap scale. (v2 B5)'),
    ('B39', 'Media backlash', 12, ["FESTIVAL SCALE AND SPECTACLE", "MEDIA AND SOCIAL MEDIA COVERAGE", "PUBLIC AND POLITICAL PRESSURE", "COURT, NGT AND MPCB RULES"],
     'The same coverage that grows the festival also carries its harms; public and political pressure becomes rules that cap scale (‖). (v2 B6)'),
    ('B40', 'Waste brings bins', 9, ["RIVER POLLUTION (MULA-MUTHA)", "COURT, NGT AND MPCB RULES", "ENFORCEMENT OF ROAD AND FOOTPATH RULES", "TOILETS, WATER AND BINS PROVIDED"],
     'Waste, nirmalya and river pollution bring rules (‖), rules are enforced on the ground, enforcement brings toilets, water and bins, and those cut waste. (v2 B11 and links)'),
    ('B41', 'Safety response', 3, ["CROWD SAFETY RISK", "POLICE BARRICADES AND DIVERSIONS", "CROWD CHANNELLED INTO BARRICADED LANES"],
     'Crowd safety risk brings barricades, barricades channel the crowd into lanes, and channelled crowds lower the risk. (v2 B12)'),
]
for code, nm, z, ns, d in V2LOOPS:
    loops.append(dict(id=code, type=code[0], name=nm, zone=z, nodes=ns, refs=[], unknown=False, src='v2', text=d))

# attach v4 descriptions
for l in loops:
    if l['src'] == 'v5':
        d = desc.get(l['id'])
        l['text'] = d['text'] if d else ''
        l['group'] = d['title'] if d else ''
        l['refs_full'] = d['refs'] if d else ''

# parity check
for l in loops:
    ns = l['nodes']
    neg = 0
    for i in range(len(ns)):
        k = (ns[i], ns[(i + 1) % len(ns)])
        assert k in E, (l['id'], k)
        if E[k]['sign'] == '−':
            neg += 1
    t = 'R' if neg % 2 == 0 else 'B'
    assert t == l['type'], (l['id'], neg)

# ---------- emit ----------
ids = {c: slug(c) for c in nodes}
assert len(set(ids.values())) == len(ids)
out_nodes = []
for c, n in nodes.items():
    out_nodes.append(dict(id=ids[c], label=RENAME.get(c, c), zone=n['zone'], kind=n['kind'], star=n['star'],
                          fam=FAM_OVERRIDE.get(c, FAM_BY_ZONE[n['zone']]), v2=n.get('v2', False)))
out_edges = []
for (a, b), d in E.items():
    out_edges.append(dict(s=ids[a], t=ids[b], sign=d['sign'], ev=d['ev'], src=d['src'], delay=d['delay'],
                          driver=d['driver'], origin=d['from']))
for l in loops:
    l['nodes'] = [ids[c] for c in l['nodes']]

texts = {k: block_after(k) for k in ['THE SYSTEM IN SENTENCES', 'HOW THE LOOPS MERGE', 'MENTAL MODELS HOLDING',
                                     'ARCHETYPES WE THINK WE SEE', 'WHERE TO ACT', "WHAT WE STILL DON'T KNOW"]}
json.dump(dict(zones={k: dict(name=v[0], blurb=v[1]) for k, v in ZONES.items()}, nodes=out_nodes,
               edges=out_edges, loops=loops, texts=texts), open(SP + 'model.json', 'w'), ensure_ascii=False, indent=1)
from collections import Counter
print('nodes', len(out_nodes), 'edges', len(out_edges), 'loops', len(loops))
print('per zone', sorted(Counter(n['zone'] for n in out_nodes).items()))
print('missing desc', [l['id'] for l in loops if not l.get('text')])
