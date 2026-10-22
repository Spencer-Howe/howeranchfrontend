import sys, os, re, json, html
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.title=''; self.desc=''; self.robots=''; self.heads=[]; self.text=[]; self.links=set()
        self.imgs=0; self.forms=0; self.inputs=0; self.iframes=[]; self._t=None; self._skip=0
    def handle_starttag(self, tag, a):
        a=dict(a)
        if tag in ('script','style','noscript'): self._skip+=1
        if tag=='title': self._t='title'
        if tag=='meta' and a.get('name')=='description': self.desc=a.get('content','')
        if tag=='meta' and a.get('name')=='robots': self.robots=a.get('content','')
        if tag in ('h1','h2'): self._t=tag; self.heads.append([tag,''])
        if tag=='a' and a.get('href'): self.links.add(a['href'])
        if tag in ('img','wow-image'): self.imgs+=1
        if tag=='form': self.forms+=1
        if tag in ('input','textarea'): self.inputs+=1
        if tag=='iframe': self.iframes.append(a.get('src') or a.get('data-src') or a.get('title') or '?')
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript'): self._skip-=1
        if tag in ('title','h1','h2'): self._t=None
    def handle_data(self, d):
        if self._skip: return
        if self._t=='title': self.title+=d
        elif self._t in ('h1','h2') and self.heads: self.heads[-1][1]+=d
        if d.strip(): self.text.append(d.strip())

D=sys.argv[1]
rows=[]
for f in sorted(os.listdir(D)):
    raw=open(os.path.join(D,f),encoding='utf-8',errors='replace').read()
    p=P(); p.feed(raw)
    words=len(' '.join(p.text).split())
    ext=sorted({l for l in p.links if l.startswith('http') and 'thehoweranch.com' not in l.replace('www.','') or 'registration' in l})
    apps=sorted(set(re.findall(r'"appDefinitionName":"([^"]+)"', raw)) | set(re.findall(r'"(wix-[a-z-]*(?:bookings|forms|blog|stores|members|events|chat|pro-gallery)[a-z-]*)"', raw)))
    rows.append(dict(page=f[:-5], title=html.unescape(p.title.strip()), desc=p.desc[:110], noindex='noindex' in p.robots,
                     words=words, imgs=p.imgs, forms=p.forms, inputs=p.inputs,
                     h=[' '.join(t.split())[:60] for _,t in p.heads if t.strip()][:4],
                     ext=[l for l in ext][:8], iframes=p.iframes[:3], apps=apps[:8]))
json.dump(rows, open(sys.argv[2],'w'), indent=1)
for r in rows:
    print(f"{r['page']:<38} w={r['words']:<5} img={r['imgs']:<3} form={r['forms']}/{r['inputs']} {'NOINDEX ' if r['noindex'] else ''}| {r['title'][:55]}")
