import {QUESTIONS} from './questions.js?v=20261020a';
import {GOLDEN,PRESETS,Propagation,metrics,votesFor,chooseLabel,validateGraph} from './algorithm.js?v=20261020a';
const $=s=>document.querySelector(s),NS='http://www.w3.org/2000/svg';
const palette=['#a57a20','#0f7966','#b76529','#315cba','#a44170','#8051a0','#397f85','#84672e'];
let graph=structuredClone(GOLDEN),engine=null,timer=null,last=null,toastTimer=null;
let missions={};try{missions=JSON.parse(localStorage.getItem('lp-lab5-missions')||'{}')||{};}catch{}
function color(n,g=graph){return palette[Math.max(0,g.nodes.indexOf(n))%palette.length];}
function node(tag,attrs={},text=''){
 const el=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))el.setAttribute(k,String(v));if(text)el.textContent=text;return el;
}
function toast(s){$('#toast').textContent=s;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,3500);}
function saveMission(name){if(missions[name]===true)return;missions[name]=true;try{localStorage.setItem('lp-lab5-missions',JSON.stringify(missions));}catch{}renderMissions();toast('实践目标完成：'+({vote:'看懂 C 的 5 票',golden:'复现教师样例',cycle:'找到同步振荡'}[name]));}
function renderMissions(){for(const[k,v]of Object.entries({vote:'看懂 C 的 5 票',golden:'复现教师样例',cycle:'找到同步振荡'})){
 const el=$('#mission-'+k);el.classList.toggle('done',missions[k]===true);el.textContent=(missions[k]===true?'✓ ':'○ ')+v;
}}
function posFor(g){
 if(g.positions)return g.positions;
 return Object.fromEntries(g.nodes.map((n,i)=>{const a=i/g.nodes.length*Math.PI*2-Math.PI/2;return[n,[370+240*Math.cos(a),260+200*Math.sin(a)]];}));
}
function draw(svg,g,labels,active=null,interactive=false){
 svg.replaceChildren();const pos=posFor(g);
 for(const[u,v,w]of g.edges){
  const a=pos[u],b=pos[v],cross=labels[u]!==labels[v],focus=u===active||v===active;
  svg.append(node('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:focus?'#977129':cross?'#b79f70':'#99b9a9','stroke-width':focus?4:1.3+Math.min(w,10)*.4,class:'edge'}));
  const mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2;
  svg.append(node('circle',{cx:mx,cy:my,r:13,fill:'#fffdf8'}),node('text',{x:mx,y:my+5,'text-anchor':'middle',fill:'#607065','font-size':15},String(w)));
 }
 for(const n of g.nodes){
  const[x,y]=pos[n];const group=node('g',{class:'node',...(interactive?{tabindex:0,role:'button','aria-label':`节点 ${n}，当前标签 ${labels[n]}，查看票数`}:{})});
  if(n===active)group.append(node('circle',{cx:x,cy:y,r:37,fill:'none',stroke:'#ae893f','stroke-width':1.5,class:$('#motion').checked?'pulse':''}));
  group.append(node('circle',{cx:x,cy:y,r:28,fill:'#fffdf8',stroke:color(labels[n],g),'stroke-width':3}),node('text',{x,y:y+8,'text-anchor':'middle',fill:'#273b32','font-size':24,'font-weight':600},n),node('text',{x,y:y+49,'text-anchor':'middle',fill:color(labels[n],g),'font-size':16},'标签 '+labels[n]));
  if(interactive){const inspect=()=>inspectNode(n);group.addEventListener('click',inspect);group.addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();inspect();}});}
  svg.append(group);
 }
}
function stop(){clearInterval(timer);timer=null;$('#play').textContent='自动播放';}
function options(){return {mode:$('#mode').value,tie:$('#tie').value,order:$('#order').value.trim().split(/[\s,，]+/).filter(Boolean)};}
function apply(){
 try{const next=new Propagation(graph,options());stop();engine=next;last=null;$('#comparison').hidden=true;render();}catch(e){toast(e.message);}
}
function inspector(votes,title,decision){
 $('#vote-title').textContent=title;$('#votes').replaceChildren();const max=Math.max(1,...Object.values(votes));
 for(const[n,w]of Object.entries(votes).sort()){
  const row=document.createElement('div');row.className='vote-row';const label=document.createElement('span');label.textContent=n;label.style.minWidth='18px';
  const bar=document.createElement('span');bar.className='vote-bar';bar.style.width=(w/max*155)+'px';bar.style.background=color(n);
  const val=document.createElement('strong');val.textContent=Number(w.toFixed(8)).toString();row.append(label,bar,val);$('#votes').append(row);
 }
 if(!Object.keys(votes).length)$('#votes').textContent='没有邻居，保留原标签。';
 $('#decision').textContent=decision;
}
function inspectNode(n){
 const source=engine.mode==='sync'?engine.base:engine.labels,{votes}=votesFor(graph,source,n);
 inspector(votes,`查看节点 ${n} 的当前票数`,`若现在更新，将选择 ${chooseLabel(votes,source[n],engine.tie)}。${engine.mode==='sync'?'读取本轮开始时的快照。':'读取当前已经写回的标签。'}`);
 draw($('#lab-graph'),graph,engine.labels,n,true);
}
function render(){
 const m=metrics(graph,engine.labels);$('#rounds').textContent=engine.round;$('#clusters').textContent=m.count;$('#cut').textContent=Number(m.cut.toFixed(8));
 $('#active-config').textContent=`${engine.mode==='async'?'异步':'同步'} · ${engine.order.join(' ')} · 平票${{min:'取最小',max:'取最大',keep:'当前优先'}[engine.tie]}`;
 draw($('#lab-graph'),graph,engine.labels,last?.node,true);
 const status={running:last?`第 ${last.round} 轮，刚计算 ${last.node}。${last.roundEnd?'本轮已完成。':''}`:'等待第一次更新',stable:`稳定：第 ${engine.round} 轮零变化，已确认。`,cycle:`振荡：第 ${engine.round} 轮出现重复状态，已停止。`,limit:`达到 ${engine.round} 轮上限，尚未确认收敛。`};
 $('#status').textContent=status[engine.status];$('#status').classList.toggle('warning',['cycle','limit'].includes(engine.status));
 for(const id of ['step','round','play'])$('#'+id).disabled=engine.status!=='running';
 if(last){
  const msg=last.changed?`${last.node}：${last.old} → ${last.label}`:`${last.node} 保留 ${last.label}`;
  const pending=engine.mode==='sync'&&!last.committed?' 这是待写回的决定，图上仍保留旧标签。':'';
  inspector(last.votes,`刚计算：${last.node}（第 ${last.round} 轮）`,msg+pending);
 }else{
  const n=engine.order[0],{votes}=votesFor(graph,engine.labels,n);inspector(votes,'下一位：'+n,'可以先预测，再点“更新一个节点”。');
 }
 $('#legend').replaceChildren();for(const[n,arr]of Object.entries(m.clusters)){
  const span=document.createElement('span'),i=document.createElement('i');i.style.background=color(n);span.append(i,document.createTextNode(`${n}：${arr.join('、')}`));$('#legend').append(span);
 }
 $('#trace').replaceChildren();for(const e of engine.history){
  const tr=document.createElement('tr');for(const val of [e.round,e.node,e.old,Object.entries(e.votes).map(([k,v])=>k+':'+Number(v.toFixed(8))).join(' / ')||'无邻居',e.label,e.mode==='async'?'立即':e.roundEnd?'本轮统一提交':'待轮末提交']){
   const td=document.createElement('td');td.textContent=val;tr.append(td);
  }$('#trace').append(tr);
 }
}
function step(){
 if(engine.status!=='running')return;last=engine.step();render();
 if(engine.status!=='running'){
  stop();if(graph.id==='pair'&&engine.mode==='sync'&&engine.status==='cycle')saveMission('cycle');
  if(engine.mode==='async'&&engine.tie==='min'&&engine.order.join('')==='ABCDE'&&JSON.stringify(graph.edges)===JSON.stringify(GOLDEN.edges)&&engine.status==='stable'&&engine.round===2&&metrics(graph,engine.labels).cut===3)saveMission('golden');
 }
}
$('#step').addEventListener('click',()=>{stop();step();});
$('#round').addEventListener('click',()=>{stop();const r=engine.round;while(engine.status==='running'&&engine.round===r)last=engine.step();render();if(engine.status!=='running'){
 if(graph.id==='pair'&&engine.mode==='sync'&&engine.status==='cycle')saveMission('cycle');
 if(engine.mode==='async'&&engine.tie==='min'&&engine.order.join('')==='ABCDE'&&JSON.stringify(graph.edges)===JSON.stringify(GOLDEN.edges)&&engine.status==='stable'&&engine.round===2)saveMission('golden');
}});
$('#play').addEventListener('click',()=>{if(timer){stop();return;}$('#play').textContent='暂停';step();if(engine.status==='running')timer=setInterval(step,850);});
$('#reset').addEventListener('click',apply);$('#apply').addEventListener('click',apply);
$('#mode').addEventListener('change',apply);$('#tie').addEventListener('change',apply);
$('#preset').addEventListener('change',()=>{
 const preset=PRESETS[$('#preset').value];graph=structuredClone(preset);$('#order').value=graph.nodes.join(' ');
 $('#bridge').disabled=graph.id!=='golden';$('#bridge').value=2;$('#bridge-value').textContent='2';apply();
});
$('#bridge').addEventListener('input',()=>{
 if(graph.id!=='golden')return;const val=Number($('#bridge').value);$('#bridge-value').textContent=val;
 graph.edges=GOLDEN.edges.map(e=>[...e]).filter(e=>!(e[0]==='C'&&e[1]==='D'));
 if(val>0)graph.edges.splice(3,0,['C','D',val]);apply();
});
$('#motion').addEventListener('change',()=>document.documentElement.classList.toggle('no-motion',!$('#motion').checked));
$('#graph-json').value=JSON.stringify({nodes:GOLDEN.nodes,edges:GOLDEN.edges},null,2);
$('#load-json').addEventListener('click',()=>{try{
 const d=JSON.parse($('#graph-json').value);validateGraph(d);graph={id:'custom',name:'自定义图',nodes:d.nodes,edges:d.edges};
 $('#order').value=graph.nodes.join(' ');$('#bridge').disabled=true;apply();toast('已加载自己的图；节点位置为圆形排列。');
}catch(e){toast('图数据有问题：'+e.message);}});
$('#compare').addEventListener('click',()=>{
 stop();const settings=[['当前配置',options()],['正序异步',{mode:'async',tie:'min',order:[...graph.nodes].sort()}],['倒序异步',{mode:'async',tie:'min',order:[...graph.nodes].sort().reverse()}],['正序同步',{mode:'sync',tie:'min',order:[...graph.nodes].sort()}]];
 const holder=$('#comparison');holder.replaceChildren();const scroll=document.createElement('div');scroll.className='table-scroll';const table=document.createElement('table');
 const header=document.createElement('tr');for(const s of ['配置','轮数','停止原因','标签（按原节点顺序）','群体数','加权割边']){const th=document.createElement('th');th.textContent=s;header.append(th);}table.append(header);
 try{for(const[name,o]of settings){const r=new Propagation(graph,o).run(),tr=document.createElement('tr');for(const v of [name,r.rounds,r.status,graph.nodes.map(n=>n+':'+r.labels[n]).join(' '),r.metrics.count,Number(r.metrics.cut.toFixed(8))]){const td=document.createElement('td');td.textContent=v;tr.append(td);}table.append(tr);}}
 catch(e){toast(e.message);return;}scroll.append(table);holder.append(scroll);const p=document.createElement('p');p.className='small';p.textContent='每行均独立重置后真实运行。轮数包含零变化确认轮；cycle 与 limit 不能视作稳定。标签名字不同不一定代表分区不同。';holder.append(p);holder.hidden=false;
});
$('#export').addEventListener('click',()=>{
 const payload={schema:'lp-lab5-v1',graph,parameters:{mode:engine.mode,tie:engine.tie,order:engine.order},...engine.result()};
 const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='label-propagation-trace.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
for(const button of document.querySelectorAll('[data-film]'))button.addEventListener('click',()=>{
 const short=button.dataset.film==='short',v=$('#film-player');v.pause();v.src=short?'media/one-graph.mp4':'media/neighbors.mp4';v.poster=short?'media/one-graph.jpg':'media/cover.jpg';
 v.querySelector('track').src=short?'media/one-graph.zh.vtt':'media/neighbors.zh.vtt';v.load();
 for(const b of document.querySelectorAll('[data-film]'))b.setAttribute('aria-pressed',String(b===button));
 for(const b of document.querySelectorAll('[data-seek]'))b.hidden=short;
});
for(const button of document.querySelectorAll('[data-seek]'))button.addEventListener('click',()=>{const v=$('#film-player');v.currentTime=Number(button.dataset.seek);v.play().catch(()=>{});});
// Burned-in subtitles are primary; the VTT remains available without duplicating them by default.
$('#film-player').addEventListener('loadedmetadata',()=>{for(const track of $('#film-player').textTracks)track.mode='disabled';});
const questions=QUESTIONS;
for(const[qidx,q]of questions.entries()){
 const article=document.createElement('article');article.className='question';const title=document.createElement('h3'),number=document.createElement('span');number.textContent=String(qidx+1).padStart(2,'0');title.append(number,document.createTextNode(q.q));
 const choices=document.createElement('div');choices.className='answers';const feedback=document.createElement('p');feedback.className='answer-feedback';feedback.setAttribute('aria-live','polite');
 q.a.forEach((answer,i)=>{const b=document.createElement('button');b.textContent=answer;b.addEventListener('click',()=>{for(const old of choices.children){old.classList.remove('wrong','correct');old.setAttribute('aria-pressed','false');}b.setAttribute('aria-pressed','true');b.classList.add(i===q.correct?'correct':'wrong');feedback.textContent=(i===q.correct?'正确。':'再想一想。')+q.e;if(i===q.correct&&q.mission)saveMission(q.mission);});choices.append(b);});article.append(title,choices,feedback);$('#questions').append(article);
}
renderMissions();draw($('#hero-graph'),GOLDEN,{A:'B',B:'B',C:'B',D:'E',E:'E'});apply();
