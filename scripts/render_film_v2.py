#!/usr/bin/env python3
"""Original 2D illustrated film. All objects, characters and diagrams are code drawn.

No generated photographic plates are used. render(t) is deterministic and reads
actual LP traces. Music transients drive commitments, inserts and scene boundaries.
"""
import argparse, bisect, colorsys, json, math, subprocess, time
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw
import numpy as np
from render_film import txt, line, circle, rect, pt, smooth, blend, stamp, S, W, H

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/'video/storyboard-v2.json').read_text())
DATA=json.loads((ROOT/'data/film-v2.json').read_text())
CUES=json.loads((ROOT/'video/music-cues-v2.json').read_text())
SCENES=PLAN['scenes'];STARTS=[s['start'] for s in SCENES];TOTAL=PLAN['duration']
PALETTE={'A':'#d69c54','B':'#43a88d','C':'#cf785f','D':'#7099bd','E':'#b28ab4'}
PAPER='#f1ead8';NAVY='#122f3a';DARK='#173e45';GOLD='#d4ad66';RED='#d27261';TEAL='#51b99d'
THEMES={'paper':(PAPER,NAVY,'#6d7970'),'night':(NAVY,PAPER,'#a4b9b2'),'sage':('#d6e2cf',NAVY,'#647d73'),'rust':('#663f36',PAPER,'#d2b9a0')}
CITY_KEYS=sorted(set(DATA['city']['labels'].values()))
CITY_COLORS=dict(zip(CITY_KEYS,[TEAL,GOLD,'#899ed0']))

def color(label):
    if label in PALETTE:return PALETTE[label]
    if label in CITY_COLORS:return CITY_COLORS[label]
    i=int(label[1:]);r,g,b=colorsys.hsv_to_rgb((i*.618034)%1,.45,.78)
    return '#%02x%02x%02x'%(int(r*255),int(g*255),int(b*255))
def poly(im,points,fill,outline=None,width=1):
    d=ImageDraw.Draw(im);q=[pt(*p) for p in points];d.polygon(q,fill=fill)
    if outline:d.line(q+[q[0]],fill=outline,width=round(width*S),joint='curve')
def ellipse(im,xy,fill,outline=None,width=1):ImageDraw.Draw(im).ellipse((*pt(*xy[:2]),*pt(*xy[2:])),fill,outline,round(width*S))
def arc(im,xy,start,end,c,width=2):ImageDraw.Draw(im).arc((*pt(*xy[:2]),*pt(*xy[2:])),start,end,fill=c,width=round(width*S))
def label(im,text,x,y,size=25,c=NAVY,serif=False,center=False,alpha=1):txt(im,text,x,y,size,c,serif,center,alpha)
def lerp(a,b,p):return a+(b-a)*p
def point(a,b,p):return (lerp(a[0],b[0],p),lerp(a[1],b[1],p))
def pathpoint(points,p):
    q=min(.99999,max(0,p))*(len(points)-1);i=int(q);return point(points[i],points[i+1],q-i)
def rounded(im,xy,fill,outline=None,width=1,r=10):rect(im,xy,fill,outline,width,r)
def action(s,index=0):return s['actions'][min(index,len(s['actions'])-1)] if s['actions'] else s['duration']*.35
def reveal(local,at,span=.45):return smooth((local-at)/span)
def beat_at(t):return min(CUES['grid'],key=lambda a:abs(a-t))
def snapped(t):
    b=beat_at(t);ons=[o for o in CUES['onsets'] if abs(o['time']-b)<.13]
    return round((max(ons,key=lambda o:o['strength'])['time'] if ons else b)*30)/30
BEATS=sorted(set(snapped(t) for t in CUES['grid']))
def beats_in(s):return [t-s['start'] for t in BEATS if s['start']+.2<t<s['start']+s['duration']-.2]

@lru_cache(maxsize=6)
def background(theme):
    bg,ink,muted=THEMES[theme];im=Image.new('RGB',(W,H),bg)
    # Stationary fine paper grain: material, not decorative moving particles.
    a=np.array(im,dtype=np.int16);noise=np.random.default_rng(51).integers(-2,3,(H,W,1),dtype=np.int16)
    im=Image.fromarray(np.clip(a+noise,0,255).astype('uint8'))
    return im
