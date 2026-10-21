import sys
import xml.etree.ElementTree as ET, html, json, re
r=ET.fromstring(open(sys.argv[1] if len(sys.argv) > 1 else 'source/figjam_dump.xml').read())
def find(e,t):
    if e.get('id')==t: return e
    for c in e:
        x=find(c,t)
        if x is not None: return x
def T(e): return html.unescape(' '.join((e.text or '').split()))
def canon(t):
    t=re.sub(r'◇.*$','',t); t=re.sub(r'◆.*$','',t)
    t=re.sub(r'^★\d+\s*','',t).strip()
    return t.upper()
def extract(sid):
    s=find(r,sid); txt={}
    for e in s.iter():
        if e.tag in('shape-with-text','sticky'): txt[e.get('id')]=T(e)
    E=[]
    for c in s.iter('connector'):
        a,b=c.get('connectorStart'),c.get('connectorEnd')
        E.append((txt.get(a),txt.get(b),T(c)))
    return txt,E
sign={}
for sid in ['678:8364','818:9029','664:7900']:
    txt,E=extract(sid)
    for a,b,l in E:
        if a is None or b is None: continue
        m=re.search(r'([+−\-?])\s*(E|H|\?)?',re.sub(r'^\S+→\S+\s*','',l))
        lab=re.sub(r'^\S+→\S+\s*','',l)
        if lab and lab[0] in '+−-?':
            sign.setdefault((canon(a),canon(b)),[]).append((sid,lab))
json.dump({f'{a}|||{b}':v for (a,b),v in sign.items()},open('source/signs.json','w'),indent=0,ensure_ascii=False)
print(len(sign))
# full v4 graph
txt4,E4=extract('836:9863')
txt5,E5=extract('854:12411')
edges={}
for src,E in (('v4',E4),('v5',E5)):
    for a,b,l in E:
        if a is None or b is None: continue
        k=(canon(a),canon(b))
        edges.setdefault(k,set()).add(src)
miss=[k for k in edges if k not in sign]
print('edges',len(edges),'unsigned',len(miss))
for k in miss: print('  ',k[0],'->',k[1], edges[k])
nodes=set(); [nodes.update(k) for k in edges]
print('nodes',len(nodes))
json.dump(dict(edges=[[a,b,sorted(s)] for (a,b),s in edges.items()]),open('source/edges.json','w'),indent=0,ensure_ascii=False)
