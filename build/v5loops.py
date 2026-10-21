import json, networkx as nx, math, re
d=json.load(open('source/v5.json')); N=d['nodes']
def pip(x,y,poly):
    ins=False
    for i in range(len(poly)):
        x1,y1=poly[i]; x2,y2=poly[(i+1)%len(poly)]
        if (y1>y)!=(y2>y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: ins=not ins
    return ins
out={}
for z in range(1,13):
    G=nx.DiGraph()
    for a,b,zz in d['edges']:
        if zz==z and a in N and b in N: G.add_edge(a,b)
    cyc=list(nx.simple_cycles(G))
    for L in [l for l in d['labels'] if l['zone']==z]:
        best=None
        for c in cyc:
            poly=[(N[n]['x'],N[n]['y']) for n in c]
            cx=sum(p[0] for p in poly)/len(poly); cy=sum(p[1] for p in poly)/len(poly)
            inside=pip(L['x'],L['y'],poly)
            dist=math.hypot(cx-L['x'],cy-L['y'])
            score=(0 if inside else 1, dist)
            if best is None or score<best[0]: best=(score,c)
        c=best[1]
        out[L['text']]=dict(zone=z,score=best[0],nodes=[N[n]['text'] for n in c],ids=c)
        print(f"Z{z} {L['text']}  inside={best[0][0]==0} d={best[0][1]:.0f}")
        for n in c: print('    ',N[n]['text'])
json.dump(out,open('source/v5loops.json','w'),indent=1)
