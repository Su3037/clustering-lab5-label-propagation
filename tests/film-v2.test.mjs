import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { Propagation } from '../site/algorithm.js';
const read=p=>JSON.parse(fs.readFileSync(new URL(p,import.meta.url)));

test('film wide shot and counterfactual retain actual executable results',()=>{
  const film=read('../data/film-v2.json');
  assert.deepEqual(new Propagation(film.cityGraph).run(),film.city);
  assert.equal(film.city.metrics.count,3);
  assert.equal(film.city.metrics.cut,2);
  const changed=structuredClone(film.goldenGraph);
  changed.edges.find(([u,v])=>u==='C'&&v==='D')[2]=10;
  assert.deepEqual(new Propagation(changed).run(),film.strong);
  assert.deepEqual(film.golden.events[2].votes,{B:5,D:2,E:1});
});

test('film has continuous coverage and actions aligned to measured music cues',()=>{
  const film=read('../video/storyboard-v2.json'),music=read('../video/music-cues-v2.json');
  assert.equal(film.music.speed,1);
  assert.equal(film.scenes[0].start,0);
  for(let i=0;i<film.scenes.length;i++){
    const s=film.scenes[i],end=s.start+s.duration;
    assert.ok(s.duration>2);
    assert.ok(Math.abs(end-(film.scenes[i+1]?.start??film.duration))<1e-6);
    for(const at of s.actions){
      assert.ok(at>0&&at<s.duration);
      const t=s.start+at;
      const error=Math.min(...music.onsets.map(o=>Math.abs(t-o.time)),...music.grid.map(v=>Math.abs(t-v)));
      assert.ok(error<=1/60+1e-4,`action ${s.id} at ${t} drifted ${error}`);
    }
  }
});
