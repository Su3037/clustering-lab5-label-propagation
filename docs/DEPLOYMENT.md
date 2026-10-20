# 部署与访问

仓库：Su3037/clustering-lab5-label-propagation。创建时为private。2026-10-20，GitHub已接受此仓库 `build_type=workflow` 的Pages配置，返回公开站点地址。因此无需为了网页而公开整个仓库。

目标站点：https://su3037.github.io/clustering-lab5-label-propagation/

GitHub Pages通过Actions上传 `site/`。所有资源使用相对路径，适用于项目子路径。只发布原创教学资源、浏览器代码和公开教学样例，不发布Canvas资料、私人录音或转写。

私有仓库与公开网站是两件事：网站中的JS、媒体（包括含指定配乐的短片 circles.mp4）、PPT、PDF与下载材料可被任何访问者获取。仓库其余源码与历史仍由GitHub私有权限控制，GitHub页面链接对未授权访问者可能不可见。

代码在访问者浏览器执行，视频与文件由GitHub托管。网站不连接作者Mac、不访问作者磁盘或SSH，Mac关机后仍可使用。浏览器会在本机保存闯关进度与音效开关（localStorage，可导出、导入或清除），不收集个人身份，不上传实验输入。

工作流在main推送与手动触发时运行算法测试、Python交叉验证及静态资源检查，成功后才部署。PR执行检查，不授予外部PR部署权限。

账号套餐或平台政策改变可能影响私有仓库Pages可用性。若未来遇到限制，再选择适合的托管方式或由用户决定公开本作业仓库；不自动公开私人课程资料仓库。
