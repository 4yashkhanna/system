import xml.etree.ElementTree as ET, html, re, json, networkx as nx
r=ET.fromstring(open(__import__('sys').argv[1] if len(__import__('sys').argv) > 1 else 'source/figjam_dump.xml').read())
MISSING=[1,2,4,5,6,8,10,11,12,18,22,25,27,31,34,36,42,44,45,46,47,49,50,51,52,54,58,64,66,67,68,70,72,75]
def T(e): return html.unescape(' '.join((e.text or '').split()))
secs={}
for c in r:
    if c.tag=='section':
        m=re.match(r'^#(\d+) (.*)$',html.unescape(c.get('name') or ''))
        if m: secs[int(m.group(1))]=(m.group(2),c)
out={}
for n in MISSING:
    title,s=secs[n]
    txt={}; 
    for e in s.iter():
        if e.tag=='shape-with-text': txt[e.get('id')]=T(e)
    edges=[]
    for c in s.iter('connector'):
        a,b=c.get('connectorStart'),c.get('connectorEnd')
        if a in txt and b in txt: edges.append((txt[a],txt[b],T(c)))
    G=nx.DiGraph()
    for a,b,l in edges:
        if a.isupper() and b.isupper(): G.add_edge(a,b,lab=l)
    loops=[]
    for cyc in nx.simple_cycles(G):
        neg=sum(1 for i in range(len(cyc)) if G[cyc[i]][cyc[(i+1)%len(cyc)]]['lab'].startswith('−'))
        loops.append(dict(type='R' if neg%2==0 else 'B',nodes=cyc))
    texts=[T(e) or html.unescape(e.get('name','')) for e in s.iter('text')]
    ev=[texts[i+1] for i,t in enumerate(texts) if t in('EVENT','PATTERN','HYPOTHESIS') and i+1<len(texts)]
    alone={k: next((t.split(':',1)[1].strip() for t in texts if t.startswith(k+' loop alone:')), '') for k in 'RB'}
    note=next((t for t in texts if t.startswith(('R and B share','Balancing loop only','Reinforcing loop only'))), '')
    evid=next((t for t in texts if t.startswith('Arrow tags:')), '')
    out[n]=dict(title=title,boxes=[t for t in txt.values()],edges=edges,loops=loops,epH=ev,alone=alone,note=note,evidence=evid)
json.dump(out,open('source/loops34.json','w'),indent=1,ensure_ascii=False)
for n,d in out.items():
    print(f"#{n} {d['title']}")
    for l in d['loops']: print('   ',l['type'],' → '.join(l['nodes']))
    ext=[b for b in d['boxes'] if not b.isupper()]
    print('    yellow:', ' | '.join(ext))