def shadow(im,x,y,w=80):ellipse(im,(x-w/2,y-5,x+w/2,y+5),'#b9bba8')
def book(im,x,y,w=130,opening=1,c=TEAL):
    h=w*.62;wing=max(.06,opening)*w*.5
    poly(im,[(x-wing-7,y),(x,y+10),(x+wing+7,y),(x+wing+7,y+h+10),(x,y+h+21),(x-wing-7,y+h+10)],c,NAVY,2)
    poly(im,[(x-wing,y-5),(x,y+5),(x,y+h+13),(x-wing,y+h)],'#fff7e2',NAVY,1.2)
    poly(im,[(x,y+5),(x+wing,y-5),(x+wing,y+h),(x,y+h+13)],'#e4dec9',NAVY,1.2)
    for k in range(4):
        yy=y+18+k*h*.17;line(im,[(x-wing*.8,yy),(x-wing*.15,yy+7)],'#b7b8a5',1)
        line(im,[(x+wing*.15,yy+7),(x+wing*.8,yy)],'#b7b8a5',1)
    poly(im,[(x+wing*.6,y-3),(x+wing*.6+11,y-5),(x+wing*.6+11,y+36),(x+wing*.6+5,y+29),(x+wing*.6,y+36)],GOLD)
def closed_book(im,x,y,w=34,h=45,c=TEAL,tilt=0):
    poly(im,[(x-w/2,y-h/2),(x+w/2,y-h/2+tilt),(x+w/2,y+h/2),(x-w/2,y+h/2-tilt)],c,NAVY,1.6)
    line(im,[(x-w/2+5,y-h/2+2),(x-w/2+5,y+h/2-3)],PAPER,1.5)
    line(im,[(x-w/2+7,y+h/2-4),(x+w/2-3,y+h/2-4)],PAPER,1.5)
def reader(im,x,y,c=TEAL,scale=1,walk=0,pose=0,who=0,carrying=False):
    # y is the floor. Deliberately illustrated, articulated limbs and tiny faces.
    sc=scale;cx=lambda u:x+u*sc;cy=lambda v:y+v*sc
    ellipse(im,(cx(-23),cy(-4),cx(23),cy(5)),'#b0b7a6')
    swing=math.sin(walk)*10
    for side in [-1,1]:
        line(im,[(cx(side*10),cy(-44)),(cx(side*11+swing*side),cy(-22)),(cx(side*15-swing*side),cy(-2))],NAVY,7*sc)
        line(im,[(cx(side*15-swing*side),cy(-2)),(cx(side*15-swing*side+10),cy(-2))],NAVY,5*sc)
    rounded(im,(cx(-22),cy(-91),cx(22),cy(-43)),c,r=10*sc)
    # Curved arms reach toward the passing book.
    for side in [-1,1]:
        hand=(cx(side*(27+pose*18)),cy(-62-pose*12))
        line(im,[(cx(side*17),cy(-83)),(cx(side*30),cy(-68)),hand],c,8*sc)
        circle(im,*hand,5*sc,'#e4b590')
    circle(im,cx(0),cy(-111),18*sc,'#e4b590')
    arc(im,(cx(-19),cy(-131),cx(20),cy(-91)),180,355,NAVY,(10 if who%2 else 8)*sc)
    circle(im,cx(6),cy(-112),1.4*sc,NAVY)
    line(im,[(cx(11),cy(-108)),(cx(15),cy(-106)),(cx(10),cy(-104))],NAVY,1*sc)
    if who%3==0:line(im,[(cx(-2),cy(-114)),(cx(12),cy(-114))],NAVY,1.5*sc)
    if carrying:closed_book(im,cx(22),cy(-66),30*sc,35*sc,GOLD)

@lru_cache(maxsize=2)
def room(end=False):
    im=background('paper').copy()
    poly(im,[(80,140),(825,140),(825,480),(80,480)],'#e2d6b7')
    poly(im,[(80,480),(825,480),(1220,580),(40,580)],'#dad9c3')
    for col in range(4):
        x=100+col*164
        rounded(im,(x,168,x+145,463),'#a9b79d',NAVY,1.5,3)
        for row in range(3):
            yy=238+row*87;line(im,[(x,yy),(x+145,yy)],NAVY,3)
            for j in range(8):
                h=32+(j*13+row*11+col*7)%27;xx=x+8+j*16
                rounded(im,(xx,yy-h,xx+11,yy-2),[TEAL,GOLD,RED,'#7e9eb3','#b5b093'][(j+col+row)%5],r=1)
    rounded(im,(857,133,1185,466),NAVY,NAVY,2,2)
    circle(im,1114,184,25,GOLD)
    for k in range(12):
        x=875+k*24;hh=40+(k*37)%100;rounded(im,(x,440-hh,x+18,440),'#35606a',r=0)
        for yy in range(round(450-hh),430,18):rect(im,(x+5,yy,x+9,yy+7),GOLD)
    line(im,[(1021,135),(1021,465)],'#e2d6b7',8)
    line(im,[(858,313),(1185,313)],'#e2d6b7',8)
    for x,y in [(376,471),(940,501)]:
        for leg in [-1,1]:line(im,[(x+leg*98,y),(x+leg*115,y+64)],NAVY,7)
        ellipse(im,(x-158,y-28,x+158,y+25),'#bc9670',NAVY,2)
        line(im,[(x,y-2),(x,y-67)],NAVY,3);poly(im,[(x-28,y-67),(x+28,y-67),(x+18,y-95),(x-18,y-95)],GOLD,NAVY,1)
    return im
