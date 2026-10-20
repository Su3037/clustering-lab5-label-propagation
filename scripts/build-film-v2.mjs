import fs from 'node:fs/promises';
import { GOLDEN, PRESETS, Propagation, votesFor, metrics } from '../site/algorithm.js';

// Three dense fictional neighborhoods, with two weak bridges. Every visible
// label change in the wide shot is produced by the classroom engine.
const nodes=Array.from({length:24},(_,i)=>`N${String(i).padStart(2,'0')}`);
const edges=[];
for(let g=0;g<3;g++) for(let i=0;i<8;i++) for(let j=i+1;j<8;j++)
  edges.push([nodes[g*8+i],nodes[g*8+j],3+(i+j)%3]);
edges.push([nodes[6],nodes[8],1],[nodes[14],nodes[16],1]);
const city={id:'film-city',nodes,edges};
const star={nodes:['S','U','V','W'],edges:[['S','U',1],['S','V',1],['S','W',4]]};
const labels={S:'S',U:'B',V:'B',W:'D'};
const strong=structuredClone(GOLDEN);strong.edges.find(([u,v])=>u==='C'&&v==='D')[2]=10;
const weak=structuredClone(GOLDEN);weak.edges=weak.edges.filter(([u,v])=>!(u==='C'&&v==='D'));
const result={golden:new Propagation(GOLDEN).run(),reverse:new Propagation(GOLDEN,{order:[...GOLDEN.nodes].reverse()}).run(),
  pairSync:new Propagation(PRESETS.pair,{mode:'sync'}).run(),pairAsync:new Propagation(PRESETS.pair).run(),
  strong:new Propagation(strong).run(),weak:new Propagation(weak).run(),limit:new Propagation(GOLDEN,{maxRounds:1}).run(),cityGraph:city,city:new Propagation(city).run(),
  weightExample:{graph:star,labels,...votesFor(star,labels,'S')},goldenGraph:GOLDEN};
result.circuitPositions=Object.fromEntries(nodes.map((n,i)=>{const slot=i*7%24;return[n,[280+slot%6*144,236+Math.floor(slot/6)*88]]}));
result.geometricLabels=Object.fromEntries(nodes.map(n=>[n,'region'+Math.floor((result.circuitPositions[n][0]-280)/288)]));
result.geometricMetrics=metrics(city,result.geometricLabels);
if(result.city.metrics.count!==3)throw Error('Wide shot changed: inspect actual grouping');
await fs.writeFile(new URL('../data/film-v2.json',import.meta.url),JSON.stringify(result,null,2));
console.log('Film traces verified:',result.city.metrics.count,'groups;',result.city.rounds,'rounds;',result.city.metrics.cut,'weighted cut.');
