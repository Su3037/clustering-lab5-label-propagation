#!/usr/bin/env python3
"""Measure an actual soundtrack; no nominal BPM or invented beat times.

FFmpeg decodes a supplied local audio file. Positive spectral flux and kick-band
energy propose a grid; JSON retains both measured onsets and the fitted grid.
Grid is an editing aid, not a claim of manually annotated musical downbeats.
"""
import argparse, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def analyze(source, destination):
    rate, hop, nfft = 22050, 220, 2048
    raw = subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-ac','1','-ar',str(rate),'-f','f32le','-'])
    audio = np.frombuffer(raw, dtype='<f4')
    frames = np.lib.stride_tricks.sliding_window_view(audio, nfft)[::hop]
    spec = np.abs(np.fft.rfft(frames*np.hanning(nfft), axis=1))
    bands = (spec[:,3:20]**2).mean(axis=1)**.5
    flux = np.maximum(0, np.diff(np.log1p(spec),axis=0)).mean(axis=1)
    flux = np.r_[0,flux]
    base=np.convolve(flux,np.ones(101)/101,'same')
    onset=np.maximum(0,flux-base*.8)
    env=onset/(np.percentile(onset,95)+1e-9)
    dt=hop/rate
    # Score periodicity over the whole file, preferring energetic positive onsets.
    candidates=[]
    for bpm in np.arange(85,145,.025):
        lag=60/bpm/dt
        lag0=int(lag)
        corr=sum(np.mean(env[:-int(round(lag*k))]*env[int(round(lag*k)):])/(k**.5) for k in (1,2,4))
        candidates.append((corr,float(bpm)))
    _,bpm=max(candidates)
    period=60/bpm
    times=np.arange(len(env))*dt+nfft/2/rate
    offsets=np.arange(0,period,.001)
    scores=[]
    for offset in offsets:
        bt=np.arange(offset,times[-1],period)
        scores.append(np.interp(bt,times,env).mean())
    offset=float(offsets[int(np.argmax(scores))])
    grid=np.arange(offset,len(audio)/rate,period)
    # Local maxima kept separately from the regular grid (which can drift).
    peaks=np.where((env[1:-1]>env[:-2])&(env[1:-1]>=env[2:])&(env[1:-1]>.8))[0]+1
    measured=[]
    for i in peaks:
        t=float(times[i])
        if measured and t-measured[-1]['time']<.18:
            if env[i]>measured[-1]['strength']:measured[-1]={'time':round(t,4),'strength':round(float(env[i]),3)}
        else:measured.append({'time':round(t,4),'strength':round(float(env[i]),3)})
    energy=[]
    for i in range(int(len(audio)/rate)+1):
        block=audio[i*rate:(i+1)*rate]
        if len(block):energy.append(round(float(np.sqrt(np.mean(block**2))),5))
    obj={'source':Path(source).name,'duration':len(audio)/rate,'bpm_estimate':round(bpm,3),
         'period':period,'phase':offset,'grid':[round(float(t),4) for t in grid],
         'onsets':measured,'rms_1s':energy,'method':'positive spectral flux; autocorrelation + grid phase fit; not manually annotated downbeats'}
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(obj,ensure_ascii=False,indent=2))
    canvas=Image.new('RGB',(1600,430),'#101a21');d=ImageDraw.Draw(canvas)
    for i,rms in enumerate(energy):
        x=round(35+i/obj['duration']*1530);d.line((x,325,x,325-rms*850),fill='#7ac9b4',width=5)
    for t in grid:
        x=35+t/obj['duration']*1530;d.line((x,60,x,90),fill='#dbbc7c')
    for t in range(0,190,5):
        x=35+t/obj['duration']*1530;d.line((x,95,x,340),fill='#263b45');d.text((x,350),str(t),fill='white')
    d.text((35,20),f'Actual music: {obj["duration"]:.3f}s / estimated {bpm:.3f} BPM',fill='white')
    canvas.save(destination.with_suffix('.png'))
    print(json.dumps({'duration':obj['duration'],'bpm_estimate':obj['bpm_estimate'],'phase':offset,'strong_onsets':len(measured),'rms_1s':energy},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('audio',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();analyze(a.audio,a.output)
