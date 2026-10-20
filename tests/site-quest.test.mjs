import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {GOLDEN,PRESETS,Propagation,metrics,votesFor,chooseLabel} from '../site/algorithm.js';
import {CONTACTS,CHIP} from '../site/film-graphs.js';
const data=JSON.parse(fs.readFileSync(new URL('../data/film-v3.json',import.meta.url)));
test('site graphs match the film data and stay inside the drawing box',()=>{
  assert.deepEqual(CONTACTS.edges,data.social.graph.edges);assert.deepEqual(CHIP.edges,data.graph.edges);
  for(const g of [CONTACTS,CHIP])for(const[x,y]of Object.values(g.positions)){assert.ok(x>=30&&x<=710&&y>=30&&y<=500);}
});
test('film numbers reproduce on the site graphs',()=>{
  const c=new Propagation(CONTACTS).run(),k=new Propagation(CHIP).run();
  assert.equal(c.rounds,3);assert.equal(c.metrics.cut,4);assert.equal(k.rounds,5);assert.equal(k.metrics.cut,2);
  assert.deepEqual(k.metrics.sizes,[8,8,8]);assert.equal(metrics(CHIP,CHIP.ruler).cut,88);assert.equal(metrics(CHIP,CHIP.ruler).totalWeight,202);
});
test('quest answers the levels compute live',()=>{
  const tie=w=>({...PRESETS.tie,edges:PRESETS.tie.edges.map(e=>e[1]==='D'?['A','D',w]:e)}),labels={A:'A',B:'B',C:'B',D:'D'};
  assert.equal(chooseLabel(votesFor(tie(2),labels,'A').votes,'A'),'B');assert.equal(chooseLabel(votesFor(tie(3),labels,'A').votes,'A'),'D');
  const p=new Propagation(GOLDEN);p.step();p.step();assert.deepEqual(votesFor(GOLDEN,p.labels,'C').votes,{B:5,D:2,E:1});
  const r1=new Propagation(GOLDEN);while(r1.round<1)r1.step();assert.deepEqual(r1.labels,{A:'B',B:'B',C:'B',D:'E',E:'E'});
  assert.equal(new Propagation(PRESETS.pair,{mode:'sync',maxRounds:6}).run().status,'cycle');
  const cd=w=>new Propagation({...GOLDEN,edges:GOLDEN.edges.map(e=>e[0]==='C'&&e[1]==='D'?['C','D',w]:e)}).run().labels;
  const min=[1,2,3,4,5,6,7,8,9,10,11,12].find(w=>cd(w).C===cd(w).D);assert.equal(min,5);assert.equal(cd(10).C,cd(10).E);assert.notEqual(cd(10).C,cd(10).A);
});
