#!/usr/bin/env python3
"""Static source/asset consistency checks; no network and no third-party dependencies."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re,json,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';missing=[]
class Check(HTMLParser):
 def __init__(self,path):super().__init__();self.path=path;self.links=[];self.ids=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'id' in d:self.ids.append(d['id'])
  for key in ['src','href','poster']:
   if key in d:self.links.append(d[key])
for path in SITE.glob('*.html'):
 c=Check(path);c.feed(path.read_text())
 assert len(c.ids)==len(set(c.ids)),f'duplicate ids in {path.name}'
 for link in c.links:
  url=urlsplit(link)
  if url.scheme or url.netloc:continue
  if url.path:
   target=(path.parent/unquote(url.path)).resolve()
   if not target.exists():missing.append((path.name,link))
  elif url.fragment and path.name=='index.html':assert url.fragment in c.ids,(path.name,link)
for path in SITE.glob('*.js'):
 for link in re.findall(r"(?:from\s*|import\s*)['\"]([^'\"]+)['\"]",path.read_text()):
  if link.startswith('.') and not (path.parent/urlsplit(link).path).exists():missing.append((path.name,link))
assert not missing,missing
for file in ['circles.mp4','one-graph.mp4']:
 b=(SITE/'media'/file).read_bytes();assert b'ftyp' in b[:40] and len(b)>1000000,file
 assert 0<b.find(b'moov')<b.find(b'mdat'),file+' is not faststart'
 for vtt in [file.replace('.mp4','.zh.vtt')]+(['circles.en.vtt'] if file=='circles.mp4' else []):
  t=(SITE/'media'/vtt).read_text();assert t.startswith('WEBVTT') and '-->' in t,vtt
assert sum(s['duration'] for s in json.loads((ROOT/'video/storyboard.json').read_text()))==229
plan=json.loads((ROOT/'video/storyboard-v4.json').read_text())
assert 379<plan['duration']<380 and len(plan['scenes'])==24
html=(SITE/'index.html').read_text()
for at in re.findall(r'data-seek(?:-film)?="([0-9.]+)"',html):assert float(at)<plan['duration'],at
chapters={round(c['start'],2) for c in json.loads((ROOT/'video/chapters-v4.json').read_text())}
for at in re.findall(r'data-seek="([0-9.]+)"',html):assert round(float(at),2) in chapters|{0.0},at
SLIDES=18
notes=json.loads((SITE/'downloads/notes.json').read_text());assert len(notes)==SLIDES
assert notes==json.loads((ROOT/'presentation/notes.json').read_text())
assert len(list((SITE/'slides').glob('slide-*.png')))==SLIDES
with zipfile.ZipFile(SITE/'downloads/label-propagation.pptx') as z:
 assert len([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)])==SLIDES
 assert len([n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',n)])==SLIDES
 deck=''.join(z.read(n).decode('utf-8') for n in z.namelist() if n.startswith('ppt/') and n.endswith('.xml'))
# Earlier film versions (邻居的颜色, 3:49, the library story) must not leak back into what visitors see.
STALE=['邻居的颜色','图书馆','3分49','3 分 49']
for w in STALE:assert w not in deck,('pptx',w)
for path in [*SITE.glob('*.html'),*SITE.glob('*.js'),*(SITE/'downloads').glob('*.md'),*(SITE/'downloads').glob('*.json'),ROOT/'README.md',*(ROOT/'docs').glob('*.md')]:
 t=path.read_text(encoding='utf-8')
 for w in STALE:assert w not in t,(str(path.relative_to(ROOT)),w)
for f in ['learn.md','sources.md','exercises.md','transcript.md','label-propagation.pdf','golden.json','label_propagation.py']:
 assert (SITE/'downloads'/f).stat().st_size>20,f
assert (SITE/'downloads/label-propagation.pdf').read_bytes().startswith(b'%PDF')
for path in SITE.rglob('*'):
 if path.is_file() and path.suffix in ['.html','.js','.css','.json','.md']:
  s=path.read_text(encoding='utf-8');assert '/Users/' not in s,path
  if path.suffix in ['.js','.html']:assert 'localhost:8785' not in s,path
print('PASS: HTML paths, anchors, module imports, faststart media, film v4 chapters, 18 slides and notes, no stale film-version text, downloads and public path hygiene.')
