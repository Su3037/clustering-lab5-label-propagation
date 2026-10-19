# 资料核对与设计来源

核对日期：2026-10-20。网页与论文支持下面列明的范围。公开制作拆解属于他人的分析，未把其逐帧测量当作本项目亲自测量，也未下载、复制或重新发布参考视频。

## 教师材料

- [Lab05 README](https://github.com/yongfu-li/eda-learning/blob/main/courses/learn_clustering/module02-01-label-propagation/README.md)：目标包括加权图上的同步与异步标签传播，提供实现与浏览器两条练习路径。
- [EXAMPLES](https://github.com/yongfu-li/eda-learning/blob/main/courses/learn_clustering/module02-01-label-propagation/EXAMPLES.md)、[CHECKLIST](https://github.com/yongfu-li/eda-learning/blob/main/courses/learn_clustering/module02-01-label-propagation/CHECKLIST.md)：指定小图默认访问顺序的结果为两轮、割边权重和3。完整图数据另见原目录 examples/tiny_graph.json。
- [参考求解器](https://github.com/yongfu-li/eda-learning/blob/main/courses/learn_clustering/common/advanced.py)：阅读实际 label_propagation 函数，核实异步立即更新、最小字典序平票、零变化确认轮。项目引擎为独立实现。
- [平台样式](https://github.com/yongfu-li/eda-learning/blob/main/platform/assets/site.css)、原课件图：观察米白背景、深绿标题、图解与文字并排的视觉逻辑。本项目重新设计，不分发教师课件和视频。

## 算法依据

- Raghavan, Albert, Kumara (2007), [Near linear time algorithm to detect community structures in large-scale networks](https://arxiv.org/abs/0709.2938)，Physical Review E 76, 036106。原研究的算法变体、顺序与平票处理不完全等同于课堂确定性加权变体；本项目默认严格对应课堂例子。论文展示同步更新可能出现的交替问题。

## Vibe 作品与制作观察

- [《运气的形状》原发布页](https://www.douyin.com/video/7690344836800913785)：公开页面核对片名、作者 Iwanau 与发布日期。借鉴“可见现象先出现、随后才引入概念”的叙事思路，不使用其画面与文案。
- [《信息论·比特之美》](https://www.douyin.com/video/7693917578917334291)：发布者说明使用字幕与配乐讲解，并从可操作的猜数问题逐步扩展。借鉴具体问题与逐步解释的关系。
- [《控制论·舵手之学》](https://www.douyin.com/video/7689866306497170697)：公开介绍用掌舵引入反馈，最后回到日常经验。本项目结尾也回到开头的图书馆类比，但限制类比范围。
- [HeyChengC 的公开作品拆解](https://github.com/HeyChengC/vibe-knowledge-film/blob/main/references/analysis.md)：二手制作分析提供短字幕、可计算图形、动作与句意对应、首尾呼应的观察。仅作为研究资料，不安装或执行其技能及工程。
- [worlds3 的作品工程说明](https://github.com/worlds3/vibe-knowledge)：展示用确定性时间函数产生动画、按音乐段落组织分镜的技术路线。我们使用本地原创 Pillow/FFmpeg 工程，不复制其代码、镜头或音乐。

## 音乐调查与实际选择

- [Bilibili 上的《运气的形状》转载页](https://www.bilibili.com/video/BV163aC6iEFj/)显示关联曲名《千年之后（氛围版）》。这只能说明该页面的曲目关联，不能据此认定所有同类视频都用它，也不能核实原发布音源和再分发许可。
- worlds3 的公开说明写明其 BGM 沿用其他项目，但没有给出足以覆盖本作公开发布的音源授权。未下载、嵌入该 BGM。
- 本作实际配乐：《邻居之间 / Between Neighbors》，由 scripts/compose_score.py 本地合成的原创器乐与事件提示音，不模仿或采样上述曲目。提供可替换音轨和无配音成片。没有使用收费音乐服务或付费生成 API。

## 本项目的创作取舍

片长由教学设计决定，不作为教师硬性规定。先用虚构借阅互动引出“连接强弱”，再回到加权图，展示每一步票数、确认轮、割边、振荡和局限。片尾提醒：图上的标签依赖连接与规则，不能当作一个人的本质，也不能从聚类推出因果。
