import xml.etree.ElementTree as ET, sys, html
r=ET.fromstring(open(sys.argv[1]).read())
target=sys.argv[2]
def find(e):
    if e.get('id')==target: return e
    for c in e:
        x=find(c)
        if x is not None: return x
sec=find(r)
txt={}
def t(e): return html.unescape(' '.join((e.text or '').split()))
def walk(e,depth,path):
    for c in e:
        tag=c.tag
        if tag in('shape-with-text','sticky','text'):
            txt[c.get('id')]=t(c) or c.get('name','')
    for c in e:
        if c.tag=='section':
            print('  '*depth+'## '+html.unescape(c.get('name')))
            walk(c,depth+1,path)
        elif c.tag in('shape-with-text','sticky'):
            print('  '*depth+f"[{c.get('id')}] {t(c)}")
        elif c.tag=='text':
            print('  '*depth+f"T: {t(c) or html.unescape(c.get('name',''))}")
        elif c.tag=='connector':
            pass
        elif c.tag in ('frame','table','rounded-rectangle','ellipse'):
            print('  '*depth+f"<{c.tag} {c.get('name')}>")
            walk(c,depth+1,path)
walk(sec,0,[])
print('---CONNECTORS')
def conns(e):
    for c in e.iter('connector'):
        a,b=c.get('connectorStart'),c.get('connectorEnd')
        print(f"{txt.get(a,a)[:60]} -> {txt.get(b,b)[:60]} | {t(c)} | caps {c.get('connectorStartCap')}/{c.get('connectorEndCap')}")
conns(sec)
