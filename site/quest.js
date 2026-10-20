// 闯关实验：九层讲解对应九关，外加序章与终章两场 Boss。
// 每一关的“正确答案”都在浏览器里用 algorithm.js 现场计算，不写死结果。
import {GOLDEN,PRESETS,Propagation,metrics,votesFor,chooseLabel} from './algorithm.js?v=20261020c';
import {CONTACTS,CHIP} from './film-graphs.js?v=20261020c';
import {sound} from './sound.js?v=20261020c';

const $=s=>document.querySelector(s),NS='http://www.w3.org/2000/svg';
const KEY='lp-quest-v1';
const BRUSH=['#0f7966','#a57a20','#315cba'];
const LABEL_COL=['#a57a20','#0f7966','#b76529','#315cba','#a44170','#8051a0','#397f85','#84672e'];
let save={done:{},best:{}};
try{const s=JSON.parse(localStorage.getItem(KEY)||'null');if(s&&typeof s==='object')save={done:s.done||{},best:s.best||{}};}catch{}
const persist=()=>{try{localStorage.setItem(KEY,JSON.stringify(save));}catch{}};

// ---------------------------------------------------------------- small helpers
function el(tag,attrs={},...kids){
  const e=tag==='svg'||['g','line','circle','text','rect','path'].includes(tag)?document.createElementNS(NS,tag):document.createElement(tag);
  for(const[k,v]of Object.entries(attrs)){if(k==='on')for(const[ev,fn]of Object.entries(v))e.addEventListener(ev,fn);else if(v!==false&&v!=null)e.setAttribute(k,String(v));}
  for(const k of kids)if(k!=null)e.append(k);return e;
}
// Small graphs colour a label by its node; big ones by the label's rank among labels shown, so groups never share a colour.
let rank=null;const labelColor=(g,l)=>(g.nodes.length>12&&rank?.has(l)?LABEL_COL[[0,1,3,4,5,2,6,7][rank.get(l)%8]]:LABEL_COL[Math.max(0,g.nodes.indexOf(l))%LABEL_COL.length]);
const ranked=(g,labels)=>{rank=new Map([...new Set(g.nodes.map(n=>labels[n]))].sort().map((x,i)=>[x,i]));};
const show=n=>n.replace(/^P\d\d$/,m=>CONTACTS.names[m]||m);
const runFull=(g,o={})=>new Propagation(g,o).run();
function afterRound(g,k,o={}){const p=new Propagation(g,o);while(p.status==='running'&&p.round<k)p.step();return p;}
function withEdge(g,u,v,w){const edges=g.edges.filter(e=>!((e[0]===u&&e[1]===v)||(e[0]===v&&e[1]===u)));if(w>0)edges.push([u,v,w]);return {...structuredClone(g),edges};}
const sameGroups=(a,b,nodes)=>nodes.every(x=>nodes.every(y=>(a[x]===a[y])===(b[x]===b[y])));

