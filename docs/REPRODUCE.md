# 视频与课件的复现

## 第二版主片（当前网站默认）

当前主片约3分10秒，34个二维镜头，1920×1080、30fps、H.264/AAC，无配音。没有使用写实生成图；场景、人物、物件与图形全部由代码绘制。字体需求同下方首版。

音乐使用用户指定的《We Never (Remix)（若如初见）》Hi Noise / 秋成，[来源BV134Ho6qENu](https://www.bilibili.com/video/BV134Ho6qENu/)，保持原上传速度。第三方音乐不属于项目CC许可，不随源码提供独立歌曲文件；复现者需自行取得适用的音源。不要把第一版的原创配乐误当成第二版音轨。

需要Node.js 20+、Python 3.10+、Pillow、NumPy、FFmpeg。将实际指定音源放在本地后：

```sh
node scripts/build-film-v2.mjs
python3 scripts/analyze_music.py /path/to/music.m4a build/private/research-v2/music-analysis.json
python3 scripts/plan_film_v2.py
python3 scripts/render_film_v2.py --music /path/to/music.m4a --preview
python3 scripts/render_film_v2.py --music /path/to/music.m4a
```

已提供 `video/storyboard-v2.json`、`video/music-cues-v2.json` 和 `data/film-v2.json`，分别保存当前镜头、实际音频标记和引擎推演。若只复现同一音轨的成片，可跳过分析与重新分镜；更换音轨必须重新规划镜头，不能只换背景音乐。

分镜脚本先拟合约112.925 BPM节拍，再在附近寻找实际瞬态，并量化到30fps帧；动画的标签写回、物件入场等关键时刻使用该时间。主片音量整体降至源录音的0.45，留出峰值余量；不改变速度。字幕、封面、章节表由第二版渲染器生成。

`tests/film-v2.test.mjs`检查新24节点图、反事实分组与引擎是否一致，并检查镜头覆盖、音频标记和动作时间的量化误差。自动时间检查不等同于人工听感评价，播放审阅仍然必要。

## 第一版与课堂慢速推演

网站另保留1分27秒的慢速五节点推演，来自第一版主片，适合课堂逐步讲解。`video/storyboard.json`、`render_film.py`、`compose_score.py`保留为第一版源工程，与第二版分开。

第一版运行需求：Node.js 20+、Python 3.10+、Pillow、NumPy、FFmpeg。macOS默认使用系统黑体和宋体，不分发字体文件。Linux可安装Noto CJK字体，或通过 `CLUSTER_SANS_FONT` 与 `CLUSTER_SERIF_FONT` 指定字体路径。

第一版原片229秒、原创合成配乐。重新构建时请先备份当前 `neighbors.mp4` 等文件，避免首版脚本覆盖第二版默认成片。课堂精讲是首版53–140秒的片段，不是第二版同一时间范围的片段。

## 可编辑课件

`site/downloads/label-propagation.pptx`的文字、图节点、连线和5张表格均为可编辑对象，封面引用本项目原创视频的一帧。无需重建就可以在PowerPoint等应用中修改。源工程是 `scripts/build_deck.mjs`。

本次构建使用Codex内置的 `@oai/artifact-tool` 2.8.99；这是实际使用环境，不假定它可以通过公共npm安装。脚本通过环境变量读取技能目录、Python与Node依赖位置。若有相同运行环境，可执行：

```sh
PRESENTATION_SKILL_DIR=/path/to/presentations/skill \
RUNTIME_PYTHON=/path/to/python3 \
RUNTIME_NODE=/path/to/node \
RUNTIME_NODE_MODULES=/path/to/node_modules \
node scripts/build_deck.mjs
```

在项目根目录链接相应 `node_modules` 后运行。构建器先渲染，再检查PPTX结构、尺寸、字体声明、原生表格和重新导入。最终目标文件已存在时，改用新文件名生成修订版，避免覆盖审阅稿。

工具的直接PDF导出缺少内置字体资源，因此本项目使用ReportLab把同一批渲染页包装成PDF预览。PDF不是编辑源文件，编辑请使用PPTX。网页预览也来自这批渲染页，并提供每页备注。

## 打包下载材料

```sh
python3 -m pip install reportlab
python3 scripts/package_materials.py
```

该步骤复制讲义、练习、备注、独立Python实现和样例JSON到网站下载区。习题正文由 `site/questions.js` 单一来源生成。静态站点的日常部署不重新渲染视频或PPT，直接发布已验证的文件。

## 数据一致性

JS引擎 `site/algorithm.js` 独立实现LP；`build-traces.mjs`运行它后产生 `data/traces.json`，视频与课件读取同一份推演记录。Python实现使用另一份逻辑，与JS交叉核对。图的结构与权重引用教师小图并标注来源，未分发教师原课件和视频。
