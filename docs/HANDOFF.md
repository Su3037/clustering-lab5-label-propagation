# 当前状态

媒体、16页课件与教学网站已完成并发布。本地浏览器功能验证、自动测试和线上资源HTTP检查均已通过。

仓库 Su3037/clustering-lab5-label-propagation 保持private，公开网站为 https://su3037.github.io/clustering-lab5-label-propagation/ 。网站由GitHub Pages托管，访客的实验计算在访客浏览器内完成，不依赖作者的Mac开机或本地预览服务。

成功部署记录：https://github.com/Su3037/clustering-lab5-label-propagation/actions/runs/39290218104 ，对应网站提交56de7b39820c5ee1b106823e49c8e3684680aa7d。之后的交付文档更新不触发重新部署。

线上首页、PPTX、PDF、精讲视频、课件图片和讲义均返回HTTP 200；主片Range请求返回206。公开站点的浏览器自动化读取持续超时，因此未把线上UI复测列为已通过；互动、移动端和视频播放/跳章节的浏览器检查是在相同发布文件的本地预览上完成。

GitHub CLI已认证Su3037。需要在gh与Git的进程环境里使用urllib.request.getproxies()返回的现有http/https代理；不需要修改系统设置或暴露任何凭据。

本地预览 python3 scripts/serve.py。

测试 npm test；python3 tests/crosscheck.py；python3 scripts/check_site.py。

教师Issue #4尚未评论、未关闭。需要用户先审阅成果。