/** Draws a graph. opts: colors(n), sub(n), onNode(n), onEdge(e,i), edgeStyle(e,i), small, names */
function drawGraph(svg,g,opts={}){
  svg.replaceChildren();const pos=opts.pos||g.positions,small=opts.small??g.nodes.length>8,r=small?12:27;
  g.edges.forEach((e,i)=>{
    const[u,v,w]=e,a=pos[u],b=pos[v],st=opts.edgeStyle?.(e,i)||{};
    const line=el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:st.stroke||'#9fb9ad','stroke-width':st.width||(small?.6+w*.45:1.3+Math.min(w,10)*.45),'stroke-opacity':st.opacity??(small?.75:1),class:'q-edge'});
    svg.append(line);
    if(opts.onEdge){const hit=el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'transparent','stroke-width':18,class:'q-hit',tabindex:0,role:'button','aria-label':`边 ${show(u)}—${show(v)}，权重 ${w}`,
      on:{click:()=>opts.onEdge(e,i),keydown:ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();opts.onEdge(e,i);}}}});svg.append(hit);}
    if(!small){const mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2;svg.append(el('circle',{cx:mx,cy:my,r:13,fill:'#fffdf8','pointer-events':'none'}),el('text',{x:mx,y:my+5,'text-anchor':'middle',fill:'#607065','font-size':15,'pointer-events':'none'},String(w)));}
  });
  for(const n of g.nodes){
    const[x,y]=pos[n],col=opts.colors?.(n)||'#8a9a90',grp=el('g',{class:'q-node'+(opts.onNode?' clickable':''),...(opts.onNode?{tabindex:0,role:'button','aria-label':opts.aria?.(n)||`节点 ${show(n)}`}:{})});
    if(opts.onNode){grp.addEventListener('click',()=>opts.onNode(n));grp.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();opts.onNode(n);}});}
    if(opts.ring?.(n))grp.append(el('circle',{cx:x,cy:y,r:r+8,fill:'none',stroke:'#b58c35','stroke-width':2,class:'q-pulse'}));
    grp.append(el('circle',{cx:x,cy:y,r,fill:opts.fill?.(n)||'#fffdf8',stroke:col,'stroke-width':small?3:3.2}));
    if(small)grp.append(el('text',{x,y:y-17,'text-anchor':'middle','font-size':13,fill:'#33433b'},show(n)));
    else grp.append(el('text',{x,y:y+8,'text-anchor':'middle','font-size':24,'font-weight':600,fill:'#273b32'},n));
    const sub=opts.sub?.(n);if(sub)grp.append(el('text',{x,y:y+(small?28:50),'text-anchor':'middle','font-size':small?11:15,fill:col},sub));
    svg.append(grp);
  }
}
function voteBars(votes,g){
  const max=Math.max(1,...Object.values(votes)),box=el('div',{class:'q-votes'});
  for(const[l,w]of Object.entries(votes).sort()){const bar=el('span',{class:'q-bar',style:`width:${w/max*140}px;background:${labelColor(g,l)}`});box.append(el('div',{},el('span',{},'标签 '+l),bar,el('strong',{},String(w))));}
  if(!Object.keys(votes).length)box.textContent='没有邻居。';return box;
}