def library(im,s,local,end=False,cross=False):
    im.paste(room(end));p=local/s['duration']
    poses=[(285,530,TEAL,0),(467,535,RED,1),(853,565,'#899ed0',2),(1050,563,GOLD,3)]
    for x,y,c,i in poses:reader(im,x,y,c,.78,0,math.sin(local)*.2+.2,i)
    if not end:
        xx=lerp(90,580,smooth(min(1,local/3.5)));reader(im,xx,562,TEAL,.85,local*8,.4,0,True)
        # One actual transfer, with a brief anticipation/release on measured beat.
        q=reveal(local,action(s),1.1);closed_book(im,lerp(325,435,q),lerp(455,453,q)-math.sin(q*math.pi)*45,35,43,GOLD)
    elif cross:
        xx=lerp(479,825,smooth(p));reader(im,xx,566,TEAL,.86,local*8,.5,0,True)
        arc(im,(415,385,920,600),185,350,'#8ba597',2)
    else:
        for a,b,c in [((320,454),(433,454),TEAL),((900,485),(1010,485),'#899ed0')]:
            arc(im,(a[0],a[1]-55,b[0],b[1]+10),185,350,c,2)
        label(im,'虚构的借阅场景 · 只作结构类比',640,588,16,'#677f72',center=True)

def book_scene(im,s,local,closing=False):
    p=local/s['duration'];o=smooth(min(1,local/1.5))
    ellipse(im,(290,500,990,573),'#c2c8b5')
    x=640 if closing else lerp(515,730,reveal(local,action(s),1.1))
    # Illustrated sleeves and hands make the opening verb literally visible.
    if not closing:
        rounded(im,(125,422,x-95,474),TEAL,r=18)
        rounded(im,(x+105,422,1150,474),'#899ed0',r=18)
        rounded(im,(x-115,426,x-35,467),'#e4b590',NAVY,1,13)
        rounded(im,(x+38,426,x+118,467),'#e4b590',NAVY,1,13)
    book(im,x,226,530,o,TEAL)
    if closing:
        pos={'A':(525,335),'B':(590,300),'C':(580,390),'D':(746,333),'E':(748,407)}
        for u,v,w in DATA['goldenGraph']['edges']:line(im,[pos[u],pos[v]],'#8c9c89',1+w*.3)
        for n,(x,y) in pos.items():circle(im,x,y,9,color(DATA['golden']['labels'][n]))
    else:
        for i,c in enumerate(PALETTE.values()):
            if local>i*.16:rounded(im,(489+i*63,344,530+i*63,397),c,r=4)
    label(im,'借阅卡',640,186,19,'#6c8376',center=True)

def table_scene(im,s,local,morph=False):
    p=local/s['duration'];pos=[(290,270),(555,220),(439,458),(893,285),(963,476)]
    ellipse(im,(160,165,1100,554),'#cbb594',NAVY,2)
    for j,(x,y) in enumerate(pos):
        circle(im,x,y,36,PAPER,NAVY,2);arc(im,(x-25,y-16,x+25,y+35),190,350,list(PALETTE.values())[j],9)
        circle(im,x,y-9,10,'#dba984');closed_book(im,x+50,y+4,28,36,list(PALETTE.values())[j])
    cue=beats_in(s)
    for j,(u,v,w) in enumerate(DATA['goldenGraph']['edges']):
        a=pos[ord(u)-65];b=pos[ord(v)-65];q=reveal(local,cue[min(j,len(cue)-1)] if cue else .2*j,.35)
        line(im,[a,point(a,b,q)],'#7b8e7b',1+w*.65)
        x,y=point(a,b,(local*.6+j*.16)%1);closed_book(im,x,y,15,19,list(PALETTE.values())[j%5])
    if morph:
        q=reveal(local,action(s),1.2)
        for j,(x,y) in enumerate(pos):
            a=point((x,y),[(310,290),(520,240),(450,435),(850,300),(850,470)][j],q)
            circle(im,*a,lerp(8,31,q),list(PALETTE.values())[j],NAVY,2)
            label(im,'ABCDE'[j],a[0],a[1]-13,26,NAVY,center=True,alpha=q)

def tag_scene(im,s,local):
    beat=beats_in(s)
    for i,n in enumerate('ABCDE'):
        at=beat[min(i,len(beat)-1)] if beat else .2*i
        q=reveal(local,at,.45);x=240+i*200;y=lerp(170,310,q)
        if local<at:continue
        poly(im,[(x-49,y),(x+32,y),(x+49,y+20),(x+49,y+120),(x-49,y+120)],color(n),NAVY,2)
        circle(im,x+27,y+20,5,PAPER,NAVY,1)
        label(im,n,x,y+34,45,NAVY,True,True)
        label(im,'节点 '+n,x,y+145,21,NAVY,center=True)
    label(im,'标签可变，节点身份保留',640,555,23,'#657f73',center=True)

