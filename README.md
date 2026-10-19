# 邻居的颜色

Clustering Lab05 标签传播聚类的中文教学共建项目。作者 Su3037。

用一部原创知识短片、一份可编辑课件和一个逐节点实验，解释加权投票、异步与同步、访问顺序、平票、稳定确认和振荡。生活类比帮助建立直觉，算法与测试负责核实结果。

**[打开教学网页](https://su3037.github.io/clustering-lab5-label-propagation/)** · **[课堂课件预览](https://su3037.github.io/clustering-lab5-label-propagation/slides.html)**

仓库先保持 private。GitHub 已接受此私有仓库的 Pages 配置；发布后网站可以公开访问。公开网站中的代码和教学资源可被访问，并不随仓库私有而隐藏。未公开任何私人课程录音或转写。

## 先看这些

| 内容 | 文件或入口 |
| --- | --- |
| 原创知识动画，3分49秒，1080p，无配音 | [MP4](site/media/neighbors.mp4) |
| 五节点推演精讲，1分27秒 | [MP4](site/media/one-graph.mp4) |
| 16页可编辑课件，带讲解备注 | [PPTX](site/downloads/label-propagation.pptx) |
| 课件静态预览 | [PDF](site/downloads/label-propagation.pdf) |
| 从零学习的中文讲义 | [讲义](docs/LEARN.md) |
| 8道练习与解析 | [习题](docs/EXERCISES.md) |
| 分镜与字幕 | [分镜](video/storyboard.json)、[文字稿](video/transcript.md)、[VTT](site/media/neighbors.zh.vtt) |
| Python独立实现 | [源码](src/label_propagation.py) |
| 研究与音乐来源 | [来源](docs/research/sources.md) |

PDF是与PPT相同页面的图像预览，编辑请用PPTX。网页课件也可切页并阅读讲解备注。

## 动手实验

网站下方提供真实计算的标签接力实验室：

- 逐个节点更新、完成一轮、自动播放和暂停。
- 异步与同步，三种确定性平票规则，可编辑访问顺序。
- 修改桥边权重、加载自己的图、查看票数与逐节点记录。
- 对照不同规则的真实结果，导出本次JSON记录。
- 双节点振荡和孤点例子。
- 三项实践目标与即时习题解释，学习目标仅保存在当前浏览器。

不需要用户账号、后端、SSH或商业EDA软件。关掉作者的Mac不影响已部署网站。算法在访问者浏览器运行。

## 本地启动

```sh
python3 scripts/serve.py
```

打开 http://127.0.0.1:8785/ 。请用HTTP服务打开，不直接双击HTML。浏览网站没有npm依赖。

## 运行与验证

Node.js 20+ 和 Python 3.10+：

```sh
npm test
python3 tests/crosscheck.py
node scripts/build-traces.mjs
python3 src/label_propagation.py data/golden.json
python3 scripts/check_site.py
python3 tests/test_preview.py
```

`tests/crosscheck.py`用独立Python与JS实现在271个固定种子的配置上比较逐节点票数、标签、轮数、停止原因与cutsize。

教师指定小图正序异步、最小标签平票时，结果为 B/B/B/E/E，两轮确认，cutsize=3。这些数值不是任意输入的性质。

## 教学改进

保留课程的基本概念与指定图，新增原创中文知识动画、同步振荡的可操作反例、投票明细、顺序对照、修改边权、独立实现交叉验证、练习解析和可编辑课堂材料。目标是学懂并改进讲解，不宣称提出了新算法。

教师 [Lab05原材料](https://github.com/yongfu-li/eda-learning/tree/main/courses/learn_clustering/module02-01-label-propagation/)；对应认领 [Issue #4](https://github.com/yongfu-li/eda-learning/issues/4)。本项目不会自动发送成果评论或关闭教师Issue，应先审阅成果。

## 复现与贡献

视频与PPT的构建见 [复现指南](docs/REPRODUCE.md)，部署见 [部署说明](docs/DEPLOYMENT.md)，课堂使用见 [展示提纲](docs/PRESENT.md)。

原创代码采用MIT，原创教材、图解、配乐与视频采用CC BY 4.0，具体范围见 LICENSE、LICENSE-CONTENT.md。教师原有视频和课件不在分发内容中。第三方工具和系统字体保留原许可，见 THIRD_PARTY_NOTICES.md。