// ---------------------------------------------------------------- levels
// Each level builds its own stage and returns {check():{ok,msg,best?}}.
const LEVELS=[
 {id:'p0',region:0,boss:true,title:'序章 Boss · 给通讯录分圈',film:0,xp:200,
  story:'28 个联系人，连线越粗，联系越频繁。用三支画笔把每个人分进一个圈子，让被切开的联系尽量少。',
  task:'给 28 人全部上色，用满 3 个圈子，被切开的联系权重 ≤ 12 即通关。',
  hints:['先找最粗的线：粗线两端的人几乎一定在同一个圈子。','从“妈妈”“阿杰”“王经理”三个人出发，沿着粗线把同色向外扩。'],
  build:ctx=>paintLevel(ctx,CONTACTS,{limit:12,groups:3,minSize:1})},
 {id:'l1',region:1,title:'第 1 关 · 名字与标签',film:189.82,xp:100,
  story:'在老师的五节点图上，每个点一开始都拿自己的名字当标签。名字是身份，永远不变；标签是归属，可以改写。',
  task:'按 A→E 异步更新一整轮。第一轮结束时，点 C 的名字和标签分别是什么？',
  hints:['名字不会变，只有标签会变。','C 的邻居里，A 和 B 在 C 之前已经改成了 B。'],
  build:ctx=>{
    const p=afterRound(GOLDEN,1),lab=p.labels.C;drawGraph(ctx.svg,GOLDEN,{colors:n=>labelColor(GOLDEN,n),sub:n=>'标签 '+n});
    ctx.note('图上是开始时的状态：每个点的标签等于名字。');
    const opts=[`名字 C，标签 ${lab}`,`名字 ${lab}，标签 ${lab}`,'名字 C，标签 C'];
    return choiceCheck(ctx,opts,0,`对。C 的名字不变，标签改写为 ${lab}。`);
  }},
 {id:'l2',region:1,title:'第 2 关 · 怎样算“最强”',film:207.23,xp:100,
  story:'A 有三个邻居：B、C 带着标签 B，D 带着标签 D。数人头，B 两票；加权重，结果可能不一样。',
  task:'拖动 A—D 的权重，让 A 最终选择标签 B。',
  hints:['同标签的边权要相加：B 的总分是 1 + 1。','平票时课堂规则取字典序最小的标签，B 比 D 小。'],
  build:ctx=>{
    const labels={A:'A',B:'B',C:'B',D:'D'};let w=4;
    const slider=el('input',{type:'range',min:1,max:8,value:w,'aria-label':'A—D 的权重'}),out=el('output',{},String(w)),info=el('div',{});
    const draw=()=>{const g=withEdge(PRESETS.tie,'A','D',w),{votes}=votesFor(g,labels,'A'),pick=chooseLabel(votes,'A','min');
      drawGraph(ctx.svg,g,{colors:n=>labelColor(GOLDEN,labels[n]),sub:n=>'标签 '+labels[n],ring:n=>n==='A'});
      info.replaceChildren(voteBars(votes,GOLDEN),el('p',{class:'q-pick'},`A 现在会选：标签 ${pick}`));ctx.state.pick=pick;};
    slider.addEventListener('input',()=>{w=Number(slider.value);out.textContent=w;draw();sound.tick();});
    ctx.controls.append(el('label',{class:'q-slider'},'A—D 的权重 ',out,slider),info);draw();
    return {check:()=>ctx.state.pick==='B'?{ok:true,msg:`对。B 的总分 2，D 的总分 ${w}${w===2?'，平票取较小的 B':''}。权重比人数更重要。`}:{ok:false,msg:'A 还在选 D。D 这一票太重了。'}};
  }},
 {id:'l3',region:1,title:'第 3 关 · 一次更新',film:227.44,xp:100,
  story:'轮到 C 更新。它不看全局，只看邻居们此刻的标签，把同标签的边权加起来。',
  task:'A、B 已经改成 B。算出 C 此刻读到的各标签总分。',
  hints:['C 的邻居：A(1)、B(4)、D(2)、E(1)。','A 和 B 都带 B：1 + 4。'],
  build:ctx=>{
    const p=new Propagation(GOLDEN);p.step();p.step();const lab={...p.labels},{votes}=votesFor(GOLDEN,lab,'C');
    drawGraph(ctx.svg,GOLDEN,{colors:n=>labelColor(GOLDEN,lab[n]),sub:n=>'标签 '+lab[n],ring:n=>n==='C'});
    const inputs={};const row=el('div',{class:'q-inputs'});
    for(const l of Object.keys(votes).sort()){inputs[l]=el('input',{type:'number',min:0,max:20,inputmode:'numeric','aria-label':'标签 '+l+' 的总分'});row.append(el('label',{},'标签 '+l+' ',inputs[l]));}
    ctx.controls.append(row);
    return {check:()=>{const bad=Object.keys(votes).filter(l=>Number(inputs[l].value)!==votes[l]);
      return bad.length?{ok:false,msg:`标签 ${bad.join('、')} 的总分还不对。`}:{ok:true,msg:`对。最大的是 B，所以 C 改写为 ${chooseLabel(votes,'C')}。`};}};
  }},
 {id:'l4',region:2,title:'第 4 关 · 一整轮',film:241.0,xp:100,
  story:'一轮就是按顺序把每个点访问一次。异步更新时，后面的点立刻读到前面的新标签。',
  task:'点节点切换它的标签，预测第一轮结束后五个点的标签。',
  hints:['A 跟随最强的邻居 B（权重 5）。B 读到 A 的新标签 B，保持 B。','C 是上一关算过的 B；D 在 C 之后更新，它最强的邻居是 E。'],
  build:ctx=>{
    const truth=afterRound(GOLDEN,1).labels,guess=Object.fromEntries(GOLDEN.nodes.map(n=>[n,n]));
    const draw=()=>drawGraph(ctx.svg,GOLDEN,{colors:n=>labelColor(GOLDEN,guess[n]),sub:n=>'标签 '+guess[n],aria:n=>`节点 ${n}，你的预测 ${guess[n]}，点按切换`,
      onNode:n=>{const L=GOLDEN.nodes;guess[n]=L[(L.indexOf(guess[n])+1)%L.length];sound.tick();draw();}});
    draw();ctx.note('点按节点，标签按 A→B→C→D→E 循环。');
    return {check:()=>{const wrong=GOLDEN.nodes.filter(n=>guess[n]!==truth[n]);
      return wrong.length?{ok:false,msg:`还有 ${wrong.length} 个点不对。`}:{ok:true,msg:'对。第一轮改变了 3 个点：A、C、D。'};}};
  }},
 {id:'l5',region:2,title:'第 5 关 · 什么时候停',film:258.02,xp:100,
  story:'看起来不再变了，还不够。只有一整轮零变化，才能确认稳定。',
  task:'在通讯录图上一轮一轮推进，算法一共要报告几轮？',
  hints:['每按一次“跑一轮”，看下方记录里这一轮改变了几人。','最后那一轮的改变数是 0，它也算一轮。'],
  build:ctx=>{
    let p=new Propagation(CONTACTS);const log=el('ol',{class:'q-log'});
    const draw=()=>{ranked(CONTACTS,p.labels);drawGraph(ctx.svg,CONTACTS,{colors:n=>labelColor(CONTACTS,p.labels[n])});};
    const btn=el('button',{class:'button',type:'button',on:{click:()=>{if(p.status!=='running')return;const r=p.round;let ch=0;
      while(p.status==='running'&&p.round===r){const e=p.step();if(e.changed)ch++;}
      log.append(el('li',{},`第 ${p.round} 轮：改变 ${ch} 人${p.status==='stable'?' · 零变化，确认稳定':''}`));sound.tick();draw();}}},'跑一轮');
    const reset=el('button',{class:'button quiet',type:'button',on:{click:()=>{p=new Propagation(CONTACTS);log.replaceChildren();draw();}}},'重来');
    const input=el('input',{type:'number',min:1,max:20,'aria-label':'你的答案：几轮'});
    ctx.controls.append(el('div',{class:'q-row'},btn,reset),log,el('label',{class:'q-answer'},'一共几轮？ ',input));draw();
    const truth=runFull(CONTACTS).rounds;
    return {check:()=>Number(input.value)===truth?{ok:true,msg:`对，${truth} 轮。最后一轮没有任何人改变，这一轮用来确认稳定。`}:{ok:false,msg:'不对。别忘了最后那一轮零变化也要算。'}};
  }},
 {id:'l6',region:2,title:'第 6 关 · 同时还是轮流',film:275.04,xp:100,
  story:'两个相连的点。如果它们同时读对方的旧标签，会发生什么？',
  task:'分别用两种方式运行，然后回答：哪种方式会永远停不下来？',
  hints:['同时更新：A 读到 B，B 读到 A，各自换成对方的标签。','下一轮再换回来，状态重复了。'],
  build:ctx=>{
    const out=el('p',{class:'q-pick'},'还没运行。');let seen={};
    const run=mode=>{const r=runFull(PRESETS.pair,{mode,maxRounds:6});seen[mode]=r.status;
      drawGraph(ctx.svg,PRESETS.pair,{colors:n=>labelColor(PRESETS.pair,r.labels[n]),sub:n=>'标签 '+r.labels[n]});
      out.textContent=`${mode==='sync'?'同时更新':'轮流更新'}：${r.status==='cycle'?`第 ${r.rounds} 轮回到了出现过的状态，停不下来`:`第 ${r.rounds} 轮零变化，稳定`}。`;sound.tick();};
    drawGraph(ctx.svg,PRESETS.pair,{colors:n=>labelColor(PRESETS.pair,n),sub:n=>'标签 '+n});
    ctx.controls.append(el('div',{class:'q-row'},el('button',{class:'button',type:'button',on:{click:()=>run('sync')}},'同时更新'),el('button',{class:'button',type:'button',on:{click:()=>run('async')}},'轮流更新')),out);
    const looping=runFull(PRESETS.pair,{mode:'sync',maxRounds:6}).status==='cycle'?0:1;
    const c=choiceCheck(ctx,['同时更新','轮流更新'],looping,'对。同时更新读的是旧快照，两个点会永远互换。轮流更新时，后者读到前者的新标签，就一致了。');
    return {check:()=>Object.keys(seen).length<2?{ok:false,msg:'先把两种方式都运行一次。'}:c.check()};
  }},
 {id:'l7',region:3,title:'第 7 关 · 分得好不好',film:292.32,xp:100,
  story:'算法停下后，被切开的边是跨越两个组的边。cutsize 加的是权重，不是条数。',
  task:'点出所有被切开的边。',
  hints:['最终 A、B、C 一组，D、E 一组。','跨组的只有和 C 相连、通向 D 或 E 的边。'],
  build:ctx=>{
    const r=runFull(GOLDEN),pick=new Set(),sum=el('p',{class:'q-pick'});
    const draw=()=>{drawGraph(ctx.svg,GOLDEN,{colors:n=>labelColor(GOLDEN,r.labels[n]),sub:n=>'标签 '+r.labels[n],
      edgeStyle:(e,i)=>pick.has(i)?{stroke:'#a33b3b',width:6}:{},onEdge:(e,i)=>{pick.has(i)?pick.delete(i):pick.add(i);sound.tick();draw();}});
      const w=[...pick].reduce((s,i)=>s+GOLDEN.edges[i][2],0);sum.textContent=`你选了 ${pick.size} 条边，权重合计 ${w}`;};
    ctx.controls.append(sum);draw();ctx.note('点按边线选中或取消。');
    const truth=new Set(GOLDEN.edges.map((e,i)=>r.labels[e[0]]!==r.labels[e[1]]?i:-1).filter(i=>i>=0));
    return {check:()=>pick.size===truth.size&&[...truth].every(i=>pick.has(i))?{ok:true,msg:`对。${truth.size} 条边，cutsize = ${r.metrics.cut}。`}:{ok:false,msg:'选的边还不对。看看哪些边的两端标签不同。'}};
  }},
 {id:'l8',region:3,title:'第 8 关 · 边界会移动',film:309.09,xp:100,
  story:'连接的强弱决定边界。把 C—D 这条桥加粗，C 和 D 迟早会落进同一组。',
  task:'找到让 C 和 D 落进同一组的最小 C—D 权重。',
  hints:['每拖一次，下面都会显示真实运行的结果。','从 2 开始一格一格往上加，看 D 的标签什么时候变成和 C 一样。'],
  build:ctx=>{
    let w=2;const slider=el('input',{type:'range',min:1,max:12,value:w,'aria-label':'C—D 的权重'}),out=el('output',{},String(w)),info=el('p',{class:'q-pick'});
    const res=x=>runFull(withEdge(GOLDEN,'C','D',x));
    const draw=()=>{const g=withEdge(GOLDEN,'C','D',w),r=res(w);
      drawGraph(ctx.svg,g,{colors:n=>labelColor(GOLDEN,r.labels[n]),sub:n=>'标签 '+r.labels[n],edgeStyle:e=>(e[0]==='C'&&e[1]==='D')||(e[0]==='D'&&e[1]==='C')?{stroke:'#b58c35',width:2+w*.6}:{}});
      info.textContent=`C—D = ${w}：${r.labels.C===r.labels.D?'C 和 D 同组':'C 和 D 不同组'}，${r.metrics.count} 组，cutsize ${r.metrics.cut}，${r.rounds} 轮。`;};
    slider.addEventListener('input',()=>{w=Number(slider.value);out.textContent=w;draw();sound.tick();});
    ctx.controls.append(el('label',{class:'q-slider'},'C—D 的权重 ',out,slider),info);draw();
    let min=null;for(let x=1;x<=12;x++){const r=res(x);if(r.labels.C===r.labels.D){min=x;break;}}
    return {check:()=>w===min?{ok:true,msg:`对，最小是 ${min}，这时 ${res(min).metrics.count} 组、cutsize ${res(min).metrics.cut}。再小一点，D 就留在 E 那边；继续加粗，看看 C 会去哪边。`}:res(w).labels.C===res(w).labels.D?{ok:false,msg:'C 和 D 已经同组了，但还能更小。'}:{ok:false,msg:'C 和 D 还不在同一组。'}};
  }},
 {id:'l9',region:3,title:'第 9 关 · 它做不到的事',film:325.98,xp:100,
  story:'标签传播不保证分几组，也不保证每组一样大。访问顺序一变，结果也可能变。',
  task:'用两种访问顺序运行老师的图，然后判断：分组和标签名有没有变？',
  hints:['A→E 的结果：A、B、C 一组，D、E 一组。','比较的是“谁和谁在一起”，不是标签叫什么。'],
  build:ctx=>{
    const fw=runFull(GOLDEN),bw=runFull(GOLDEN,{order:[...GOLDEN.nodes].reverse()}),out=el('p',{class:'q-pick'});let seen=0;
    const run=(r,name)=>{seen|=name==='fw'?1:2;drawGraph(ctx.svg,GOLDEN,{colors:n=>labelColor(GOLDEN,r.labels[n]),sub:n=>'标签 '+r.labels[n]});
      out.textContent=`${name==='fw'?'A→E':'E→A'}：${r.rounds} 轮，标签 ${GOLDEN.nodes.map(n=>n+':'+r.labels[n]).join(' ')}`;sound.tick();};
    drawGraph(ctx.svg,GOLDEN,{colors:n=>labelColor(GOLDEN,n),sub:n=>'标签 '+n});
    ctx.controls.append(el('div',{class:'q-row'},el('button',{class:'button',type:'button',on:{click:()=>run(fw,'fw')}},'顺序 A→E'),el('button',{class:'button',type:'button',on:{click:()=>run(bw,'bw')}},'顺序 E→A')),out);
    const same=sameGroups(fw.labels,bw.labels,GOLDEN.nodes),namesSame=GOLDEN.nodes.every(n=>fw.labels[n]===bw.labels[n]);
    const opts=['分组相同，标签名不同','分组不同，标签名也不同','分组和标签名都相同'],ans=same&&!namesSame?0:!same?1:2;
    const c=choiceCheck(ctx,opts,ans,`对。这张图里分组没变，但轮数从 ${fw.rounds} 变成 ${bw.rounds}，标签名也换了。别的图上，分组本身也可能变。`);
    return {check:()=>seen<3?{ok:false,msg:'先把两种顺序都运行一次。'}:c.check()};
  }},
 {id:'boss',region:3,boss:true,title:'终章 Boss · 芯片分块',film:309.09,xp:200,
  story:'24 个电路单元，拿尺子按位置切成三块，会切断 88 的连线权重。你能分得比尺子好吗？',
  task:'用三支画笔把 24 个单元分成三块，每块 6–10 个，切断的权重低于尺子的 88 即通关。',
  hints:['单元之间的粗线多在同一条“蛇形”带里，不一定按左右分。','试试从 N00、N08、N16 出发，沿粗线涂色。'],
  build:ctx=>paintLevel(ctx,CHIP,{limit:87,groups:3,minSize:6,maxSize:10,ruler:true})}
];
const REGIONS=[{name:'序章 · 通讯录',badge:'圈子观察者'},{name:'规则站 · 第 1–3 关',badge:'标签学徒'},{name:'运行站 · 第 4–6 关',badge:'传播调度员'},{name:'芯片城 · 第 7–9 关与终章',badge:'芯片划分师'}];
const RANKS=['新晋观察者','标签学徒','传播能手','芯片划分师'];

