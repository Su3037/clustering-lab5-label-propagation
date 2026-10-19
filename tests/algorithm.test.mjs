import test from 'node:test';import assert from 'node:assert/strict';
import {GOLDEN,PRESETS,Propagation,metrics,votesFor,chooseLabel,validateGraph} from '../site/algorithm.js';
test('教师 golden：含零变化确认轮，cut 为加权和',()=>{
 const r=new Propagation(GOLDEN).run();assert.equal(r.rounds,2);assert.equal(r.status,'stable');
 assert.deepEqual(r.labels,{A:'B',B:'B',C:'B',D:'E',E:'E'});assert.equal(r.metrics.cut,3);assert.deepEqual(r.metrics.sizes,[3,2]);
 assert.deepEqual(r.events.slice(0,5).map(e=>e.label),['B','B','B','E','E']);assert.equal(r.events[4].changes,3);assert.equal(r.events[9].changes,0);
 assert.deepEqual(r.events[2].votes,{B:5,D:2,E:1});assert.equal(r.metrics.cutEdges.length,2);
});
test('异步马上可见，同步读旧快照、末尾统一提交',()=>{
 const a=new Propagation(PRESETS.pair),s=new Propagation(PRESETS.pair,{mode:'sync'});
 assert.deepEqual(a.step().labels,{A:'B',B:'B'});assert.deepEqual(s.step().labels,{A:'A',B:'B'});
 assert.deepEqual(s.step().labels,{A:'B',B:'A'});assert.equal(s.history[0].committed,false);
 assert.equal(a.run().status,'stable');const r=s.run();assert.equal(r.status,'cycle');assert.equal(r.rounds,2);assert.equal(r.events.at(-1).period,2);
});
test('票数按权重而非邻居数量，平票可复现',()=>{
 const labels=Object.fromEntries(PRESETS.tie.nodes.map(n=>[n,n]));labels.C='B';
 const {votes}=votesFor(PRESETS.tie,labels,'A');assert.deepEqual(votes,{B:2,D:4});assert.equal(chooseLabel(votes,'A'),'D');
 assert.equal(chooseLabel({B:2,C:2},'A'),'B');assert.equal(chooseLabel({B:2,C:2},'A','max'),'C');assert.equal(chooseLabel({B:2,C:2},'C','keep'),'C');
});
test('孤点保留标签，无边图一轮确认',()=>{
 assert.equal(new Propagation(PRESETS.island).run().labels.E,'E');
 const r=new Propagation({nodes:['A'],edges:[]}).run();assert.equal(r.rounds,1);assert.equal(r.status,'stable');assert.equal(r.metrics.cut,0);
});
test('标签名称改变不等于分区改变',()=>{
 const a=new Propagation(GOLDEN).run(),b=new Propagation(GOLDEN,{order:[...GOLDEN.nodes].reverse()}).run();
 assert.notDeepEqual(a.labels,b.labels);assert.deepEqual(Object.values(a.metrics.clusters).sort(),Object.values(b.metrics.clusters).sort());assert.equal(b.rounds,3);
});
test('max rounds 与 stable 明确区分',()=>{const r=new Propagation(GOLDEN,{maxRounds:1}).run();assert.equal(r.status,'limit');assert.equal(r.rounds,1);});
test('输入边界和独立实例',()=>{
 assert.throws(()=>new Propagation(GOLDEN,{order:['A']}));assert.throws(()=>validateGraph({nodes:['A','B'],edges:[['A','B',0]]}));
 assert.throws(()=>validateGraph({nodes:['A'],edges:[['A','A',1]]}));assert.throws(()=>validateGraph({nodes:['A','B'],edges:[['A','B',1],['B','A',1]]}));
 const a=new Propagation(GOLDEN);a.run();const b=new Propagation(GOLDEN);assert.equal(b.labels.A,'A');assert.equal(GOLDEN.edges[0][2],5);
});
test('合法标签名与对象原型关键字不冲突',()=>{
 const g={nodes:['constructor','toString'],edges:[['constructor','toString',2]]};
 const r=new Propagation(g).run();assert.equal(r.status,'stable');assert.equal(r.metrics.count,1);assert.equal(r.metrics.cut,0);
});
