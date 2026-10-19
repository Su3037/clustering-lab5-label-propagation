#!/usr/bin/env python3
"""Original deterministic motion graphics. Pillow + FFmpeg; no browser, cloud or paid API.
Use --preview for four stills and a 12s sample; default exports the complete 1080p film.
"""
import argparse, json, math, os, subprocess, time
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
SCENES=json.loads((ROOT/'video/storyboard.json').read_text())
DATA=json.loads((ROOT/'data/traces.json').read_text())
TOTAL=sum(s['duration'] for s in SCENES)
W,H,S=1920,1080,1.5
INK='#ede9dc';MUTED='#a5b5b3';GOLD='#dbbc7c';TEAL='#77c9b6';RED='#e08b85'
COLORS={'A':'#e3c179','B':'#7ac9b4','C':'#e4a166','D':'#8faee2','E':'#dba1bf'}
SANS=os.environ.get('CLUSTER_SANS_FONT','/System/Library/Fonts/STHeiti Medium.ttc')
SERIF=os.environ.get('CLUSTER_SERIF_FONT','/System/Library/Fonts/Supplemental/Songti.ttc')
if not Path(SERIF).exists():SERIF=SANS
if not Path(SANS).exists():
 SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
 SERIF='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
def smooth(x):return max(0,min(1,x))**2*(3-2*max(0,min(1,x)))
def rgb(c):return tuple(int(c[i:i+2],16) for i in (1,3,5))
def blend(a,b,t):return tuple(round(x+(y-x)*t) for x,y in zip(rgb(a),rgb(b)))
def pt(x,y):return (round(x*S),round(y*S))
@lru_cache(maxsize=80)
def font(size,serif=False):return ImageFont.truetype(SERIF if serif else SANS,round(size*S))
@lru_cache(maxsize=2500)
def text_sprite(text,size,color,serif):
 f=font(size,serif);bbox=f.getbbox(text);pad=3
 im=Image.new('RGBA',(max(1,bbox[2]-bbox[0]+pad*2),max(1,bbox[3]-bbox[1]+pad*2)),(0,0,0,0))
 ImageDraw.Draw(im).text((pad-bbox[0],pad-bbox[1]),text,font=f,fill=color)
 return im