def balance(im,s,local,tie=False,people=False):
    q=reveal(local,action(s),.7);tilt=(0 if tie else q*42)
    poly(im,[(620,410),(660,410),(682,528),(598,528)],NAVY)
    circle(im,640,345,11,GOLD,NAVY,2)
    line(im,[(350,345-tilt),(930,345+tilt)],NAVY,8)
    for side,x in [(-1,350),(1,930)]:
        yy=345+tilt*side
        line(im,[(x-75,yy+125),(x,yy),(x+75,yy+125)],NAVY,2)
        ellipse(im,(x-93,yy+110,x+93,yy+146),'#bdc8af',NAVY,2)
        c=TEAL if side==-1 else ('#b28ab4' if tie else '#7099bd')
        vals=5 if tie else (2 if side==-1 else 4)
        for j in range(vals):
            tx=x+(j-(vals-1)/2)*26;circle(im,tx,yy+103,12,c,NAVY,1.5)
        label(im,'B' if side==-1 else ('E' if tie else 'D'),x,yy-67,44,c,True,True)
        label(im,str(vals) if tie else ('1 ＋ 1' if side==-1 else '4'),x,yy+165,33,NAVY,center=True)
    if tie:
        if q>.2:label(im,'B < E  →  B',640,205,37,TEAL,center=True,alpha=q)
    elif people:
        for x,c,i in [(280,TEAL,0),(420,TEAL,1),(930,'#7099bd',2)]:reader(im,x,280,c,.65,0,.3,i)
    elif q>.2:label(im,'D 胜',640,190,42,'#7099bd',True,True,alpha=q)

