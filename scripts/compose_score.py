#!/usr/bin/env python3
"""Original score 'Between Neighbors'. No recordings, samples or external AI APIs.
Optional --music PATH replaces only the original score, retaining the video picture.
"""
import argparse,json,math,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];SR=48000
scenes=json.loads((ROOT/'video/storyboard.json').read_text());duration=sum(x['duration'] for x in scenes)
score=np.zeros((duration*SR,2),dtype=np.float32)
def add(x,at,gain=1,pan=0):
 i=int(at*SR);n=min(len(x),len(score)-i)
 if n<=0:return
 angle=(pan+1)*np.pi/4
 score[i:i+n,0]+=x[:n]*(gain*np.cos(angle));score[i:i+n,1]+=x[:n]*(gain*np.sin(angle))
def tone(freq,dur=2,decay=1,soft=.01):
 t=np.arange(int(dur*SR),dtype=np.float32)/SR
 e=np.minimum(1,t/soft)*np.exp(-t/decay)*np.minimum(1,(dur-t)/.09)
 return (np.sin(2*np.pi*freq*t)+.18*np.sin(2*np.pi*freq*2*t))*e
def hz(midi):return 440*2**((midi-69)/12)
def generate():
 beat=.75 # 80 BPM; original arpeggio and harmonic progression.
 chords=[[50,57,62,65],[46,53,58,62],[53,60,65,69],[48,55,60,64]]
 for bar,at in enumerate(np.arange(0,duration,beat*4)):
  chord=chords[bar%4]
  intensity=.55+.35*math.sin(math.pi*min(1,at/duration))
  for j,note in enumerate(chord):add(tone(hz(note),5.5,2.8,.7),at,.035*intensity,(-.4+j*.26))
  for j in range(8):
   note=chord[[0,2,1,3,2,1,3,2][j]]+12
   add(tone(hz(note),2.8,.8,.014),at+j*beat/2,.037*intensity,math.sin(j*1.1)*.55)
  add(tone(hz(chord[0]-12),3.2,1.5,.12),at,.045)
 # A distinct warm bell at each chapter, and small pings exactly on label changes.
 start=0
 for s in scenes:
  if s['id'] in ['title','setup','verify','sync','eda','return']:
   for n in [62,69,74]:add(tone(hz(n),5,1.5,.02),start+.15,.035)
  if s['visual']=='event':
   add(tone(hz(81),.65,.16,.003),start+s['duration']/2,.055,0)
  start+=s['duration']
 # A pause lets the oscillation question breathe; otherwise no abrupt cuts.
 start=sum(s['duration'] for s in scenes[:15]);a=int((start+5)*SR);b=int((start+6.5)*SR)
 envelope=np.ones(len(score),dtype=np.float32)
 envelope[a:b]=.12
 for boundary,left,right in [(a-.4*SR,1,.12),(b-.4*SR,.12,1)]:
  k=int(boundary);envelope[k:k+int(.4*SR)]=np.linspace(left,right,int(.4*SR))
 envelope[:SR*3]*=np.linspace(0,1,SR*3);envelope[-SR*5:]*=np.linspace(1,0,SR*5)
 score[:]*=envelope[:,None]
 peak=float(np.abs(score).max());score[:]*=.72/max(peak,.001)
 wav=ROOT/'build/private/score.wav'
 with wave.open(str(wav),'wb') as f:
  f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes((score*32767).astype('<i2').tobytes())
 return wav
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--music');a=p.parse_args()
 source=Path(a.music) if a.music else generate()
 # Save a small standalone track to make replacing and crediting the music easy.
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),'-t',str(duration),'-c:a','aac','-b:a','160k',str(ROOT/'site/media/between-neighbors.m4a')],check=True)
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(ROOT/'build/private/picture.mp4'),'-i',str(source),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-t',str(duration),'-movflags','+faststart',str(ROOT/'site/media/neighbors.mp4')],check=True)
 print('Finished original score and neighbors.mp4',duration,'seconds')
