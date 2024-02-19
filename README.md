# Doudarr: 将豆瓣电影榜单转换为Radarr列表

## 介绍

Doudarr是一个将豆瓣电影榜单转换为Radarr列表的工具。它可以将任意豆瓣电影榜单中的电影列表转换为Radarr列表，从而实现自动监控豆瓣电影榜单中的电影，并自动下载。

![Cover](res/cover.png)

## 使用

* 使用Docker部署Doudarr:

```bash
docker run -d --name doudarr -p 8000:8000 -v /path/to/cache:/app/cache kfstorm/doudarr:latest
```

* 访问[http://localhost:8000/collection/movie_weekly_best](http://localhost:8000/collection/movie_weekly_best)，测试是否能够获取到豆瓣电影榜单中的电影列表。(对应的豆瓣网页为[https://m.douban.com/subject_collection/movie_weekly_best](https://m.douban.com/subject_collection/movie_weekly_best)。)
* 进入Radarr，在`设置 -> 列表`中新增一个列表，选择`Advanced List`中的`StevenLu Custom`，设置好参数后保存。一些常用参数：
  * 名称: 可以和豆瓣榜单的名字一样，方便记忆。
  * 启用自动添加：打开后会自动添加榜单里的电影到库中。（建议打开）
  * 添加时搜索：打开后在添加电影到库中时会自动开始搜索下载。（建议打开）
  * URL: URL的格式为`http://<Doudarr服务地址>/collection/<榜单ID>`。请根据需要修改Doudarr服务的地址以及榜单的ID，例如：`http://localhost:8000/collection/movie_weekly_best`。
* 片刻后，应该能看到Radarr自动添加了榜单中的电影。也可以在Radarr的`电影 -> 发现`中查看。（右上角`选项`里取消勾选`包含Radarr推荐`，右上角`过滤`里选择`全部`。）

## 注意事项

* 因为豆瓣的反爬策略，Doudarr限制了请求频率。首次启动Doudarr时，API请求较慢，需耐心等待。
* 记得将容器内的`/app/cache`目录映射到宿主机上，以免后续容器重建或升级时丢失缓存数据。

## 项目特色

* 支持任意豆瓣电影榜单。
* 使用IMDb ID作为电影的唯一标识，不会因为电影名字相近而导致添加错误的电影。

## FAQ

* 如何获取榜单ID？

在豆瓣手机App中，选择`书影音 -> 电影 -> 豆瓣榜单`，可以浏览所有的电影榜单。选择一个想要监控的榜单，点击进入，然后打开分享菜单，选择`复制链接`，即可获得榜单的URL。榜单URL的格式为`https://m.douban.com/subject_collection/<榜单ID>`，请注意剔除`?`后面的部分（包括`?`）。
