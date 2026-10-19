"""Compare separately implemented Python/JS engines on seeded graphs and rules."""
import json,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from label_propagation import solve
rng=random.Random(20261020);cases=[]
golden=json.loads((ROOT/'data/traces.json').read_text())['graphs']['golden']
for index in range(45):
    nodes=[chr(65+j) for j in range(rng.randint(1,8))]
    edges=[[u,v,rng.randint(1,8)] for i,u in enumerate(nodes) for v in nodes[i+1:] if rng.random()<.42]
    g={'nodes':nodes,'edges':edges}
    for mode in ['async','sync']:
        for tie in ['min','max','keep']:
            order=nodes.copy();rng.shuffle(order);cases.append({'g':g,'o':{'mode':mode,'tie':tie,'order':order,'maxRounds':50}})
cases.append({'g':golden,'o':{'mode':'async','tie':'min','order':golden['nodes'],'maxRounds':50}})
script="import fs from 'node:fs';import{Propagation}from './site/algorithm.js';let a=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(a.map(x=>new Propagation(x.g,x.o).run())));"
p=subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,input=json.dumps(cases),text=True,capture_output=True,check=True)
actual=json.loads(p.stdout)
for index,(case,js) in enumerate(zip(cases,actual)):
    o=case['o'];g=case['g'];py=solve(g['nodes'],g['edges'],mode=o['mode'],tie=o['tie'],order=o['order'],max_iters=o['maxRounds'])
    for field in ['labels','rounds','status']:assert py[field]==js[field],(index,field,py,js)
    assert py['cut']==js['metrics']['cut'],index
    assert len(py['events'])==len(js['events']),index
    for a,b in zip(py['events'],js['events']):
        for k in ['round','node','old','label','votes']:assert a[k]==b[k],(index,k)
assert actual[-1]['rounds']==2 and actual[-1]['metrics']['cut']==3
print(f'PASS: {len(cases)} seeded cross-checks, including all node-level votes, stop reasons and golden.')
