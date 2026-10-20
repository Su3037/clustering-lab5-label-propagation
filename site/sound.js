// Tiny synthesized cues. Off by default; the choice is remembered in this browser only.
const KEY='lp-sound';
let on=false,ctx=null;
try{on=localStorage.getItem(KEY)==='on';}catch{}
function tone(freqs,dur=.09,gap=.07,type='sine',vol=.06){
  if(!on)return;try{ctx=ctx||new AudioContext();const t0=ctx.currentTime;
    freqs.forEach((f,i)=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.value=f;
      const t=t0+i*gap;g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vol,t+.01);g.gain.exponentialRampToValueAtTime(.0001,t+dur);
      o.connect(g).connect(ctx.destination);o.start(t);o.stop(t+dur+.02);});}catch{}
}
export const sound={
  get on(){return on;},
  set(v){on=v;try{localStorage.setItem(KEY,v?'on':'off');}catch{}if(v)tone([660,880]);},
  tick:()=>tone([520],.05,0,'triangle',.035),
  ok:()=>tone([660,880],.1),
  miss:()=>tone([300,240],.12,.09,'triangle',.05),
  win:()=>tone([523,659,784,1047],.16,.09)
};
const btn=document.querySelector('#sound-toggle');
if(btn){const paint=()=>{btn.textContent=on?'音效 开':'音效 关';btn.setAttribute('aria-pressed',String(on));};
  btn.addEventListener('click',()=>{sound.set(!on);paint();});paint();}