function choiceCheck(ctx,options,correct,okMsg){
  const box=el('div',{class:'q-choices',role:'radiogroup','aria-label':'选择答案'});
  options.forEach((t,i)=>box.append(el('button',{type:'button',class:'button',role:'radio','aria-checked':'false',on:{click:ev=>{ctx.state.choice=i;
    for(const b of box.children)b.setAttribute('aria-checked',String(b===ev.currentTarget));sound.tick();}}},t)));
  ctx.controls.append(box);
  return {check:()=>ctx.state.choice==null?{ok:false,msg:'先选一个答案。'}:ctx.state.choice===correct?{ok:true,msg:okMsg}:{ok:false,msg:'再想一想。'}};
}

function paintLevel(ctx,g,{limit,groups,minSize,maxSize=99,ruler=false}){
  const paint={};let brush=0;const stat=el('p',{class:'q-pick'});
  const lp=runFull(g),bar=el('div',{class:'q-brushes',role:'radiogroup','aria-label':'选择画笔'});
  BRUSH.forEach((c,i)=>bar.append(el('button',{type:'button',class:'q-brush',role:'radio','aria-checked':String(i===0),style:`--c:${c}`,on:{click:ev=>{brush=i;
    for(const b of bar.children)b.setAttribute('aria-checked',String(b===ev.currentTarget));}}},`圈子 ${i+1}`)));
  bar.append(el('button',{type:'button',class:'q-brush erase',on:{click:()=>{for(const k in paint)delete paint[k];draw();}}},'清空'));
  const score=()=>{const labs=Object.fromEntries(g.nodes.map(n=>[n,paint[n]??'?']));const m=metrics(g,labs);
    const sizes=BRUSH.map((_,i)=>g.nodes.filter(n=>paint[n]===i).length);return {m,sizes,all:g.nodes.every(n=>paint[n]!=null)};};
  const draw=()=>{const s=score();
    drawGraph(ctx.svg,g,{colors:n=>paint[n]!=null?BRUSH[paint[n]]:'#a7b3ac',fill:n=>paint[n]!=null?BRUSH[paint[n]]+'26':'#fffdf8',
      edgeStyle:e=>paint[e[0]]!=null&&paint[e[1]]!=null&&paint[e[0]]!==paint[e[1]]?{stroke:'#c0504d',opacity:.9}:{},
      aria:n=>`${show(n)}，${paint[n]!=null?'圈子 '+(paint[n]+1):'未上色'}，点按上色`,
      onNode:n=>{paint[n]=paint[n]===brush?undefined:brush;if(paint[n]===undefined)delete paint[n];sound.tick();draw();}});
    stat.textContent=`已上色 ${g.nodes.filter(n=>paint[n]!=null).length}/${g.nodes.length} · 各圈 ${s.sizes.join(' / ')} · 被切开的权重 ${s.all?s.m.cut:'—'}${ruler?' · 尺子 88':''}`;};
  const reveal=el('button',{type:'button',class:'button quiet',on:{click:()=>{
    let k=0;const p=new Propagation(g);const tick=()=>{if(p.status!=='running'){stat.textContent=`标签传播：${p.round} 轮，切开 ${metrics(g,p.labels).cut}，各组 ${metrics(g,p.labels).sizes.join(' / ')}。这不是你的答案，通关仍看你自己的分法。`;return;}
      p.step();ranked(g,p.labels);drawGraph(ctx.svg,g,{colors:n=>labelColor(g,p.labels[n])});if(++k<400)setTimeout(tick,reduce()?0:35);};tick();}}},'看标签传播怎么分');
  ctx.controls.append(bar,stat,el('div',{class:'q-row'},reveal,el('button',{type:'button',class:'button quiet',on:{click:draw}},'回到我的分法')));draw();
  ctx.note(g===CONTACTS?'点按名字上色，再点一次取消。红线是被切开的联系。':'点按单元上色，再点一次取消。红线是被切开的连线。');
  return {check:()=>{const s=score();
    if(!s.all)return {ok:false,msg:'还有没上色的。'};
    if(s.sizes.filter(x=>x>0).length<groups)return {ok:false,msg:`要用满 ${groups} 个圈子。`};
    if(s.sizes.some(x=>x>0&&(x<minSize||x>maxSize)))return {ok:false,msg:`每个圈子要有 ${minSize}–${maxSize} 个。`};
    if(s.m.cut>limit)return {ok:false,msg:`被切开的权重是 ${s.m.cut}，目标 ≤ ${limit}。`};
    return {ok:true,best:s.m.cut,msg:`通关！你切开 ${s.m.cut}${ruler?'，尺子切开 88':''}；标签传播切开 ${lp.metrics.cut}。${s.m.cut<=lp.metrics.cut?'你和算法一样好。':'看看算法怎么分。'}`};}};
}
const reduce=()=>matchMedia('(prefers-reduced-motion: reduce)').matches||document.documentElement.classList.contains('no-motion');