def vessel(im,x,y,key,val,progress=1,ink=NAVY):
    c=color(key);line(im,[(x-62,y-74),(x-55,y+92),(x+55,y+92),(x+62,y-74)],ink,2.5)
    for j in range(val):
        q=smooth((progress*val-j)*1.5);yy=lerp(y-125,y+70-(j//3)*27,q);xx=x+(j%3-1)*29
        if progress*val>=j:circle(im,xx,yy,11,c,ink,1.3)
    label(im,key,x,y-130,34,c,True,True)
    label(im,str(val),x,y+115,37,ink,center=True)
def tokens_scene(im,s,local):
    q=reveal(local,action(s),1.2)
    for x,k,v in [(370,'B',5),(700,'D',2),(980,'E',1)]:vessel(im,x,360,k,v,q)
    label(im,'1',210,245,32,TEAL,center=True);label(im,'4',260,390,32,TEAL,center=True)
    line(im,[(230,275),(304,300)],TEAL,3);line(im,[(282,410),(310,380)],TEAL,3)
    if q>.8:label(im,'1 ＋ 4 ＝ 5',370,560,26,TEAL,center=True)

POS={'A':(225,274),'B':(445,222),'C':(409,429),'D':(685,307),'E':(685,507)}
def graph(im,labels,local,active=None,old=None,mix=1,cut=False,separate=0,positions=None,weights=None,flow_end=None):
    pos=dict(positions or POS)
    if separate:
        pos={n:(x+(-75 if n in 'ABC' else 115)*separate,y) for n,(x,y) in pos.items()}
    for u,v,w in weights or DATA['goldenGraph']['edges']:
        a,b=pos[u],pos[v];cross=labels[u]!=labels[v]
        c=GOLD if cut and cross else '#78978f';width=1.1+w*.42
        line(im,[a,b],c,width)
        mx,my=point(a,b,.5);circle(im,mx,my,13,NAVY if cut else PAPER)
        label(im,str(w),mx,my-10,20,PAPER if cut else NAVY,center=True)
        if active in [u,v] and (flow_end is None or local<=flow_end+.08):
            # Packets carry the neighbor's label, not arbitrary decorative colors.
            n=v if active==u else u;origin=pos[n];dest=pos[active]
            for j in range(min(w,5)):
                p=smooth((local-j*.08)/max(.2,flow_end-j*.08)) if flow_end else max(0,min(1,(local*.9-j*.12)%1.8))
                x,y=point(origin,dest,p)
                circle(im,x,y,4,color((old or labels)[n]))
    for n,(x,y) in pos.items():
        c=color(labels[n]);c=blend(color(old[n]),c,mix) if old and old[n]!=labels[n] else c
        if n==active:circle(im,x,y,46,None,GOLD,3)
        circle(im,x,y,32,c,PAPER if cut else NAVY,2)
        label(im,n,x,y-17,32,NAVY,True,True)
        label(im,'标签 '+labels[n],x,y+44,19,color(labels[n]),center=True)

def board_scene(im,s,local):
    vis=s['visual'];q=reveal(local,action(s),.55)
    if vis=='board':
        graph(im,{n:n for n in 'ABCDE'},local)
        for i,n in enumerate('ABCDE'):
            x=928+(i%3)*70;y=280+(i//3)*75;rounded(im,(x-22,y-23,x+22,y+23),color(n),r=3);label(im,n,x,y-12,25,NAVY,center=True)
        label(im,'访问队列',991,220,22,NAVY,center=True)
        label(im,'A → B → C → D → E',991,470,20,NAVY,center=True)
        label(im,'课程指定小图',417,580,17,'#70877c',center=True)
    elif vis=='visit':
        e=DATA['golden']['events'][s['event']];committed=local>=action(s);labels=e['labels'] if committed else e['before']
        graph(im,labels,local,e['node'],flow_end=action(s))
        votes=sorted(e['votes'].items())
        for j,(k,v) in enumerate(votes):vessel(im,(900+j*140) if len(votes)==3 else (930+j*175),345,k,v,reveal(local,.12,.8),NAVY)
        if committed:label(im,f"{e['node']}：{e['old']} → {e['label']}",990,560,34,color(e['label']),center=True)
    elif vis=='finish':
        e=DATA['golden']['events'][3 if q<.6 else 4];graph(im,e['labels'] if q else e['before'],local,e['node'])
        label(im,'D → E',982,282,45,color('E'),True,True,alpha=q)
        label(im,'E 保留 E',982,375,32,color('E'),center=True,alpha=reveal(local,action(s,1),.4))
    elif vis=='confirm':
        bs=beats_in(s);idx=min(4,max(0,bisect.bisect_right(bs,local)-1));graph(im,DATA['golden']['labels'],local,'ABCDE'[idx])
        for i,n in enumerate('ABCDE'):
            x=900+(i%3)*80;y=270+(i//3)*90
            label(im,n,x,y,27,THEMES['paper'][2],center=True)
            if i<=idx:line(im,[(x-13,y+46),(x-3,y+57),(x+18,y+32)],TEAL,4)
        label(im,'第 2 轮：0 次变化',980,520,29,TEAL,center=True)
    elif vis=='cut':
        graph(im,DATA['golden']['labels'],local,cut=True,separate=q)
        label(im,'2 ＋ 1',1030,290,52,GOLD,True,True)
        label(im,'cutsize = 3',1030,380,31,PAPER,center=True)
        label(im,'2 条跨组边',1030,450,23,'#a4b9b2',center=True)

def ledger_scene(im,s,local,zero=False):
    q=reveal(local,action(s),.7)
    rounded(im,(160,226,1120,510),'#e5ddc5',NAVY,2,7)
    line(im,[(160,280),(1120,280)],'#879b88',2)
    for i,n in enumerate('ABCDE'):
        x=256+i*190;label(im,n,x,241,26,NAVY,center=True)
        c='B' if zero and q>.5 else DATA['golden']['labels'][n]
        yy=lerp(315,342,reveal(local,.3+i*.18,.4));rounded(im,(x-57,yy,x+57,yy+92),color(c),NAVY,2,3)
        label(im,c,x,yy+19,46,NAVY,True,True)
    if zero:
        label(im,'2 组 → 1 组',640,170,32,NAVY,center=True)
        label(im,'cutsize  3 → 0',640,550,33,'#6b7e71',center=True,alpha=q)
    else:label(im,'标签  B   B   B   E   E',640,555,27,NAVY,center=True)

def mail(im,x,y,key,name,open_=0):
    rounded(im,(x-90,y-70,x+90,y+75),'#dddec7',NAVY,3,8)
    rounded(im,(x-75,y-57,x+75,y+49),color(key),NAVY,2,5)
    # A physical read flap with a hinge, rather than two bouncing circles.
    poly(im,[(x-75,y-57),(x+75,y-57),(x+75,y-57-65*open_),(x-75,y-57-65*open_)],PAPER,NAVY,2)
    label(im,key,x,y-33,54,NAVY,True,True);label(im,'节点 '+name,x,y+99,23,NAVY,center=True)
    line(im,[(x,y+77),(x,y+150)],NAVY,6)
def pair_scene(im,s,local,mode):
    bs=beats_in(s);k=bisect.bisect_right(bs,local)
    states=[{n:n for n in 'AB'}]+[e['labels'] for e in DATA['pairSync' if mode!='async' else 'pairAsync']['events'] if e['roundEnd']]
    if mode=='sync':idx=1 if local>action(s,1) else 0
    elif mode=='cycle':idx=(k//2)%3
    else:idx=1 if local>action(s) else 0
    st=states[min(idx,len(states)-1)]
    line(im,[(380,356),(900,356)],'#91a38c',3)
    for j,x in enumerate([380,900]):mail(im,x,340,st['AB'[j]],'AB'[j],.45 if local<action(s) else 0)
    if mode=='cycle':
        for j,st0 in enumerate(states[:3]):
            x=470+j*172;label(im,'/'.join(st0.values()),x,548,30,TEAL if j==idx else '#718479',center=True)
            if j<2:label(im,'→',x+87,548,26,NAVY,center=True)
    else:
        if mode=='async':
            e=DATA['pairAsync']['events'][0]
            label(im,'先写回',380,178,24,TEAL,center=True)
            label(im,'再读取',900,178,24,TEAL,center=True,alpha=reveal(local,action(s),.4))
        else:label(im,'一起读旧值 → 一起提交',640,179,27,NAVY,center=True)

CITYPOS={n:(270+(i//8)*360+94*math.cos((i%8)*math.tau/8),350+94*math.sin((i%8)*math.tau/8)) for i,n in enumerate(DATA['cityGraph']['nodes'])}
def city_labels(s,local,animated):
    if not animated:return DATA['city']['labels']
    bs=beats_in(s);count=bisect.bisect_right(bs,local);ne=len(DATA['city']['events'])
    k=min(ne,int(count/max(1,len(bs))*ne))
    return ({n:n for n in DATA['cityGraph']['nodes']} if k==0 else DATA['city']['events'][k-1]['labels'])
def house(im,x,y,c,scale=1):
    a=scale;rounded(im,(x-22*a,y-24*a,x+22*a,y+24*a),'#d7dbc4',NAVY,1.3,2)
    poly(im,[(x-28*a,y-25*a),(x,y-44*a),(x+28*a,y-25*a)],c,NAVY,1.3)
    for dx in [-9,9]:rounded(im,(x+(dx-3)*a,y-11*a,x+(dx+3)*a,y+2*a),c,r=1)
    rounded(im,(x-4*a,y+9*a,x+5*a,y+24*a),NAVY,r=1)
def many_scene(im,s,local,houses=False):
    labels=city_labels(s,local,not houses)
    for u,v,w in DATA['cityGraph']['edges']:
        a,b=CITYPOS[u],CITYPOS[v];c='#426a70' if not houses else '#b1bdab'
        line(im,[a,b],c,.8 if w>1 else 2)
    for n,(x,y) in CITYPOS.items():
        if houses:house(im,x,y,color(labels[n]),.84)
        else:circle(im,x,y,14,color(labels[n]),PAPER,1.5)
    for i,key in enumerate(CITY_KEYS):
        label(im,('群体 '+str(i+1)) if houses else key,270+i*360,528,25,color(key),center=True)
    label(im,'24 节点 / 86 条边 / 真实运行 / 最终 3 组',640,586,17,'#718b82' if houses else '#a4b9b2',center=True)
def bridge_scene(im,s,local):
    q=reveal(local,action(s),.65)
    poly(im,[(0,473),(0,520),(1280,400),(1280,353)],'#98b9b7')
    for j in range(6):line(im,[(j*250,490-j*22),(j*250+120,478-j*22)],'#c8d6c6',2)
    line(im,[(290,485),(880,423)],NAVY,8)
    for j in range(12):
        x,y=point((290,485),(880,423),j/11);line(im,[(x,y-22),(x,y+22)],NAVY,2)
    for i,n in enumerate('ABCDE'):
        x=[185,315,400,908,1050][i];y=[370,300,405,335,395][i]
        key=DATA['strong' if q>.5 else 'golden']['labels'][n];house(im,x,y,color(key),1.2)
        label(im,n,x,y+43,26,NAVY,center=True)
    label(im,'C—D',640,255,25,NAVY,center=True)
    label(im,'2 → 10',640,303,44,'#7099bd',True,True)
    for j in range(3+int(q*7)):
        x,y=point((330,480),(840,427),(local*.3+j*.1)%1);circle(im,x,y,5,GOLD,NAVY,1)
    label(im,'实际新分组：{A,B} / {C,D,E}',640,563,26,NAVY,center=True,alpha=q)
def order_scene(im,s,local):
    for row,rev in enumerate([False,True]):
        y=270+row*190;names='EDCBA' if rev else 'ABCDE'
        line(im,[(200,y+45),(1080,y+45)],'#9cae97',2)
        for i,n in enumerate(names):
            x=280+i*170;closed_book(im,x,y+16,50,64,color(n));label(im,n,x,y+67,23,NAVY,center=True)
        label(im,'倒序 · 3 轮' if rev else '正序 · 2 轮',640,y-70,30,NAVY,center=True)

def chip_scene(im,s,local,packed=False,constraints=False):
    q=1 if constraints else reveal(local,action(s),.9);cx,cy=640,355
    rounded(im,(172,160,1108,567),'#24545a',GOLD,2,18)
    for x in range(210,1090,35):
        line(im,[(x,160),(x,130)],GOLD,4);line(im,[(x,567),(x,597)],GOLD,4)
    for y in range(190,560,30):
        line(im,[(172,y),(140,y)],GOLD,4);line(im,[(1108,y),(1140,y)],GOLD,4)
    target={n:(280+(i//8)*310+(i%4)*48,288+(i%8//4)*110) for i,n in enumerate(DATA['cityGraph']['nodes'])}
    positions={n:point(CITYPOS[n],target[n],q if packed else 0) for n in CITYPOS}
    for u,v,w in DATA['cityGraph']['edges']:
        a,b=positions[u],positions[v];line(im,[a,(b[0],a[1]),b],'#48716c',1.2 if w>1 else 2)
    for n,(x,y) in positions.items():
        c=color(DATA['city']['labels'][n]);rounded(im,(x-17,y-23,x+17,y+23),c,PAPER,1,2)
    if packed:
        for i,key in enumerate(CITY_KEYS):
            rounded(im,(251+i*310,243,463+i*310,454),None,color(key),2,8)
    if constraints:
        for i,(text,c) in enumerate([('规模',GOLD),('时序','#b28ab4'),('拥塞',RED)]):
            x=335+i*310;label(im,text,x,486,26,c,center=True)
            if local>=action(s,i):
                if i==0:
                    line(im,[(x-70,228),(x-70,199),(x+70,199),(x+70,228)],c,3)
                elif i==1:
                    circle(im,x,208,26,None,c,3)
                    angle=-math.pi/2+max(0,local-action(s,i))*1.5
                    line(im,[(x,208),(x+17*math.cos(angle),208+17*math.sin(angle))],c,3)
                else:
                    for j in range(7):line(im,[(x-75,185+j*7),(x+75,245-j*5)],c,2)
    label(im,'虚构单元连线示意 · 仅展示分组线索',640,614,16,'#a4b9b2',center=True)
def controls_scene(im,s,local):
    for j,(word,c) in enumerate([('数据',TEAL),('边权',GOLD),('规则','#899ed0')]):
        x=310+j*330;circle(im,x,325,76,c,NAVY,2)
        label(im,word,x,300,34,NAVY,True,True)
        theta=local*.25+j;line(im,[(x,325),(x+55*math.cos(theta),325+55*math.sin(theta))],NAVY,4)
    label(im,'模型的条件，写在结果旁边',640,526,30,NAVY,center=True)

def draw_world(s,local):
    vis=s['visual'];theme='paper'
    if vis in ['title','cut','many','chip','floorplan','constraints','credits']:theme='night'
    elif vis in ['tags','table','morph','city','order','ribbons']:theme='sage'
    im=background(theme).copy()
    if vis in ['book','close']:book_scene(im,s,local,vis=='close')
    elif vis in ['library','return','cross']:library(im,s,local,vis!='library',vis=='cross')
    elif vis in ['table','morph']:table_scene(im,s,local,vis=='morph')
    elif vis=='tags':tag_scene(im,s,local)
    elif vis in ['weight','scale','tie']:balance(im,s,local,vis=='tie',vis=='weight')
    elif vis=='tokens':tokens_scene(im,s,local)
    elif vis in ['board','visit','finish','confirm','cut']:board_scene(im,s,local)
    elif vis in ['ledger','zero']:ledger_scene(im,s,local,vis=='zero')
    elif vis in ['sync','cycle','async']:pair_scene(im,s,local,vis)
    elif vis in ['many','city']:many_scene(im,s,local,vis=='city')
    elif vis=='bridge':bridge_scene(im,s,local)
    elif vis=='order':order_scene(im,s,local)
    elif vis in ['chip','floorplan','constraints']:chip_scene(im,s,local,vis!='chip',vis=='constraints')
    elif vis=='ribbons':controls_scene(im,s,local)
    elif vis=='title':
        q=reveal(local,.1,.8)
        # Five ribbon bookmarks arc out and settle into the title's baseline.
        for i,c in enumerate(PALETTE.values()):
            x=440+i*100;y=lerp(450+70*math.sin(i),440,q)
            poly(im,[(x-22,y-42),(x+22,y-42),(x+22,y+44),(x,y+26),(x-22,y+44)],c)
        label(im,'邻居的颜色',640,220,78,GOLD,True,True,alpha=q)
        label(im,'LABEL PROPAGATION',640,342,22,'#a4b9b2',center=True,alpha=q)
    elif vis=='credits':
        label(im,'邻居的颜色',640,205,62,GOLD,True,True)
        label(im,'Su3037 · Clustering Lab 05',640,307,24,PAPER,center=True)
        label(im,'音乐：We Never (Remix)（若如初见）',640,389,23,PAPER,center=True)
        label(im,'Hi Noise / 秋成 · 用户指定版本 BV134Ho6qENu',640,432,18,'#a4b9b2',center=True)
        label(im,'课程 Lab05 · Raghavan, Albert & Kumara (2007)',640,505,18,'#a4b9b2',center=True)
        label(im,'音乐为第三方录音，不属于本项目的 CC 许可',640,547,16,'#a4b9b2',center=True)
    return im,theme

def render(t):
    idx=max(0,min(len(SCENES)-1,bisect.bisect_right(STARTS,t)-1));s=SCENES[idx];local=t-s['start']
    im,theme=draw_world(s,local);bg,ink,muted=THEMES[theme]
    if idx and local<.23:
        prev=SCENES[idx-1];old,_=draw_world(prev,prev['duration']-.02);im=Image.blend(old,im,smooth(local/.23))
    # Camera belongs to the illustration layer. Titles/subtitles remain still.
    p=local/s['duration'];z=1.0;fx,fy=640*S,360*S
    if s['visual'] in ['book','close']:z=1.02+.055*smooth(p)
    elif s['visual'] in ['table','morph']:z=1.01+.07*smooth(p)
    elif s['visual']=='many':z=lerp(1.22,1,smooth(p))
    elif s['visual']=='city':z=lerp(1.06,1,smooth(p))
    elif s['visual']=='chip':z=lerp(1.10,1,smooth(p))
    elif s['visual']=='visit':z=1+.025*smooth(p)
    elif s['visual']=='cross':z=1+.035*smooth(p)
    if z!=1:im=im.transform((W,H),Image.Transform.AFFINE,(1/z,0,fx*(1-1/z),0,1/z,fy*(1-1/z)),Image.Resampling.BILINEAR)
    if s['visual'] not in ['title','credits']:
        label(im,s['chapter'],70,40,17,muted)
        label(im,s['title'],70,82,33,ink,True,alpha=reveal(local,.08,.3))
    label(im,'Su3037',1205,42,14,muted,center=True)
    cap=s['caption'];alpha=reveal(local,.25,.3)*smooth((s['duration']-local)/.2)
    label(im,cap,640,655,26 if len(cap)<=34 else 23,ink,center=True,alpha=alpha)
    if t>TOTAL-1.6:im=Image.blend(im,background('night'),smooth((t-(TOTAL-1.6))/1.6))
    return im

def write_materials():
    media=ROOT/'site/media';vtt=['WEBVTT',''];md=['# 邻居的颜色 第二版分镜','',f'{TOTAL:.3f} 秒 / 1080p / 30fps / 二维图形动画 / 无配音','',
      '音乐：We Never (Remix)（若如初见）—Hi Noise / 秋成。用户指定 BV134Ho6qENu，按原上传速度使用。音乐不属于项目 CC 许可。','']
    chapters=[]
    for s in SCENES:
        a=s['start'];b=a+s['duration'];vtt.extend([f'{stamp(a+.25)} --> {stamp(b-.1)}',s['caption'],''])
        chapters.append({'start':a,'title':s['title'],'id':s['id']})
        md.extend([f'## {stamp(a)} {s["title"]}',s['caption'],'',f'画面：{s["camera"]}',f'按实测节奏安排的动作时间：{[round(a+x,3) for x in s["actions"]]} 秒',''])
    (media/'neighbors.zh.vtt').write_text('\n'.join(vtt))
    (media/'chapters.json').write_text(json.dumps(chapters,ensure_ascii=False,indent=2))
    (ROOT/'video/transcript-v2.md').write_text('\n'.join(md))
    (ROOT/'site/downloads/transcript.md').write_text('\n'.join(md))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stills',action='store_true');ap.add_argument('--preview',action='store_true');ap.add_argument('--start',type=float,default=0);ap.add_argument('--seconds',type=float);ap.add_argument('--music',type=Path,default=ROOT/'build/private/research-v2/chosen-music-audio.m4a');a=ap.parse_args()
    out=ROOT/'build/private/v2';out.mkdir(parents=True,exist_ok=True)
    for i,s in enumerate(SCENES):
        render(s['start']+s['duration']*.65).save(out/f'{i:02}-{s["id"]}.jpg',quality=94)
    if a.stills:return
    seconds=a.seconds or (25 if a.preview else TOTAL)
    picture=out/('sample-picture.mp4' if a.preview else 'picture.mp4')
    dest=(ROOT/'../output/邻居的颜色_v2_二维样片.mp4').resolve() if a.preview else ROOT/'site/media/neighbors.mp4'
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(picture)]
    enc=subprocess.Popen(cmd,stdin=subprocess.PIPE);clock=time.monotonic()
    try:
        for n in range(round(seconds*30)):
            enc.stdin.write(render(a.start+n/30).tobytes())
            if n%150==0:print(f'v2 frame {n}/{round(seconds*30)} ({time.monotonic()-clock:.1f}s)',flush=True)
    finally:enc.stdin.close()
    if enc.wait():raise RuntimeError('video encoder failed')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(picture),'-ss',str(a.start),'-i',str(a.music),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','volume=0.45','-c:a','aac','-b:a','192k','-t',str(seconds),'-movflags','+faststart',str(dest)],check=True)
    if not a.preview:
        write_materials();render(19.5).save(ROOT/'site/media/cover.jpg',quality=95)
    print(dest,flush=True)
if __name__=='__main__':main()
