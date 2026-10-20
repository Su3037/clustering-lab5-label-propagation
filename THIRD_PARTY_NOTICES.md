# 第三方工具与来源

- 教师Lab05定义、小图数据和参考结果来自 yongfu-li/eda-learning，对应链接见 docs/research/sources.md。本项目独立实现求解器、重写中文讲解并自行制作视觉材料，未分发教师原视频、原课件或私人课堂记录。
- 算法原研究：Raghavan, Albert, Kumara (2007), Physical Review E 76, 036106。使用数学概念并引用来源，未复制论文图版。
- Pillow（HPND）、NumPy（BSD-3-Clause）、ReportLab（BSD）与FFmpeg用于本地媒体构建，不随网站分发其程序。FFmpeg的实际构建许可取决于编译选项，见其官方说明 https://ffmpeg.org/legal.html 。
- 课件由 scripts/build_deck.py 生成：python-pptx（MIT）写出可编辑 PPTX，Pycairo（LGPL-2.1/MPL-1.1）绘制 PDF 与网页预览图。不随网站分发这些工具。
- 第四版短片由 Pycairo 逐帧绘制，使用 Noto Sans/Serif CJK SC（SIL OFL 1.1），字体文件未打包。
- PDF 与网页预览图嵌入 Noto Sans/Serif CJK SC 的字形（SIL OFL 1.1 允许嵌入）。PPTX 只声明 PingFang SC 与 Songti SC，不包含字体文件，缺字体时由演示软件替换。网站使用访问者已有字体。第一版短片使用 macOS 系统的 Heiti SC 与 Songti SC，字体文件未打包。
- 参考vibe作品用于叙事和镜头研究，不在网站分发参考画面、文案或代码。第一版配乐为原创合成；第二版与当前第四版主片《圈子从哪里来》使用用户指定的《We Never (Remix)（若如初见）》—Hi Noise / 秋成，来源 https://www.bilibili.com/video/BV134Ho6qENu/ ，保持原上传速度（第四版原速播放两遍）。该音乐不属于MIT或CC BY许可，也不提供独立音轨下载。

原创代码MIT与原创内容CC BY 4.0的覆盖范围见对应许可文件，不覆盖第三方内容。
