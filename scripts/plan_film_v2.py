#!/usr/bin/env python3
"""Bind original shots and actions to measured transients in the chosen music."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'build/private/research-v2/music-analysis.json').read_text())
def snap(t):
    beat=min(m['grid'],key=lambda x:abs(x-t))
    peaks=[o for o in m['onsets'] if abs(o['time']-beat)<.13]
    onset=max(peaks,key=lambda o:o['strength'])['time'] if peaks else beat
    return round(onset*30)/30

# time, id, visual, chapter, short title, caption, camera / literal action.
rows=[
(0,'book','book','序 · 相遇','一本书的旅程','一本书，从你手里，走到另一个人手里。','close / book opens and moves'),
(4.2,'library','library','序 · 相遇','没有人先宣布分组','相似的相遇多了，熟悉的圈子慢慢出现。','wide / people walk and pass books'),
(9.0,'table','table','序 · 连接','我们能画出这些关系吗？','把一次次交流，记成轻重不同的连接。','overhead / book paths are drawn'),
(13.0,'morph','morph','序 · 连接','对象 → 节点；联系 → 边','留下连接，暂时放下人物的故事。','match move / bookmarks become nodes'),
(17.1,'title','title','LABEL PROPAGATION','邻居的颜色','一条局部规则，如何长出整体的形状？','music lift / title assembles'),
(21.4,'tags','tags','01 · 一条规则','先给每个点一个标签','节点的名字不变；颜色记录当前的标签。','top-down / five tags drop onto a page'),
(26.0,'weight-people','weight','01 · 一条规则','两位邻居，还是一位？','两位支持 B，一位支持 D。先别急着数人。','front / two small weights and one large weight'),
(30.2,'weight-scale','scale','01 · 一条规则','真正相加的是权重','B 的权重是 1＋1；D 的权重是 4。D 胜。','macro / scale visibly tips toward D'),
(34.5,'sum','tokens','01 · 一条规则','相同标签，放进同一个容器','先按标签归类，再把这些边的权重相加。','overhead / 1 and 4 chips collect into B vessel'),
(39.0,'setup','board','02 · 五节点实验','老师的图，真实算一遍','按 A 到 E 访问；平票时取字典序最小标签。','wide / board and queue enter'),
(43.2,'a','visit','02 · 五节点实验','A 收到 B 的 5 票','A 选择 B；新标签立即写回，这叫异步更新。','push / packets arrive then A changes',0),
(47.5,'b','visit','02 · 五节点实验','B 已经能读到新的 A','A 带着 B 标签送来 5 票，B 保留 B。','track / move focus from A to B',1),
(51.8,'c','visit','02 · 五节点实验','C 的关键一票','A 和 B 都带着 B：1＋4＝5，胜过 D 和 E。','macro / two streams merge into one tally',2),
(58.0,'de','finish','02 · 五节点实验','另一侧，也形成了群体','D 从 E 得到 5 票；D 变 E，E 保留 E。','pan / D updates before E reads'),
(64.4,'ledger','ledger','02 · 五节点实验','第一轮，三次改变','A、B、C 同组；D、E 同组。节点没有改名。','pull back / stamps land on a paper ledger'),
(68.6,'confirm','confirm','02 · 五节点实验','稳定，要用一整轮确认','第二轮零变化。因此，这个样例报告 2 轮。','scan / five checks appear one by one'),
(75.0,'cut','cut','02 · 五节点实验','边界上，还有两条连接','C—D 权重 2，C—E 权重 1。加权割边是 3。','separate / crossing ribbons stretch but remain'),
(81.2,'zero','zero','03 · 另一面','全部同色，割边也会变成 0','数字更小，未必就是任务需要的划分。','compress / five tags collapse into one tray'),
(85.5,'sync','sync','03 · 另一面','如果大家同时模仿对方？','A 读旧的 B；B 也读旧的 A，然后一起更新。','split / two mailboxes read then commit together'),
(91.8,'cycle','cycle','03 · 另一面','换回来，再换回去','A/B → B/A → A/B。这是振荡，不是收敛。','timeline / alternating snapshots remain visible'),
(96.0,'async','async','03 · 另一面','让后一个点，看见刚才的变化','A 先变 B；B 随后读到 B，两点便同色。','stagger / first mailbox commits before second reads'),
(100.5,'many','many','04 · 从局部到整体','把镜头拉远','同一条规则，放到 24 个节点上继续计算。','music lift / real multi-node trace propagates'),
(107.0,'city','city','04 · 从局部到整体','群体，从连接里浮现','这是虚构网络的模拟结果，不是现实人群的定论。','aerial / computed groups light different neighborhoods'),
(113.4,'bridge','bridge','04 · 从局部到整体','把桥梁加粗，边界也可能改变','五节点图的 C—D 改为 10，实际分组随之改变。','side / bridge traffic grows, memberships recompute'),
(119.8,'order','order','04 · 从局部到整体','顺序，也属于实验条件','此例倒序需 3 轮；标签名不同，分组仍可相同。','paper paths / forward and reverse queues unfold'),
(126.1,'tie','tie','04 · 从局部到整体','平票时，把规则写清楚','等权时可约定最小标签；实验才能准确复现。','balance / equal trays stop, B is selected'),
(132.5,'chip','chip','05 · 走进电路','从一本书，到一块芯片','把电路单元看作节点，把连接看作边。','match cut / city blocks become cell rectangles'),
(139.0,'floorplan','floorplan','05 · 走进电路','先把联系密切的部分找出来','聚类可以为粗化、初始分组提供线索。','top-down / actual groups pack into a chip outline'),
(145.3,'constraints','constraints','05 · 走进电路','真实设计，还有更多约束','规模、时序、拥塞，都需要另外检查。','zoom / size gauge, timing path and congested wires'),
(151.7,'ribbons','ribbons','尾声 · 重新看见','关系，决定了这次观察的形状','数据、边权、规则改变，结果也可能改变。','tracking / three literal controls change a small graph'),
(158.0,'return','return','尾声 · 重新看见','再回到那间图书馆','模型画出的群体，不是一个人的本质。','wide / opening room returns with visible connections'),
(166.6,'cross','cross','尾声 · 重新看见','圈子的边界，不必成为墙','群体之间，仍然可以有新的相遇。','dolly / reader carries a book between two tables'),
(175.0,'close','close','尾声 · 重新看见','看见连接，也记得连接之外的人','一条边帮助我们理解世界，却不能替代世界。','close / same book opens to a new relationship diagram'),
(183.2,'credits','credits','CLUSTERING LAB 05 · Su3037','邻居的颜色','标签传播聚类 · 二维图形动画 · 无配音','hold / credits over final book')]

# Dark technical revision: retain the accepted soundtrack and shot timings,
# replace the library metaphor with a computed circuit grouping problem.
revisions={
 'book':('circuit-hook','序 · 一个问题','按位置分，还是按连接分？','这些电路单元，你会按什么分组？'),
 'library':('geometric','序 · 一个问题','先试一条最直观的办法','按位置，整齐地划成三块。'),
 'table':('crossing','序 · 冲突','整齐的边界，切散了紧密的联系','跨组连接亮了起来：这份方案的权重和是 242。'),
 'morph':('local','序 · 另一种办法','如果每次，只看邻居呢？','不先画边界，让每个单元读一读相邻的标签。'),
 'tags':('tags','01 · 一条规则','先给每个点一个标签','节点的名字不变；标签可以在更新中改变。'),
 'weight-people':('weight','01 · 一条规则','两条细连接，还是一条粗连接？','两位邻居支持 B，一位支持 D。先别急着数人。'),
 'weight-scale':('weighted','01 · 一条规则','数的是权重','B 的权重是 1＋1；D 的权重是 4。D 胜。'),
 'sum':('tokens','01 · 一条规则','同一种标签，累计到一起','先按标签归类，再把对应边权相加。'),
 'setup':('board','02 · 五节点实验','先用五个点，看清一次更新','按 A 到 E 访问；平票时取字典序最小标签。'),
 'many':('many','04 · 回到开场','再回到刚才的 24 个单元','只读邻居的标签，让同一条规则继续运行。'),
 'city':('comparison','04 · 回到开场','从 242，到 2','这次运行得到三组、每组八个；跨组权重降到 2。'),
 'bridge':('bridge','04 · 条件与结果','再改一条边','课程五节点图的 C—D 改为 10，实际分组随之改变。'),
 'chip':('chip','05 · 走进设计','找到群体，只是开始','聚类结果可以成为粗化、初始分组的线索。'),
 'floorplan':('floorplan','05 · 走进设计','把紧密联系的部分，交给后续设计','分组不等于布局完成，更不等于芯片已经可用。'),
 'ribbons':('stopping','05 · 检查结果','停止原因，也属于结果','稳定、振荡、达到上限，需要分开报告。'),
 'return':('return','尾声 · 回答开场','现在，重新看待那两道边界','整齐只是外观。这个任务还要看连接与设计约束。'),
 'cross':('experiment','尾声 · 轮到你','让一条边变弱，或者变强','在实验室里改一条边，亲手检验你的猜想。'),
 'close':('close','尾声 · 重新看见','局部规则，整体结构','每次只读邻居，也能让群体逐步显现。')}
rows=[(r[0],r[1],*revisions[r[1]],r[6],*r[7:]) if r[1] in revisions else r for r in rows]

scenes=[]
for row in rows:
    at,id,visual,chapter,title,caption,camera,*event=row
    start=0 if not at else snap(at)
    s=dict(id=id,visual=visual,start=start,chapter=chapter,title=title,caption=caption,camera=camera)
    if event:s['event']=event[0]
    scenes.append(s)
for i,s in enumerate(scenes):
    end=scenes[i+1]['start'] if i+1<len(scenes) else round(m['duration']*30)/30
    s['duration']=end-s['start']
    s['actions']=[snap(s['start']+m['period']*k)-s['start'] for k in (2,4,6) if m['period']*k<s['duration']-.35]
    assert s['duration']>2
plan={'version':2,'fps':30,'duration':round(m['duration']*30)/30,
      'music':{'title':'We Never (Remix)（若如初见）','artists':'Hi Noise / 秋成','source':'https://www.bilibili.com/video/BV134Ho6qENu/','speed':1,'estimatedBPM':m['bpm_estimate'],
               'note':'User-selected exact upload; no additional 0.9x change. Third-party recording, excluded from project CC license.'},
      'scenes':scenes}
(ROOT/'video/storyboard-v2.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
# Analysis only; the source audio remains ignored, not a downloadable raw song.
(ROOT/'video/music-cues-v2.json').write_text(json.dumps({k:m[k] for k in ['duration','bpm_estimate','period','phase','grid','onsets','method']},indent=2))
print(len(scenes),'shots;',plan['duration'],'seconds; estimated BPM',m['bpm_estimate'])
