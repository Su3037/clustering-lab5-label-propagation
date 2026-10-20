# 圈子从哪里来

Clustering Lab05 标签传播聚类的中文教学共建项目。作者 Su3037。

通讯录里的圈子，芯片里的分块，是同一个问题。这个项目用一部 6 分 20 秒的双语知识短片、九层由浅入深的讲解和一套闯关实验，讲清楚标签传播（label propagation）如何只靠一条局部规则，让群体从连接里浮现，以及它在芯片设计（EDA）中能做什么、不能做什么。

**[打开教学网页](https://su3037.github.io/clustering-lab5-label-propagation/)** · **[课堂课件预览](https://su3037.github.io/clustering-lab5-label-propagation/slides.html)**

仓库保持 private；GitHub Pages 网站公开可访问，网站中的代码和教学资源因此也可被访问。未公开任何私人课程录音或转写。

## 先看这些

| 内容 | 文件或入口 |
| --- | --- |
| 知识短片《圈子从哪里来》，6 分 20 秒，1080p，中英双语字幕，无配音 | [MP4](site/media/circles.mp4) |
| 课堂慢速推演（首版），1 分 27 秒 | [MP4](site/media/one-graph.mp4) |
| 九层讲义：从通讯录到芯片 | [讲义](docs/LEARN.md) |
| 分镜、双语字幕与文字稿 | [分镜](video/storyboard-v4.json) · [文字稿](video/transcript-v4.md) · [中文 VTT](site/media/circles.zh.vtt) · [English VTT](site/media/circles.en.vtt) |
| 剧本修改记录 | [第四版剧本说明](docs/research/film-v4-script.md) |
| 18 页可编辑课件，和短片同一条故事线，带讲解备注 | [PPTX](site/downloads/label-propagation.pptx) · [PDF](site/downloads/label-propagation.pdf) |
| 练习与解析 | [习题](docs/EXERCISES.md) |
| Python 独立实现 | [源码](src/label_propagation.py) |
| 研究与音乐来源 | [来源](docs/research/sources.md) |

### 短片结构

| 时间 | 段落 |
| --- | --- |
| 00:00 | 序：打开通讯录，几百个名字，怎么分圈子？（社群发现） |
| 00:34 | 2007 年 Raghavan、Albert、Kumara 的极简办法，在虚构通讯录上真实运行 |
| 00:51 | 芯片里的同一个问题：块内短线，块间长线 |
| 01:25 | 尺子切开 88 / 202；穷举：24 个单元约 15.8 亿种，一百万个单元的分法有 477,121 位 |
| 01:59 | 一条局部规则，和它留下的六个问题 |
| 03:09 | 下篇九层：标签 → 怎样算最强 → 一次更新 → 一整轮 → 何时停止 → 同时还是轮流 → 分得好不好 → 回到芯片 → 它做不到的事 |
| 05:43 | 现实中的用法（粗化）与结尾：没有人画圈，圈子从连接里长出来 |

配乐为用户指定的《We Never (Remix)（若如初见）》Hi Noise / 秋成（[来源](https://www.bilibili.com/video/BV134Ho6qENu/)），原速播放两遍，只随成片分发，不提供独立音轨。第三方音乐不属于本项目的 MIT 或 CC BY 许可。所有标签、票数、轮数与 cutsize 都由项目算法实际运行得出；通讯录与 24 单元电路是虚构的教学图。

## 网站

- **九层讲解**：每层一句结论、一段更深的细节、一个跳转到短片对应时间的按钮和一个关卡入口。
- **闯关实验《标签传播大冒险》**：借鉴 [Tcl Quest](https://github.com/Su3037/tcl-quest) 的游戏化设计。冒险地图分四个区域，九关对应九层讲解，外加两场 Boss（给通讯录分圈、芯片分块：比尺子的 88 分得更好）。每关有向导“签签”的说明、两级提示、首次通关 XP（共 1300 XP）、四枚区域徽章、等级称号、全屏庆祝和默认关闭的音效。答案全部由浏览器中的算法现场计算，不写死；答错不扣分。进度只存在本机浏览器，可导出或导入 JSON。
- **自由实验台**：逐个节点更新、整轮、自动播放；异步与同步、三种平票规则、可编辑访问顺序；新增短片里的通讯录和 24 单元电路；修改桥边权重、比较配置、加载自己的图、导出逐步记录。
- **练习**：10 道带解析的选择题。

不需要账号、后端或商业 EDA 软件，算法在访问者的浏览器运行。

## 本地启动

```sh
python3 scripts/serve.py
```

打开 http://127.0.0.1:8785/ 。请用 HTTP 服务打开，不要直接双击 HTML。浏览网站没有 npm 依赖。

## 运行与验证

Node.js 20+ 和 Python 3.10+：

```sh
npm test                          # 引擎、短片数据与闯关答案
python3 tests/crosscheck.py       # 271 组固定种子，JS 与独立 Python 实现逐节点比对
python3 tests/film_v3_crosscheck.py  # 短片用到的每个数字，用 Python 独立复算
python3 scripts/check_site.py     # 网页路径、媒体、章节、课件、下载文件，以及没有旧版本内容
python3 tests/test_preview.py     # 视频的字节范围请求（章节跳转需要）
```

教师指定小图正序异步、最小标签平票时，结果为 B/B/B/E/E，两轮确认，cutsize = 3。24 单元电路：标签传播 5 轮、三组各 8 个、cutsize = 2；按位置的尺子切法 cutsize = 88（总权重 202）。虚构通讯录：3 轮、cutsize = 4。

## 重建短片

短片由代码逐帧绘制（Pycairo + ffmpeg），数据来自同一个算法：

```sh
node scripts/build-film-v3.mjs        # 生成 data/film-v3.json：24 单元电路、通讯录和全部对照运行
node scripts/build-site-graphs.mjs    # 导出网站闯关用的图 site/film-graphs.js
python3 scripts/render_film_v4.py --stills        # 每个场景一张关键帧
python3 scripts/render_film_v4.py --start 0 --end 95  # 分段渲染无声画面，再用 ffmpeg 拼接
```

`scripts/render_film_v4.py` 复用 `scripts/render_film_v3.py` 的场景并按新的节奏重新映射时间，字幕与章节由 `video/storyboard-v4.json` 生成。配乐不在仓库中；混音时把指定音轨原速循环两遍、音量 0.45、结尾 1.5 秒淡出。详见 [复现指南](docs/REPRODUCE.md)。

课件、PDF 与网页预览由同一个脚本生成，数字读自短片数据：

```sh
python3 scripts/build_deck.py         # PPTX、PDF、site/slides 预览图与讲解备注
python3 scripts/package_materials.py  # 讲义、文字稿、练习等复制到网站下载区
```

## 教学改进

保留课程的基本概念与指定图，新增原创双语知识短片、九层讲解、闯关实验、同步振荡的可操作反例、投票明细、顺序对照、修改边权、独立实现交叉验证、练习解析和可编辑课堂材料。目标是学懂并改进讲解，不宣称提出了新算法。

教师 [Lab05 原材料](https://github.com/yongfu-li/eda-learning/tree/main/courses/learn_clustering/module02-01-label-propagation/)；对应认领 [Issue #4](https://github.com/yongfu-li/eda-learning/issues/4)。本项目不会自动发送成果评论或关闭教师 Issue，应先审阅成果。

## 复现与贡献

视频与 PPT 的构建见 [复现指南](docs/REPRODUCE.md)，部署见 [部署说明](docs/DEPLOYMENT.md)，课堂使用见 [展示提纲](docs/PRESENT.md)。

原创代码采用 MIT，原创教材、图解与视频画面采用 CC BY 4.0，具体范围见 LICENSE、LICENSE-CONTENT.md。教师原有视频和课件不在分发内容中。第三方音乐、工具和字体保留原许可，见 THIRD_PARTY_NOTICES.md。
