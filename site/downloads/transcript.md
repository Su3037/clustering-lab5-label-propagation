# 圈子从哪里来（v4）分镜与双语字幕

成片 379.64 秒，1920×1080，30 fps，无配音。

## 00:00:00.000 序 · 通讯录
画面：intro hits: names fall out of a contact list; the silent break draws who talks to whom

- 00:00:00.600 打开通讯录，几百个名字。  
  *Open your contacts: hundreds of names.*
- 00:00:04.800 要把他们分成几个圈子，你会怎么分？  
  *How would you sort them into circles?*
- 00:00:11.000 你不需要知道每个人是谁，  
  *You don't need to know who anyone is.*
- 00:00:14.400 只要看：谁和谁常联系。  
  *Just look at who keeps in touch with whom.*

## 00:00:17.410 title
画面：title card lands on the groove entry


## 00:00:24.850 序 · 通讯录
画面：good grouping: tight inside, few links between

- 00:00:25.000 好的分组：圈内联系紧，圈与圈之间联系少。  
  *A good grouping: tight inside, few links between.*
- 00:00:29.200 网络科学把这件事叫作“社群发现”。  
  *Network science calls this community detection.*

## 00:00:34.170 一 · 一个极简的办法
画面：2007 citation, then the real run on the contacts graph; circles gather on the fill

- 00:00:34.400 2007 年，三位研究者提出一个极简的办法。  
  *In 2007, three researchers proposed a strikingly simple method.*
- 00:00:38.600 每个人看看朋友们现在属于哪个圈子，  
  *Each person checks which circle their friends are in now,*
- 00:00:42.800 然后加入联系最多的那一个。  
  *and joins the one they are most connected to.*
- 00:00:47.000 一遍遍重复，圈子自己浮现。  
  *Repeat, and the circles appear on their own.*

## 00:00:51.180 二 · 芯片里的同一个问题
画面：the contacts dissolve into a die; zoom to cells and wires

- 00:00:51.400 同样的问题，藏在每一块芯片里。  
  *The same problem hides inside every chip.*
- 00:00:55.600 几百万个单元，由导线连成一张网。  
  *Millions of cells, wired into one network.*
- 00:00:59.800 设计时，EDA 软件要先把它们分成几块。  
  *To design it, EDA software first splits them into blocks.*
- 00:01:04.000 为什么要在乎怎么分？  
  *Why does the split matter?*

## 00:01:08.200 二 · 芯片里的同一个问题
画面：short wire inside a block, long wire across blocks

- 00:01:08.400 同一块里的单元，用短导线相连。  
  *Cells in the same block connect with short wires.*
- 00:01:12.600 分在两块的单元，只能靠长导线。  
  *Cells in different blocks need long wires.*
- 00:01:16.800 导线越长，信号越慢，也越耗电。  
  *Longer wires mean slower signals and more power.*
- 00:01:21.000 所以目标和通讯录一样：块内紧，块间少。  
  *So the goal matches your contacts: tight inside, few between.*

## 00:01:25.220 三 · 尺子与穷举
画面：the ruler splits 24 cells; the severed weight adds up

- 00:01:25.400 看一个 24 个单元的小例子。  
  *Take a small example: 24 cells.*
- 00:01:29.600 最直接的办法：拿尺子，按位置切成三块。  
  *The obvious approach: a ruler, three blocks by position.*
- 00:01:33.800 很整齐。可它切断了多少连线？  
  *Neat. But how much wiring does it cut?*
- 00:01:37.800 切断的权重是 88，全部 202：将近一半。  
  *It cuts weight 88 out of 202: almost half.*

## 00:01:42.500 三 · 尺子与穷举
画面：how many splits exist: real counts

- 00:01:42.700 那就试遍所有分法，挑最好的？  
  *Then why not try every split and keep the best?*
- 00:01:46.900 24 个单元平分三组，约 15.8 亿种分法。  
  *24 cells into three equal groups: about 1.58 billion ways.*
- 00:01:51.100 上百万个单元呢？分法的数字有 47 万位。  
  *A million cells? The count itself has 477,121 digits.*