def txt(im,text,x,y,size=24,color=INK,serif=False,center=False,alpha=1):
 sprite=text_sprite(str(text),size,color,serif)
 if alpha<1:
  sprite=sprite.copy();sprite.putalpha(sprite.getchannel('A').point(lambda a:int(a*max(0,alpha))))
 pos=pt(x,y)
 if center:pos=(pos[0]-sprite.width//2,pos[1])
 im.paste(sprite,pos,sprite)
def line(im,points,fill,width=2):ImageDraw.Draw(im).line([pt(*p) for p in points],fill=fill,width=max(1,round(width*S)))
def circle(im,x,y,r,fill,outline=None,width=2):ImageDraw.Draw(im).ellipse((*pt(x-r,y-r),*pt(x+r,y+r)),fill=fill,outline=outline,width=round(width*S))
def rect(im,xy,fill,outline=None,width=1,r=0):
 d=ImageDraw.Draw(im);box=(*pt(xy[0],xy[1]),*pt(xy[2],xy[3]))
 if r:d.rounded_rectangle(box,radius=round(r*S),fill=fill,outline=outline,width=round(width*S))
 else:d.rectangle(box,fill=fill,outline=outline,width=round(width*S))
def glow(im,x,y,r,color=GOLD):
 # Soft concentric rings avoid a full-frame blur per particle.
 for k in range(3,0,-1):circle(im,x,y,r+k*5,None,blend('#0b1b23',color,.08+(4-k)*.12),1.1)
 circle(im,x,y,r,color)
def pulse_edge(im,a,b,t,color=GOLD,width=2):
 line(im,[a,b],blend('#132c33',color,.4),width)
 for offset in [0,.5]:
  p=(t*.65+offset)%1;x=a[0]+(b[0]-a[0])*p;y=a[1]+(b[1]-a[1])*p
  glow(im,x,y,2.4,color)

@lru_cache(maxsize=1)
def backdrop():
 im=Image.new('RGB',(W,H));pix=im.load()
 # Paint at tiny resolution then upscale once.
 small=Image.new('RGB',(160,90));p=small.load()
 for y in range(90):
  for x in range(160):
   v=max(0,1-math.hypot((x-82)/120,(y-39)/85));p[x,y]=(round(6+v*6),round(14+v*13),round(21+v*14))
 im=small.resize((W,H),Image.Resampling.BICUBIC)
 d=ImageDraw.Draw(im)
 for i in range(85):
  x=(i*439+73)%W;y=(i*211+17)%H
  d.ellipse((x,y,x+1,y+1),fill=(37,59,66))
 return im

def scene_at(t):
 start=0
 for i,s in enumerate(SCENES):
  if t<start+s['duration']:return i,s,t-start,start
  start+=s['duration']
 return len(SCENES)-1,SCENES[-1],SCENES[-1]['duration'],TOTAL-SCENES[-1]['duration']

def graph(im,labels=None,old=None,mix=1,active=None,time_=0,cut=False,positions=None,small=False):
 labels=labels or {n:n for n in DATA['graphs']['golden']['nodes']}
 pos=positions or {'A':[190,240],'B':[415,200],'C':[330,390],'D':[610,420],'E':[530,550]}
 for u,v,w in DATA['graphs']['golden']['edges']:
  a,b=pos[u],pos[v];cross=labels[u]!=labels[v]
  c=GOLD if cut and cross else '#4e7277'
  if active in [u,v]:pulse_edge(im,a,b,time_,COLORS[labels[v if active==u else u]],1+w*.37)
  else:line(im,[a,b],c,1.3+w*.37)
  mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
  circle(im,mx,my,13,'#10252e');txt(im,str(w),mx,my-9,19,c if cut and cross else MUTED,center=True)
 for n,(x,y) in pos.items():
  color=COLORS[labels[n]]
  if old and old[n]!=labels[n]:color=blend(COLORS[old[n]],color,mix)
  # draw accepts both RGB tuples and hex strings
  circle(im,x,y,29,'#0d2029',color,2.6)
  if n==active:circle(im,x,y,37+math.sin(time_*3)*2,None,GOLD,1.2)
  txt(im,n,x,y-13,30,INK,center=True)
  txt(im,'标签 '+labels[n],x,y+39,17,COLORS[labels[n]],center=True)

def vote_bars(im,votes,p=1,x=850,y=290,title='按标签累计的权重'):
 txt(im,title,x,y-50,21,MUTED)
 maximum=max(votes.values(),default=1)
 for j,(label,val) in enumerate(sorted(votes.items())):
  yy=y+j*64;txt(im,label,x,yy,25,COLORS.get(label,GOLD))
  rect(im,(x+45,yy+3,x+45+230*(val/maximum)*smooth(p),yy+24),COLORS.get(label,GOLD),r=2)
  txt(im,str(val),x+290,yy,25,INK)

def person(im,x,y,label,t,group=False):
 c=COLORS[label]
 circle(im,x,y-26,11,c)
 ImageDraw.Draw(im).arc((*pt(x-24,y-9),*pt(x+24,y+44)),180,360,fill=c,width=round(4*S))
 # A book, visibly different from a graph vertex.
 rect(im,(x-18,y+8,x+18,y+32),'#152c34',c,1,r=2);line(im,[(x,y+9),(x,y+31)],c,1)

def library(im,t,end=False,morph=0):
 pos={'A':(250,260),'B':(445,230),'C':(370,450),'D':(830,280),'E':(1000,420)}
 for i in range(5):
  yy=185+i*70
  line(im,[(140,yy),(1130,yy)],'#1f343b',1)
  for j in range(12):
   xx=150+j*85;h=20+(i*13+j*17)%27
   rect(im,(xx,yy-h,xx+14,yy),'#152b34')
 for u,v,w in DATA['graphs']['golden']['edges']:
  a=pos[u];b=pos[v]
  pulse_edge(im,(a[0],a[1]+5),(b[0],b[1]+5),t,TEAL if end and u in 'ABC' and v in 'ABC' else GOLD,1+w*.22)
 for n,(x,y) in pos.items():
  label=('B' if n in 'ABC' else 'E') if end else n
  person(im,x,y+math.sin(t+n.__len__())*2,label,t)
  txt(im,n,x,y+47,18,MUTED,center=True)
 txt(im,'虚构借阅互动 · 仅为结构类比',640,570,16,MUTED,center=True)

def render(t):
 idx,s,local,start=scene_at(t);dur=s['duration'];p=local/dur
 im=backdrop().copy();vis=s['visual'];fade=smooth(local/.65)*smooth((dur-local)/.6)
 txt(im,s['chapter'],76,43,16,GOLD)
 if vis not in ['title','credits']:
  txt(im,s['title'],76,92,34,INK,serif=True)
 if vis in ['library','library-end','morph']:
  library(im,local,vis=='library-end')
  if vis=='morph' and p>.42:
   # Transform the whole relationship view by cross-fading into the graph.
   over=backdrop().copy();txt(over,s['chapter'],76,43,16,GOLD);txt(over,s['title'],76,92,34,INK,serif=True)
   graph(over,time_=local);txt(over,'节点 = 对象\n',850,270,23,TEAL);txt(over,'边权 = 建模的连接强度',850,325,21,MUTED)
   im=Image.blend(im,over,smooth((p-.42)/.32))
 elif vis in ['title','credits']:
  center=(640,310)
  for k in range(3):
   rr=100+k*53
   ImageDraw.Draw(im).arc((*pt(640-rr,310-rr),*pt(640+rr,310+rr)),round(-60+local*5+k*30),round(120+local*5+k*30),fill='#29474b',width=round(S))
  for j in range(5):
   angle=j*math.tau/5+local*.055;x=640+210*math.cos(angle);y=310+95*math.sin(angle)
   glow(im,x,y,4,list(COLORS.values())[j])
  txt(im,'邻居的颜色',640,235,68,GOLD,True,True,smooth(local/1.6))
  txt(im,'LABEL PROPAGATION',640,345,22,MUTED,center=True)
  if vis=='credits':
   txt(im,'Su3037 · Clustering Lab 05',640,425,21,INK,center=True)
   txt(im,'原创动画与配乐 · 复现工程随仓库提供',640,478,19,MUTED,center=True)
 elif vis=='initial':
  graph(im,time_=local)
  for j,n in enumerate('ABCDE'):txt(im,f'{n} → {n}',900,230+j*53,26,COLORS[n])
  txt(im,'初始标签',900,186,18,MUTED)
 elif vis=='weight':
  pos={'A':(550,360),'B':(210,240),'C':(210,470),'D':(800,360)}
  for n,w in [('B',1),('C',1),('D',4)]:
   pulse_edge(im,pos[n],pos['A'],local,COLORS['B' if n in 'BC' else 'D'],w+1)
   txt(im,str(w),(pos[n][0]+550)/2,(pos[n][1]+360)/2-25,23,MUTED)
  for n,(x,y) in pos.items():
   label='B' if n in 'BC' else n;circle(im,x,y,29,'#11262f',COLORS[label],2);txt(im,n,x,y-14,28,center=True)
   txt(im,'标签 '+label,x,y+40,18,COLORS[label],center=True)
  vote_bars(im,{'B':2,'D':4},local/2,960,290,'权重相加')
 elif vis=='formula':
  txt(im,'邻居的标签',175,230,25,MUTED);txt(im,'B     B     D     E',175,295,36,TEAL)
  txt(im,'边的权重',175,375,25,MUTED);txt(im,'1     4     2     1',175,435,36,GOLD)
  vote_bars(im,{'B':5,'D':2,'E':1},local/2,780,260)
  txt(im,'选择：B',910,505,32,TEAL,center=True)
 elif vis=='event':
  e=DATA['golden']['events'][s['event']];flip=dur*.5;progress=smooth((local-flip)/1.1)
  labels=e['labels'] if local>=flip else e['before']
  graph(im,labels,e['before'] if local>=flip else None,progress,e['node'],local)
  vote_bars(im,e['votes'],local/2)
  msg=f"{e['node']}：{e['old']} → {e['label']}" if e['changed'] else f"{e['node']} 保留 {e['label']}"
  txt(im,msg,855,515,32,COLORS[e['label']],alpha=smooth((local-flip)/.8))
 elif vis=='verify':
  labels=DATA['golden']['labels'];active='ABCDE'[min(4,int(p*5))]
  graph(im,labels,active=active,time_=local)
  txt(im,'第 2 轮',850,235,28,MUTED);txt(im,'0 次变化',850,300,47,TEAL)
  txt(im,'确认稳定后停止',850,390,24,INK)
 elif vis=='cut':
  graph(im,DATA['golden']['labels'],time_=local,cut=True)
  txt(im,'C—D     2',860,260,29,GOLD);txt(im,'C—E     1',860,325,29,GOLD)
  line(im,[(850,380),(1140,380)],'#5b6460',1)
  txt(im,'cutsize = 3',850,415,37,INK)
 elif vis=='zero':
  labels=DATA['golden']['labels'] if p<.45 else dict.fromkeys('ABCDE','B')
  graph(im,labels,time_=local,cut=True)
  txt(im,'2 组 → 1 组',845,245,31,INK);txt(im,'cutsize 3 → 0',845,315,31,GOLD)
  txt(im,'“更小”需要结合任务判断',845,415,21,MUTED)
 elif vis in ['sync','async']:
  states=[{'A':'A','B':'B'},{'A':'B','B':'A'}] if vis=='sync' else [{'A':'A','B':'B'},{'A':'B','B':'B'}]
  k=int(local/2.2);labels=states[k%2] if vis=='sync' else states[min(1,k)]
  pulse_edge(im,(380,335),(900,335),local,GOLD,2)
  for n,x in [('A',380),('B',900)]:
   circle(im,x,335,55,'#10242e',COLORS[labels[n]],3);txt(im,n,x,313,45,center=True)
   txt(im,'标签 '+labels[n],x,418,30,COLORS[labels[n]],center=True)
  txt(im,('同一轮只读旧值' if vis=='sync' else '第二个点读到新值'),640,205,26,MUTED,center=True)
  txt(im,('A/B     B/A     A/B     …' if vis=='sync' else 'A/B     B/B     稳定'),640,520,30,GOLD,center=True)
 elif vis=='order':
  reverse=DATA['reverse'];graph(im,reverse['labels'],time_=local)
  txt(im,'访问 E D C B A',825,220,27,MUTED);txt(im,'确认稳定：3 轮',825,286,32,GOLD)
  txt(im,'最终仍为 {A,B,C} / {D,E}',825,365,23,INK)
  txt(im,'名字不同，分组可以相同',825,435,22,TEAL)
 elif vis=='tie':
  vote_bars(im,{'B':5,'E':5},local/2,270,260)
  txt(im,'B  <  E',900,290,49,GOLD,center=True)
  txt(im,'默认选择 B',900,385,28,TEAL,center=True)
  txt(im,'课堂规则：字典序最小',900,445,20,MUTED,center=True)
 elif vis=='stop':
  for j,(a,b,c) in enumerate([('stable','整轮零变化',TEAL),('cycle','完整状态再次出现',RED),('limit','到达安全轮数上限',GOLD)]):
   y=220+j*112;txt(im,a,170,y,33,c);txt(im,b,530,y+5,27,INK)
 elif vis=='eda':
  labels=DATA['golden']['labels'];pos={'A':[215,240],'B':[430,220],'C':[330,415],'D':[650,365],'E':[560,540]}
  for u,v,w in DATA['graphs']['golden']['edges']:
   a,b=pos[u],pos[v];mid=(b[0],a[1]);line(im,[a,mid,b],COLORS[labels[u]] if labels[u]==labels[v] else GOLD,2)
  for n,(x,y) in pos.items():
   rect(im,(x-37,y-23,x+37,y+23),'#132d32',COLORS[labels[n]],2,3);txt(im,n,x,y-11,24,center=True)
  txt(im,'粗化 / 初始分组的线索',825,260,27,TEAL)
  txt(im,'规模约束',825,335,25,MUTED);txt(im,'时序约束',825,393,25,MUTED);txt(im,'物理实现与拥塞',825,451,25,MUTED)
  txt(im,'电路连线示意，非真实网表',410,580,17,MUTED,center=True)
 elif vis=='boundary':
  graph(im,DATA['golden']['labels'],time_=local)
  txt(im,'连接 ≠ 因果',850,245,35,GOLD)
  txt(im,'标签 ≠ 个人本质',850,325,32,INK)
  txt(im,'模型需要解释和检验',850,420,23,MUTED)
 # Single full-width Chinese sentence at a time, held long enough for reading.
 cap=s['captions'][0 if p<.5 else 1]
 capfade=smooth((local if p<.5 else local-dur*.5)/.4)
 line(im,[(76,614),(1204,614)],'#2d4349',1)
 size=27 if len(cap)<39 else 24
 txt(im,cap,640,647,size,INK,center=True,alpha=capfade)
 txt(im,'Su3037',1204,43,13,MUTED,center=False)
 rect(im,(76,703,76+1128*t/TOTAL,705),GOLD)
 if fade<1:im=Image.blend(backdrop(),im,fade)
 return im

def stamp(t):
 h=int(t)//3600;m=int(t)//60%60;s=int(t)%60;ms=round((t%1)*1000)
 return f'{h:02}:{m:02}:{s:02}.{ms:03}'
def write_materials():
 media=ROOT/'site/media';media.mkdir(exist_ok=True)
 vtt=['WEBVTT',''];start=0;chapters=[];md=['# 邻居的颜色 分镜与字幕','',f'成片 {TOTAL} 秒，1920×1080，30 fps，无配音。片长为本项目设计选择。','']
 for i,s in enumerate(SCENES):
  chapters.append({'start':start,'title':s['chapter'],'id':s['id']})
  md.extend([f"## {stamp(start)} {s['title']}",f"画面：{s['visual']}",''])
  for j,cap in enumerate(s['captions']):
   a=start+j*s['duration']/2;b=start+(j+1)*s['duration']/2
   vtt.extend([f'{stamp(a)} --> {stamp(b)}',cap,'']);md.append(cap)
  md.append('');start+=s['duration']
 (media/'neighbors.zh.vtt').write_text('\n'.join(vtt),encoding='utf-8')
 (ROOT/'video/transcript.md').write_text('\n'.join(md),encoding='utf-8')
 (media/'chapters.json').write_text(json.dumps(chapters,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--stills',action='store_true');args=ap.parse_args()
 write_materials();out=ROOT/'build/private/film-stills';out.mkdir(parents=True,exist_ok=True)
 starts=[];a=0
 for s in SCENES:starts.append(a);a+=s['duration']
 for i,s in enumerate(SCENES):render(starts[i]+s['duration']*.7).save(out/f'{i:02}-{s["id"]}.jpg',quality=94)
 render(starts[2]+2.8).save(ROOT/'site/media/cover.jpg',quality=96)
 if args.stills:return
 seconds=12 if args.preview else TOTAL
 dest=ROOT/('build/private/preview.mp4' if args.preview else 'build/private/picture.mp4')
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE);start=time.time()
 try:
  for n in range(round(seconds*30)):
   p.stdin.write(render(n/30).tobytes())
   if n%300==0:print(f'frame {n}/{seconds*30}, elapsed {time.time()-start:.1f}s',flush=True)
 finally:p.stdin.close()
 if p.wait()!=0:raise SystemExit('ffmpeg failed')
 print(dest,'seconds',seconds,flush=True)
if __name__=='__main__':main()