// ---------------------------------------------------------------- HUD, map, level view
const xpTotal=LEVELS.reduce((s,l)=>s+l.xp,0);
function hud(){
  const xp=LEVELS.filter(l=>save.done[l.id]).reduce((s,l)=>s+l.xp,0),n=LEVELS.filter(l=>save.done[l.id]).length;
  const badges=REGIONS.filter((_,i)=>LEVELS.filter(l=>l.region===i).every(l=>save.done[l.id]));
  $('#q-rank').textContent=RANKS[Math.min(3,Math.floor(n/3))];$('#q-xp').textContent=xp;$('#q-xp-total').textContent=xpTotal;
  $('#q-count').textContent=`${n} / ${LEVELS.length}`;$('#q-bar').style.width=(n/LEVELS.length*100)+'%';$('#q-badges').textContent=badges.length;
  $('#q-badge-list').replaceChildren(...REGIONS.map((r,i)=>el('li',{class:badges.includes(r)?'got':''},(badges.includes(r)?'★ ':'☆ ')+r.badge)));
}
function map(){
  const holder=$('#q-map');holder.replaceChildren();
  REGIONS.forEach((r,i)=>{const list=el('div',{class:'q-stops'});
    for(const l of LEVELS.filter(x=>x.region===i))list.append(el('button',{type:'button',class:'q-stop'+(save.done[l.id]?' done':'')+(l.boss?' boss':''),on:{click:()=>open(l.id)}},
      el('span',{class:'q-stop-mark'},save.done[l.id]?'✓':l.boss?'♛':l.title.match(/第 (\d) 关/)?.[1]||'·'),el('span',{},l.title.replace(/^.*· /,'')),el('small',{},`+${l.xp} XP`)));
    holder.append(el('section',{class:'q-region'},el('h4',{},r.name),list));});
}
let current=null;
function open(id){
  const l=LEVELS.find(x=>x.id===id);current=l;const view=$('#q-level');view.hidden=false;
  $('#q-title').textContent=l.title;$('#q-story').textContent=l.story;$('#q-task').textContent=l.task;$('#q-xp-tag').textContent=`${save.done[id]?'已通关 · ':'首次通关 '}+${l.xp} XP`;
  $('#q-film').onclick=()=>{window.dispatchEvent(new CustomEvent('seek-film',{detail:l.film}));};
  const svg=$('#q-svg'),controls=$('#q-controls'),noteEl=$('#q-note'),feedback=$('#q-feedback');controls.replaceChildren();noteEl.textContent='';feedback.textContent='';feedback.className='q-feedback';
  for(const[i,h]of l.hints.entries()){const d=$(`#q-hint${i+1}`);d.open=false;d.querySelector('p').textContent=h;}
  const ctx={svg,controls,state:{},note:t=>{noteEl.textContent=t;}};l.api=l.build(ctx);
  const idx=LEVELS.indexOf(l);$('#q-prev').disabled=idx===0;$('#q-next').disabled=idx===LEVELS.length-1;
  view.scrollIntoView({behavior:reduce()?'auto':'smooth',block:'start'});
}
function check(){
  const r=current.api.check(),fb=$('#q-feedback');fb.textContent=r.msg;fb.className='q-feedback '+(r.ok?'ok':'no');
  if(!r.ok){sound.miss();return;}
  if(r.best!=null)save.best[current.id]=Math.min(save.best[current.id]??Infinity,r.best);
  const first=!save.done[current.id];save.done[current.id]=true;persist();hud();map();
  $('#q-xp-tag').textContent=`已通关 · +${current.xp} XP`;
  if(first){sound.win();celebrate(current);}else sound.ok();
}
function celebrate(l){
  const o=$('#q-celebrate');o.hidden=false;$('#q-cele-title').textContent=l.boss?'Boss 击败！':'通关！';$('#q-cele-xp').textContent=`+${l.xp} XP`;
  const region=REGIONS[l.region],full=LEVELS.filter(x=>x.region===l.region).every(x=>save.done[x.id]);
  $('#q-cele-badge').textContent=full?`获得徽章：${region.badge}`:'';
  const burst=$('#q-confetti');burst.replaceChildren();
  if(!reduce())for(let i=0;i<60;i++)burst.append(el('i',{style:`--x:${Math.random()*100}vw;--d:${.8+Math.random()*1.4}s;--r:${Math.random()*720-360}deg;background:${[...BRUSH,'#b58c35','#a44170'][i%5]}`}));
  clearTimeout(celebrate.t);celebrate.t=setTimeout(()=>{o.hidden=true;},2600);
}
$('#q-celebrate').addEventListener('click',()=>{$('#q-celebrate').hidden=true;});
$('#q-check').addEventListener('click',check);
$('#q-reset').addEventListener('click',()=>open(current.id));
$('#q-prev').addEventListener('click',()=>open(LEVELS[LEVELS.indexOf(current)-1].id));
$('#q-next').addEventListener('click',()=>open(LEVELS[LEVELS.indexOf(current)+1].id));
$('#q-start').addEventListener('click',()=>open((LEVELS.find(l=>!save.done[l.id])||LEVELS[0]).id));
$('#q-export').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({schema:KEY,...save},null,2)],{type:'application/json'})),a=el('a',{href:url,download:'label-propagation-quest.json'});a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('#q-import').addEventListener('change',async ev=>{try{const d=JSON.parse(await ev.target.files[0].text());if(d.schema!==KEY)throw Error();
  save={done:Object.fromEntries(Object.entries(d.done||{}).filter(([k,v])=>v===true&&LEVELS.some(l=>l.id===k))),best:d.best||{}};persist();hud();map();}catch{alert('无法读取这个进度文件。');}ev.target.value='';});
$('#q-clear').addEventListener('click',()=>{if(confirm('清除这个浏览器里的闯关进度？')){save={done:{},best:{}};persist();hud();map();}});
for(const b of document.querySelectorAll('[data-level]'))b.addEventListener('click',ev=>{ev.preventDefault();open(b.dataset.level);});
hud();map();
export {drawGraph};
