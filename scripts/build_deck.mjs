// Editable mathematical diagrams and text, using the bundled Artifact Tool.
import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath,pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const skill=process.env.PRESENTATION_SKILL_DIR;if(!skill)throw Error('Set PRESENTATION_SKILL_DIR; see docs/REPRODUCE.md');
const data=JSON.parse(await fs.readFile(path.join(root,'data/traces.json'),'utf8'));
const out=path.join(root,'build/private/deck');await fs.mkdir(out,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});p.theme.defaultFont='Heiti SC';
const C={bg:'#f3efe6',ink:'#1c2421',green:'#0f6b5c',muted:'#5c675f',line:'#d5cdc0',gold:'#9a6b12',red:'#a33b3b'};
const colors={A:'#a57a20',B:'#0f7966',C:'#b76529',D:'#315cba',E:'#a44170'};
const source='https://github.com/yongfu-li/eda-learning/tree/main/courses/learn_clustering/module02-01-label-propagation';
const paper='https://arxiv.org/abs/0709.2938';
function text(s,t,x,y,w,h,size=28,color=C.ink,bold=false,serif=false){
 const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=t;a.text.style={typeface:serif?'Songti SC':'Heiti SC',fontSize:size,color,bold,insets:0,wrap:'square',autoFit:'none'};return a;
}
function slide(title,notes=''){
 const s=p.slides.add();s.background.fill=C.bg;
 text(s,title,64,42,1152,72,44,C.green,true,true);
 text(s,`Lab 05  标签传播聚类`,64,676,780,24,16,C.muted);
 text(s,String(p.slides.items.length).padStart(2,'0'),1160,676,56,24,16,C.muted);
 s.speakerNotes.text=notes+'\n\n资料：'+source+'\n'+paper;return s;
}
function ln(s,x1,y1,x2,y2,color=C.line,width=2){
 const minx=Math.min(x1,x2),miny=Math.min(y1,y2);
 return s.shapes.add({geometry:'line',position:{left:minx,top:miny,width:Math.abs(x2-x1)||.1,height:Math.abs(y2-y1)||.1,verticalFlip:y2<y1,horizontalFlip:x2<x1},fill:'none',line:{fill:color,width}});
}
function node(s,n,label,x,y,r=28){
 const a=s.shapes.add({geometry:'ellipse',position:{left:x-r,top:y-r,width:r*2,height:r*2},fill:'#fffdf8',line:{fill:colors[label],width:3}});
 text(s,n,x-r,y-19,r*2,40,30,colors[label],true).text.alignment='center';
 text(s,'标签 '+label,x-60,y+36,120,27,20,colors[label]).text.alignment='center';return a;
}
function graph(s,labels=Object.fromEntries('ABCDE'.split('').map(n=>[n,n])),cut=false){
 const pos={A:[155,228],B:[375,202],C:[305,385],D:[625,410],E:[515,555]};
 for(const [u,v,w]of data.graphs.golden.edges){
  const a=pos[u],b=pos[v],co=cut&&labels[u]!==labels[v]?C.gold:'#78948c';
  ln(s,...a,...b,co,1+w*.35);text(s,String(w),(a[0]+b[0])/2-16,(a[1]+b[1])/2-19,32,34,23,co,true).text.alignment='center';
 }
 for(const[n,[x,y]]of Object.entries(pos))node(s,n,labels[n],x,y);
}
function statement(s,t,x=795,y=200,w=415,size=30,color=C.ink){return text(s,t,x,y,w,400,size,color);}
function table(s,values,x,y,w,h,widths){
 const tb=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
 tb.borders.assign({fill:C.line,width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=tb.getCell(r,c);cell.fill=r===0?C.green:(r%2?'#fffdf8':C.bg);
  cell.text.style={typeface:'Heiti SC',fontSize:25,color:r===0?'#ffffff':C.ink,bold:r===0,insets:12};
 }return tb;
}
// 01: the source film is the requested presentation material, not decorative stock.
{
 const s=p.slides.add();s.background.fill='#0a1922';const b=await fs.readFile(path.join(root,'site/media/cover.jpg'));
 s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/jpeg',position:{left:0,top:0,width:1280,height:720},fit:'contain',alt:'原创影片封面：邻居的颜色'});
 s.speakerNotes.text='开场播放原创短片《邻居的颜色》，3分49秒，无配音。随后选第4至11页讲解核心实例。作者 Su3037。图书馆为虚构结构类比，不用于判断真实个人。\n'+source;
}
{
 const s=slide('连接与群体','先问观众：没有指定组长，为什么经常相连的点仍可能形成群体？这里讨论的是图结构的分组，不是社会学因果。');
 graph(s);statement(s,'每个点先有自己的标签。\n\n反复采用邻居的优势标签。\n群体可能逐渐形成。');
}
{
 const s=slide('课堂采用的确定性规则','课堂版本使用加权无向图。每轮依次更新，立即写回。平票按标签字典序最小。孤点保留原标签。原论文还有其他顺序和平票变体。');
 table(s,[['部分','本项目默认规则'],['初始化','每个节点以自身名称为标签'],['票数','按邻居当前标签累计边权'],['更新','异步，按 A 到 E 依次写回'],['平票','取字典序最小的标签'],['停止','一整轮没有任何改变']],64,154,1152,445,[220,932]);
}
{
 const s=slide('五节点的加权图','图结构与权重来自教师指定 tiny_graph。边权总和18。不是运行真实EDA工具。');
 graph(s);statement(s,'AB=5，AC=1，BC=4\nCD=2，DE=5，CE=1\n\n固定图和访问顺序。\n约定平票规则。\n\n再讨论结果。',795,205,415,29);
}
{
 const s=slide('A 的第一次更新','A看到B标签5票，C标签1票，因此A选择B。B随后读取已经更新的A，这是异步更新。');
 graph(s,data.golden.events[0].labels);statement(s,'B 标签得到 5 票\nC 标签得到 1 票\n\nA 的标签改为 B。\n后续节点立即看见这个变化。');
}
{
 const s=slide('C 的票数按标签累加','这一刻A和B均带标签B，C通过AC和BC收到同标签的1+4=5票。不能只选最粗的单条边，也不是按邻居人数多数。');
 graph(s,data.golden.events[2].before);table(s,[['标签','权重和'],['B','1 + 4 = 5'],['D','2'],['E','1']],800,205,410,270,[130,280]);
 text(s,'C 因此选择 B',800,520,410,60,34,C.green,true);
}
{
 const s=slide('第一轮的完整记录','逐个解释A、B、C、D、E。变化节点A、C、D共3个。此时已经形成两组，但还未完成零变化确认轮。');
 table(s,[['访问节点','更新前','更新后','发生改变'],...data.golden.events.slice(0,5).map(e=>[e.node,e.old,e.label,e.changed?'是':'否'])],64,160,1152,400,[230,280,280,362]);
 text(s,'轮末标签：B  B  B  E  E',64,588,1152,56,32,C.green,true);
}
{
 const s=slide('稳定确认与加权割边','第2轮零变化，所以iters=2包含确认轮。跨组的是CD与CE两条边，权重和3。切边数与加权cutsize区分。样例特定结果，不是普遍性质。');
 graph(s,data.golden.labels,true);statement(s,'第 2 轮：0 次改变\n\n跨组边：CD 与 CE\ncutsize = 2 + 1 = 3\n\n分组规模：3 : 2',795,205,415,30);
}
{
 const s=slide('同步更新可能振荡','双节点图初始A/B。同步整轮读旧值会轮流B/A与A/B。异步A先变B，B随后看到B而不变。实验检测重复状态并报告cycle，不伪称stable。');
 table(s,[['轮次','同步 A / B','异步 A / B'],['初始','A / B','A / B'],['第1轮','B / A','B / B'],['第2轮','A / B','B / B'],['停止原因','检测到重复状态','整轮零变化']],64,165,1152,390,[230,461,461]);
 text(s,'读取哪个时刻的邻居标签，会改变过程',64,590,1152,50,30,C.green);
}
{
 const s=slide('访问顺序与标签名字','实际独立运行：正序B/B/B/E/E，两轮；倒序A/A/A/D/D，三轮。分区相同但标签名不同。其他图或参数可能得到不同分区，不把本图的结果推广为总是相同。');
 table(s,[['顺序','最终标签 A B C D E','确认轮数'],['A B C D E','B B B E E','2'],['E D C B A','A A A D D','3']],64,185,1152,265,[250,652,250]);
 text(s,'比较分区时，需要区分“标签叫什么”和“哪些点在一起”',64,510,1152,100,29,C.ink);
}
{
 const s=slide('平票与停止原因','最小标签、最大标签、保留当前优先都是可定义的教学变体。默认教师规则是min。三种停止原因分别对应stable/cycle/limit。');
 text(s,'B 和 E 各得 5 票',64,180,560,70,37,C.ink,true);
 text(s,'课堂默认取 B\n\n平票规则与访问顺序必须一起记录。',64,290,550,230,29,C.green);
 text(s,'stable：整轮没有变化\n\ncycle：完整状态再次出现\n\nlimit：达到安全上限',720,190,490,360,28,C.ink);
}
{
 const s=slide('EDA 中的用途与限制','LP可作为粗化或初始社区线索。图模型是教学简化，实际网表可能包含超边，还需适合的模型与约束。不会保证两组、平衡或最优切割。');
 graph(s,data.golden.labels);statement(s,'用途：粗化与初始社区线索\n\n还需考虑规模和时序。\n也要满足物理实现约束。\n\n全同色时，cutsize=0。\n仍可能不符合任务。',795,185,415,29);
}
{
 const s=slide('生活类比的边界','回扣图书馆。模型里的标签依赖观察关系与权重，不能推出因果或人的本质。现实意义是提醒记录建模选择，重新观察边界，不是用算法替人贴标签。');
 text(s,'标签依赖我们选择的数据与规则',64,190,1152,85,46,C.green,true,true);
 text(s,'同一份连接可以有不同的解释。\n\n聚类结果需要回到任务与数据中检验。',64,330,1100,200,33,C.ink);
}
{
 const s=slide('本次教学改进','说明课程共建的增量，而非发明新算法。原材料已经有五节点图，本项目补充中文无配音知识动画、真实逐节点记录、同步振荡反例、改参实验、练习解析和复现测试。');
 text(s,'中文动画把每一句话对应到实际的图变化。',64,175,1152,70,33,C.green,true);
 text(s,'同一套算法事件连接视频、课堂例子和网页实验。\n\n加入同步振荡、顺序对照与加权票数的反例。\n\n习题给出解析，源码与测试支持复现。',64,290,1120,300,29,C.ink);
}
{
 const s=slide('课堂互动','切换网页到#lab。先让同学预测C的选择，再逐节点验证。切换两节点图同步运行观察cycle，最后改变桥边权重。无需完成所有实验。');
 text(s,'1  预测 C 的下一标签，并说出票数。\n\n2  切换同步更新，观察双节点为什么振荡。\n\n3  改变桥边权重，比较群体与加权割边。',64,190,1152,330,33,C.ink);
 text(s,'网页地址与完整使用说明见仓库 README',64,585,1152,50,25,C.green);
}
{
 const s=slide('资料与复现','来源完整链接列入本页备注。教师文件无独立开源许可声明，因此不再分发其课件、视频或课程私密资料。只引用事实与小图数据并注明来源。原创代码MIT，原创教材与媒体CC BY4.0，第三方各遵原许可。');
 text(s,'课程 Lab05：README、EXAMPLES、CHECKLIST\n参考求解器与指定的 tiny_graph 数据',64,180,1152,130,29,C.ink);
 text(s,'Raghavan、Albert、Kumara（2007）\nNear linear time algorithm to detect community structures',64,350,1152,120,27,C.ink);
 text(s,'原创动画、配乐、课件与实验源码随仓库交付',64,540,1152,70,31,C.green,true);
}
// Public HTML slide preview is generated from the same authored content renders.
for(let i=0;i<p.slides.items.length;i++){
 const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(out,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
await fs.writeFile(path.join(out,'montage.webp'),new Uint8Array(await(await p.export({format:'webp',montage:true})).arrayBuffer()));
// PDF preview is packaged from these same rendered pages by scripts/package_materials.py.
// The bundled direct PDF exporter currently lacks its internal standard-font resources.
const candidate=path.join(out,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(root,'site/downloads/label-propagation.pptx'),
 pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[3,6,7,9,10].flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:[3,6,7,9,10],fontPolicy:{basis:'design',families:['Heiti SC','Songti SC']},
 verifyArtifactToolImport:true,receiptPath:path.join(out,'validation.json')});
console.log('Deck finalized:',JSON.stringify(result));
await fs.mkdir(path.join(root,'site/slides'),{recursive:true});
for(let i=1;i<=p.slides.items.length;i++)await fs.copyFile(path.join(out,`slide-${String(i).padStart(2,'0')}.png`),path.join(root,'site/slides',`slide-${String(i).padStart(2,'0')}.png`));
await fs.writeFile(path.join(root,'presentation/notes.json'),JSON.stringify(p.slides.items.map((s,i)=>({slide:i+1,notes:s.speakerNotes.text})),null,2));
