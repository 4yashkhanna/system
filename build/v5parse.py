import sys
import xml.etree.ElementTree as ET, html, json, re, math, itertools
r=ET.fromstring(open(sys.argv[1] if len(sys.argv) > 1 else 'source/figjam_dump.xml').read())
def find(e,t):
    if e.get('id')==t: return e
    for c in e:
        x=find(c,t)
        if x is not None: return x
v5=find(r,'854:12411')
def T(e): return html.unescape(' '.join((e.text or '').split()))
nodes={}; labels=[]; edges=[]
for z in v5:
    if z.tag!='section': continue
    zname=html.unescape(z.get('name')); zx,zy=float(z.get('x')),float(z.get('y'))
    zid=int(zname.split()[0][1:])
    for c in z:
        if c.tag=='shape-with-text':
            x=float(c.get('x'))+float(c.get('width'))/2; y=float(c.get('y'))+float(c.get('height'))/2
            t=T(c)
            if re.match(r'^[RB]\d+ ',t) and float(c.get('width'))<300:
                labels.append(dict(id=c.get('id'),zone=zid,text=t,x=x,y=y))
            else:
                nodes[c.get('id')]=dict(id=c.get('id'),zone=zid,text=t,x=x,y=y,w=float(c.get('width')))
        if c.tag=='connector':
            edges.append((c.get('connectorStart'),c.get('connectorEnd'),zid))
json.dump(dict(nodes=nodes,labels=labels,edges=edges),open('source/v5.json','w'),indent=0)
print(len(nodes),len(labels),len(edges))
print(set(n['w'] for n in nodes.values()))
