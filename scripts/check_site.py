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
for file,seconds in [('neighbors.mp4',229),('one-graph.mp4',87)]:
 b=(SITE/'media'/file).read_bytes();assert b'ftyp' in b[:40] and len(b)>1000000,file
 assert 0<b.find(b'moov')<b.find(b'mdat'),file+' is not faststart'
 vtt=(SITE/'media'/file.replace('.mp4','.zh.vtt')).read_text();assert vtt.startswith('WEBVTT')
 assert '-->' in vtt
assert sum(s['duration'] for s in json.loads((ROOT/'video/storyboard.json').read_text()))==229
notes=json.loads((SITE/'downloads/notes.json').read_text());assert len(notes)==16
assert len(list((SITE/'slides').glob('slide-*.png')))==16
with zipfile.ZipFile(SITE/'downloads/label-propagation.pptx') as z:
 assert len([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)])==16
 assert len([n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',n)])==16
for f in ['learn.md','sources.md','exercises.md','transcript.md','label-propagation.pdf','golden.json','label_propagation.py']:
 assert (SITE/'downloads'/f).stat().st_size>20,f
assert (SITE/'downloads/label-propagation.pdf').read_bytes().startswith(b'%PDF')
for path in SITE.rglob('*'):
 if path.is_file() and path.suffix in ['.html','.js','.css','.json','.md']:
  s=path.read_text(encoding='utf-8');assert '/Users/' not in s,path
  if path.suffix in ['.js','.html']:assert 'localhost:8785' not in s,path
print('PASS: HTML paths, anchors, module imports, faststart media, 16 slides and notes, downloads and public path hygiene.')