- 00:01:55.300 一个个试，永远试不完。  
  *Trying them one by one would never finish.*

## 00:01:59.270 四 · 一条局部规则
画面：push into one cell; neighbours' labels travel in; the strongest wire lights

- 00:01:59.500 那就借用通讯录里的那条规则：  
  *So borrow the rule from your contacts:*
- 00:02:03.700 每个单元看看邻居们现在的标签，  
  *each cell looks at its neighbours' current labels,*
- 00:02:07.900 加入连接最强的那一组。  
  *and joins the group it is most strongly wired to.*
- 00:02:12.100 这就是标签传播。  
  *This is label propagation.*

## 00:02:16.160 四 · 一条局部规则
画面：the soft outro: what the one-line rule leaves open

- 00:02:16.600 规则只有一句话，细节却很要紧：  
  *One sentence of rule, but the details matter:*
- 00:02:21.400 “最强”怎么算？谁先更新？  
  *What counts as strongest? Who updates first?*
- 00:02:26.400 什么时候停？它一定会停吗？  
  *When does it stop? Does it always stop?*
- 00:02:33.600 下半部分，用老师给的五节点图，一层层拆开。  
  *In part two, we take it apart layer by layer on the teacher's five-node graph.*
- 00:02:39.000 停在这里想一想：如果是你，会怎么回答？  
  *Pause here: how would you answer them?*

## 00:02:50.600 interlude
画面：the track ends; part card for part two

- 00:02:57.000 九层，从浅到深。  
  *Nine layers, from shallow to deep.*

## 00:03:09.820 第 1 层 · 标签
画面：teacher's graph lands on the hits; name vs label register in the silent break

- 00:03:10.400 第一层：标签。  
  *Layer one: labels.*
- 00:03:14.600 开始时，每个点的标签就是自己的名字。  
  *At the start, every node's label is its own name.*
- 00:03:20.800 名字是身份，永远不变；  
  *The name is its identity and never changes;*
- 00:03:24.200 标签是归属，会被改写。  
  *the label is where it belongs, and it can be rewritten.*

## 00:03:27.230 第 2 层 · 怎样算最强
画面：two light votes against one heavy vote

- 00:03:27.400 第二层：“最强”怎么算？  
  *Layer two: what counts as strongest?*
- 00:03:31.600 A 的三个邻居里，B 和 C 带着标签 B，D 带着 D。  
  *Of A's three neighbours, B and C carry label B, D carries D.*
- 00:03:36.000 数人头，B 两票；加权重，B 只有 2，D 有 4。  
  *By headcount B has two votes; by weight B has 2 and D has 4.*

## 00:03:41.850 第 2 层 · 怎样算最强
画面：the rule written as one line, built during the drum roll

- 00:03:42.100 所以规则是：把同标签邻居的边权加起来，取最大。  
  *So the rule: add up edge weights per label, take the largest.*

## 00:03:47.440 第 3 层 · 一次更新
画面：C's accumulator, slowly

- 00:03:47.600 第三层：一次更新。看 C。  
  *Layer three: one update. Watch C.*
- 00:03:52.200 邻居 A、B 已经是 B；D 是 D，E 是 E。  
  *Neighbours A and B already carry B; D carries D, E carries E.*
- 00:03:56.600 同标签先相加：B 是 1 + 4 = 5，D 是 2，E 是 1。  
  *Same labels add up first: B is 1 + 4 = 5, D is 2, E is 1.*

## 00:04:01.000 第 4 层 · 一整轮
画面：A to E in order, asynchronous

- 00:04:01.200 第四层：一整轮，按 A 到 E 依次更新。  
  *Layer four: a full round, A to E in order.*
- 00:04:05.600 B 立刻读到 A 的新标签：这叫异步更新。  
  *B already sees A's new label: this is asynchronous updating.*
- 00:04:09.800 C 改为 B，就是刚才那一步。  
  *C becomes B, the step we just saw.*
- 00:04:13.800 D 改为 E，E 保持。第一轮结束。  
  *D becomes E, E stays. Round one ends.*

## 00:04:18.020 第 5 层 · 何时停止
画面：a full round with zero changes

