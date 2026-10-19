import fs from 'node:fs/promises';import {GOLDEN,PRESETS,Propagation} from '../site/algorithm.js';
const traces={golden:new Propagation(GOLDEN).run(),reverse:new Propagation(GOLDEN,{order:[...GOLDEN.nodes].reverse()}).run(),pairSync:new Propagation(PRESETS.pair,{mode:'sync'}).run(),graphs:PRESETS};
await fs.writeFile(new URL('../data/traces.json',import.meta.url),JSON.stringify(traces,null,2));
console.log('真实运行生成 traces.json：golden',traces.golden.rounds,traces.golden.metrics.cut);
