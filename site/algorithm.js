/** Original, deterministic teaching implementation. Undirected, positive weighted simple graphs. */
export const GOLDEN = {
  id:'golden', name:'教师五节点图', nodes:['A','B','C','D','E'],
  edges:[['A','B',5],['A','C',1],['B','C',4],['C','D',2],['D','E',5],['C','E',1]],
  positions:{A:[170,100],B:[390,85],C:[305,270],D:[530,375],E:[280,440]}
};
export const PRESETS = {
  golden:GOLDEN,
  pair:{id:'pair',name:'两节点振荡',nodes:['A','B'],edges:[['A','B',1]],positions:{A:[200,240],B:[510,240]}},
  tie:{id:'tie',name:'一票还是两票？',nodes:['A','B','C','D'],edges:[['A','B',1],['A','C',1],['A','D',4]],positions:{A:[350,240],B:[150,100],C:[150,380],D:[600,240]}},
  island:{id:'island',name:'孤点与断开的群体',nodes:['A','B','C','D','E'],edges:[['A','B',3],['C','D',2]],positions:{A:[150,130],B:[310,130],C:[150,380],D:[310,380],E:[600,250]}}
};
export function validateGraph(graph) {
  if(!graph || !Array.isArray(graph.nodes) || !Array.isArray(graph.edges)) throw Error('需要 nodes 与 edges 数组');
  const {nodes,edges}=graph;
  if(nodes.length<1 || nodes.length>30 || new Set(nodes).size!==nodes.length) throw Error('节点须唯一，数量为 1–30');
  if(nodes.some(n=>typeof n!=='string'||!/^[A-Za-z][A-Za-z0-9_]{0,11}$/.test(n))) throw Error('节点用字母开头的短名称');
  if(edges.length>200) throw Error('边数不能超过 200');
  const seen=new Set();
  for(const e of edges){
    if(!Array.isArray(e)||e.length!==3) throw Error('边格式为 [节点,节点,正权重]');
    const [u,v,w]=e,key=[u,v].sort().join('/');
    if(!nodes.includes(u)||!nodes.includes(v)||u===v) throw Error('边须连接两个不同的已有节点');
    if(!Number.isFinite(w)||w<=0||w>1e6) throw Error('权重须为有限正数，不超过 1000000');
    if(seen.has(key)) throw Error('不支持重边，请先合并权重');
    seen.add(key);
  }
  return graph;
}
export function metrics(graph,labels) {
  const clusters={};for(const n of graph.nodes){const label=labels[n];if(!Object.hasOwn(clusters,label))clusters[label]=[];clusters[label].push(n);}
  const cutEdges=graph.edges.filter(([u,v])=>labels[u]!==labels[v]);
  return {clusters,count:Object.keys(clusters).length,cut:cutEdges.reduce((s,e)=>s+e[2],0),cutEdges,
    sizes:Object.values(clusters).map(a=>a.length).sort((a,b)=>b-a),totalWeight:graph.edges.reduce((s,e)=>s+e[2],0)};
}
export function votesFor(graph,labels,node) {
  const votes={},neighbors=[];
  for(const [u,v,w] of graph.edges){
    const n=u===node?v:v===node?u:null;if(n===null)continue;
    const label=labels[n];votes[label]=(Object.hasOwn(votes,label)?votes[label]:0)+w;neighbors.push({node:n,label,weight:w});
  }
  return {votes,neighbors};
}
export function chooseLabel(votes,current,tie='min') {
  const entries=Object.entries(votes);if(!entries.length)return current;
  const max=Math.max(...entries.map(x=>x[1]));
  const tied=entries.filter(x=>Math.abs(x[1]-max)<1e-12).map(x=>x[0]).sort();
  if(tie==='keep'&&tied.includes(current))return current;
  return tie==='max'?tied.at(-1):tied[0];
}
export class Propagation {
  constructor(graph,{mode='async',order=null,tie='min',maxRounds=50}={}){
    validateGraph(graph);this.graph=structuredClone(graph);
    if(!['async','sync'].includes(mode)||!['min','max','keep'].includes(tie))throw Error('未知更新或平票规则');
    this.order=order??[...graph.nodes].sort();
    if(this.order.length!==graph.nodes.length||new Set(this.order).size!==graph.nodes.length||this.order.some(n=>!graph.nodes.includes(n)))throw Error('访问顺序须恰好包含每个节点一次');
    if(!Number.isInteger(maxRounds)||maxRounds<1||maxRounds>200)throw Error('最大轮数为 1–200');
    this.mode=mode;this.tie=tie;this.maxRounds=maxRounds;
    this.labels=Object.fromEntries(graph.nodes.map(n=>[n,n]));this.round=0;this.index=0;
    this.status='running';this.history=[];this.seen=new Map([[this.signature(this.labels),0]]);
    this.base={...this.labels};this.pending={...this.labels};this.roundChanges=0;
  }
  signature(labels){return this.graph.nodes.map(n=>labels[n]).join('|');}
  step(){
    if(this.status!=='running')return null;
    const node=this.order[this.index], before={...this.labels};
    const source=this.mode==='sync'?this.base:this.labels;
    const {votes,neighbors}=votesFor(this.graph,source,node);
    const old=source[node],label=chooseLabel(votes,old,this.tie),changed=label!==old;
    this.pending[node]=label;if(this.mode==='async')this.labels[node]=label;
    if(changed)this.roundChanges++;
    const event={round:this.round+1,index:this.index,node,old,label,changed,votes,neighbors,before,
      pending:{...this.pending},roundEnd:false,committed:this.mode==='async',mode:this.mode,tie:this.tie};
    this.index++;
    if(this.index===this.order.length){
      if(this.mode==='sync')this.labels={...this.pending};
      this.round++;event.roundEnd=true;event.committed=true;event.changes=this.roundChanges;
      const signature=this.signature(this.labels);
      if(this.roundChanges===0)this.status='stable';
      else if(this.seen.has(signature)){this.status='cycle';event.cycleStart=this.seen.get(signature);event.period=this.round-this.seen.get(signature);}
      else if(this.round>=this.maxRounds)this.status='limit';
      this.seen.set(signature,this.round);
      this.index=0;this.roundChanges=0;this.base={...this.labels};this.pending={...this.labels};
    }
    event.labels={...this.labels};event.status=this.status;event.metrics=metrics(this.graph,this.labels);
    this.history.push(event);return event;
  }
  run(){while(this.status==='running')this.step();return this.result();}
  result(){return {mode:this.mode,tie:this.tie,order:this.order,labels:{...this.labels},rounds:this.round,status:this.status,metrics:metrics(this.graph,this.labels),events:this.history};}
}
