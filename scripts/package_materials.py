#!/usr/bin/env python3
"""Package teaching downloads. PDF is a faithful image preview, PPTX is editable."""
from pathlib import Path
import shutil,json,subprocess,re
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'site/downloads'
pages=sorted((ROOT/'build/private/deck').glob('slide-*.png'))
assert len(pages)==16,'Generate and validate the editable deck first'
assert (dest/'label-propagation.pptx').exists()
c=canvas.Canvas(str(dest/'label-propagation.pdf'),pagesize=(960,540))
c.setTitle('Label propagation Lab05 - Su3037');c.setAuthor('Su3037')
for p in pages:
 c.drawImage(ImageReader(str(p)),0,0,width=960,height=540);c.showPage()
c.save()
for src,name in [('video/transcript.md','transcript.md'),('presentation/notes.json','notes.json'),('src/label_propagation.py','label_propagation.py'),('docs/research/sources.md','sources.md'),('docs/LEARN.md','learn.md')]:
 if (ROOT/src).exists():shutil.copyfile(ROOT/src,dest/name)
g=json.loads((ROOT/'data/traces.json').read_text())['graphs']['golden']
small={'nodes':g['nodes'],'edges':g['edges']}
for p in [ROOT/'data/golden.json',dest/'golden.json']:p.write_text(json.dumps(small,indent=2),encoding='utf-8')
module="import{QUESTIONS}from './site/questions.js';console.log(JSON.stringify(QUESTIONS));"
q=json.loads(subprocess.check_output(['node','--input-type=module','-e',module],cwd=ROOT,text=True))
lines=['# 标签传播练习与解析','', '建议先在网页尝试，再阅读答案。','']
for i,x in enumerate(q,1):
 lines.extend([f'## {i} {x["q"]}',''])
 lines.extend([f'- {chr(65+j)}. {a}' for j,a in enumerate(x['a'])])
 lines.extend(['',f'答案：{chr(65+x["correct"])}。{x["e"]}',''])
for p in [ROOT/'docs/EXERCISES.md',dest/'exercises.md']:p.write_text('\n'.join(lines),encoding='utf-8')
shutil.copyfile(ROOT/'build/private/film-stills/09-visit-c.jpg',ROOT/'site/media/one-graph.jpg')
vtt=['WEBVTT',''];t=0
def stamp(t):
 return f'{int(t)//3600:02}:{int(t)//60%60:02}:{int(t)%60:02}.{round(t%1*1000):03}'
for s in json.loads((ROOT/'video/storyboard.json').read_text()):
 for j,cap in enumerate(s['captions']):
  a=t+j*s['duration']/2;b=t+(j+1)*s['duration']/2
  if a>=53 and b<=140:vtt.extend([f'{stamp(a-53)} --> {stamp(b-53)}',cap,''])
 t+=s['duration']
(ROOT/'site/media/one-graph.zh.vtt').write_text('\n'.join(vtt),encoding='utf-8')
for source,name in [('LICENSE','LICENSE.txt'),('LICENSE-CONTENT.md','LICENSE-CONTENT.md'),('THIRD_PARTY_NOTICES.md','THIRD_PARTY_NOTICES.md')]:shutil.copyfile(ROOT/source,dest/name)
print('Packaged PDF preview, notes, transcript, 8 exercises and reference implementation')
