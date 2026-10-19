// 24-cell teaching graph for the dark film. Deterministic, fictional, not a real netlist.
// Every number shown on screen comes from running site/algorithm.js on this file.
import fs from 'node:fs/promises';import {GOLDEN,PRESETS,Propagation,metrics,votesFor} from '../site/algorithm.js';
const COLS=6,ROWS=4,id=(r,c)=>`N${String(r*COLS+c).padStart(2,'0')}`;
// Fictional placement: three tightly wired groups that snake across the floorplan.
const groupOf=(r,c)=>r===0||(r===1&&c<2)?0:r===3||(r===2&&c>=4)?2:1;
let seed=5;const rand=()=>(seed=(seed*16807)%2147483647)/2147483647;
const cells=[];for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++)cells.push({id:id(r,c),r,c,g:groupOf(r,c),
  x:Math.round(330+c*252+(rand()-.5)*70),y:Math.round(250+r*165+(rand()-.5)*70)});
const byId=Object.fromEntries(cells.map(n=>[n.id,n]));
// Rename so each group is a consecutive block N00-N07, N08-N15, N16-N23 (reads cleanly on screen).
const ordered=[...cells].sort((a,b)=>a.g-b.g||a.r-b.r||a.c-b.c);
const rename=Object.fromEntries(ordered.map((n,i)=>[n.id,`N${String(i).padStart(2,'0')}`]));
const edges=[],seen=new Set();
const add=(a,b,w)=>{const k=[a,b].sort().join('/');if(a===b||seen.has(k))return;seen.add(k);edges.push([rename[a],rename[b],w]);};
for(const n of cells)for(const m of cells){
  if(n.id>=m.id||n.g!==m.g)continue;const d=Math.abs(n.r-m.r)+Math.abs(n.c-m.c);
  if(d===1)add(n.id,m.id,4+Math.floor(rand()*3));
  else if(d===2)add(n.id,m.id,2+Math.floor(rand()*3));
  else if(d<=4&&n.r!==m.r&&rand()<.6)add(n.id,m.id,1+Math.floor(rand()*2));
}
// Two weak links between groups.
add(id(1,1),id(2,1),1);add(id(2,3),id(3,3),1);
// Readability pass: slide (vertically, so columns stay intact) any cell sitting on a wire it does not belong to.
const P=Object.fromEntries(cells.map(n=>[rename[n.id],n]));
for(let it=0;it<400;it++){let moved=false;
  for(const [u,v] of edges)for(const k of Object.keys(P)){
    if(k===u||k===v)continue;const a=P[u],b=P[v],c=P[k];const dx=b.x-a.x,dy=b.y-a.y,L=dx*dx+dy*dy;
    const t=((c.x-a.x)*dx+(c.y-a.y)*dy)/L;if(t<=0||t>=1)continue;
    const px=a.x+t*dx-c.x,py=a.y+t*dy-c.y,d=Math.hypot(px,py);
    if(d<46){c.y-=(py>0?1:-1)*4;moved=true;}}
  if(!moved)break;}
for(const n of cells){n.x=Math.round(n.x);n.y=Math.round(n.y);}
// Any wire that still runs through a third cell is dropped rather than drawn through it.
const blocked=([u,v])=>Object.keys(P).some(k=>{if(k===u||k===v)return false;const a=P[u],b=P[v],c=P[k];
  const dx=b.x-a.x,dy=b.y-a.y,t=((c.x-a.x)*dx+(c.y-a.y)*dy)/(dx*dx+dy*dy);
  return t>0&&t<1&&Math.hypot(a.x+t*dx-c.x,a.y+t*dy-c.y)<40;});
for(let i=edges.length-1;i>=0;i--)if(blocked(edges[i]))edges.splice(i,1);
const graph={id:'circuit24',name:'虚构电路单元图',nodes:ordered.map(n=>rename[n.id]),edges,
  positions:Object.fromEntries(cells.map(n=>[rename[n.id],[n.x,n.y]]))};
// Comparison partition by position only: the 8 leftmost, 8 middle and 8 rightmost cells.
const byX=[...cells].sort((a,b)=>a.x-b.x);
const geoLabels=Object.fromEntries(byX.map((n,i)=>[rename[n.id],['L','M','R'][Math.floor(i/8)]]));
console.log('column gaps',byX[8].x-byX[7].x,byX[16].x-byX[15].x);
const lp=new Propagation(graph).run();
const golden=new Propagation(GOLDEN).run();
const withWeight=(g,u,v,w)=>({...g,edges:g.edges.map(e=>(e[0]===u&&e[1]===v)?[u,v,w]:e)});
const tie=PRESETS.tie,tieLabels={A:'A',B:'B',C:'B',D:'D'};
const extra={
  reverse:new Propagation(GOLDEN,{order:[...GOLDEN.nodes].reverse()}).run(),
  pairSync:new Propagation(PRESETS.pair,{mode:'sync',maxRounds:6}).run(),
  pairAsync:new Propagation(PRESETS.pair).run(),
  weightVote:{graph:tie,labels:tieLabels,...votesFor(tie,tieLabels,'A')},
  strongCD:new Propagation(withWeight(GOLDEN,'C','D',10)).run(),
  island:new Propagation(PRESETS.island).run(),islandGraph:PRESETS.island};
const out={graph,geometric:{labels:geoLabels,metrics:metrics(graph,geoLabels)},lp,
  initialCut:metrics(graph,Object.fromEntries(graph.nodes.map(n=>[n,n]))).cut,golden,...extra};
await fs.writeFile(new URL('../data/film-v3.json',import.meta.url),JSON.stringify(out));
console.log({nodes:graph.nodes.length,edges:edges.length,total:out.geometric.metrics.totalWeight,
  geoCut:out.geometric.metrics.cut,lpCut:lp.metrics.cut,lpRounds:lp.rounds,status:lp.status,
  groups:Object.entries(lp.metrics.clusters).map(([k,v])=>k+':'+v.join(','))});
console.log('reverse',extra.reverse.rounds,extra.reverse.labels,'pairSync',extra.pairSync.status,extra.pairSync.rounds,
  'pairAsync',extra.pairAsync.labels,'vote',extra.weightVote.votes,'strongCD',extra.strongCD.labels,extra.strongCD.metrics.cut,
  'island',extra.island.labels);