- 00:04:18.200 第五层：什么时候停？再问一遍每个点。  
  *Layer five: when to stop? Ask every node again.*
- 00:04:22.400 整整一轮，没有一个点改变。  
  *A whole round, and no node changes.*
- 00:04:26.600 只有整轮零变化，才能确认稳定。  
  *Only a full round with zero changes confirms it is stable.*
- 00:04:30.800 否则后面的点一改，前面的点可能又要改。  
  *Otherwise a later change could force an earlier node to change again.*

## 00:04:35.040 第 6 层 · 同时还是轮流
画面：the twist: synchronous updates swap forever

- 00:04:35.400 第六层：如果所有点同时更新呢？  
  *Layer six: what if every node updates at once?*
- 00:04:39.600 两个点，各自读对方的旧标签——  
  *Two nodes, each reading the other's old label...*
- 00:04:43.800 A 变成 B，B 变成 A，再换回来：永远停不下来。  
  *A becomes B, B becomes A, and back again: it never stops.*
- 00:04:48.000 轮流更新时，B 读到 A 的新标签，两者一致。  
  *Taking turns, B reads A's new label and they agree.*

## 00:04:52.320 第 7 层 · 分得好不好
画面：weighted cutsize; strengthen C-D and the boundary moves on the fill

- 00:04:52.600 第七层：分得好不好？看被切开的边。  
  *Layer seven: is the split good? Look at the cut edges.*
- 00:04:56.800 C–D 权重 2，C–E 权重 1。  
  *C–D has weight 2, C–E has weight 1.*
- 00:05:01.000 cutsize 是被切开的权重之和：2 + 1 = 3。  
  *Cutsize is the sum of cut weights: 2 + 1 = 3.*
- 00:05:05.200 把 C–D 加强到 10，边界立刻移动。  
  *Strengthen C–D to 10 and the boundary moves.*

## 00:05:09.090 第 8 层 · 回到芯片
画面：the real run on 24 cells; groups surface on the fill

- 00:05:09.400 第八层：回到 24 个单元，每个从自己的标签出发。  
  *Layer eight: back to the 24 cells, each starting with its own label.*
- 00:05:13.600 颜色沿着最强的连线扩散。  
  *Colour spreads along the strongest wires.*
- 00:05:17.800 每一轮只读每条连线两次：工作量和连线数成正比。  
  *Each round reads every wire twice: the work grows with the number of wires.*
- 00:05:22.000 第 5 轮零变化。只切开 2，尺子切开 88。  
  *Round 5: no changes. It cuts 2; the ruler cut 88.*

## 00:05:25.980 第 9 层 · 它做不到的事
画面：group count, balance, visiting order

- 00:05:26.200 第九层：它做不到的事。  
  *Layer nine: what it cannot do.*
- 00:05:30.400 它不保证分成几组，也不保证每组一样大。  
  *It promises neither the number of groups nor equal sizes.*
- 00:05:34.600 换个访问顺序，标签名和轮数都可能变。  
  *Change the visiting order and label names and round counts can change.*
- 00:05:38.800 它给出的是线索，不是最终答案。  
  *It gives a clue, not a final answer.*

## 00:05:43.020 现实中的用法
画面：cluster first, then partition and place

- 00:05:43.200 在芯片设计中，聚类常用来先把紧密的单元收成团，  
  *In chip design, clustering often first gathers tightly wired cells,*
- 00:05:47.400 让电路图变小，再交给更精细的划分与布局。  
  *shrinking the netlist before finer partitioning and placement.*

## 00:05:51.400 现实中的用法
画面：contacts and chip side by side

- 00:05:51.600 通讯录里的圈子，芯片里的分块，是同一个问题。  
  *Circles in your contacts and blocks in a chip are the same problem.*
- 00:05:56.200 没有人画圈。圈子，从连接里长出来。  
  *No one draws the circles. They grow out of the connections.*

## 00:06:00.420 credits
画面：closing line, citations and credits

- 00:06:01.000 去实验室改一条边的权重，看看边界会怎么走。  
  *Open the lab, change one edge weight, and watch the boundary move.*
