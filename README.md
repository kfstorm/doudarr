# Doudarr: 将豆瓣榜单/片单/豆列转换为Radarr列表

## 介绍

Doudarr是一个将豆瓣榜单/片单/豆列（以下统称`豆瓣列表`）转换为Radarr列表的工具。它可以将任意豆瓣列表中的电影列表转换为Radarr列表，从而实现自动监控豆瓣列表中的电影，并自动下载。

![Cover](res/cover.png)

## 使用

1. 使用Docker部署Doudarr: `docker run -d --name doudarr -p 8000:8000 -v /path/to/cache:/app/cache kfstorm/doudarr:latest`

2. 访问[http://localhost:8000/collection/movie_weekly_best](http://localhost:8000/collection/movie_weekly_best)，测试是否能够获取到该豆瓣列表中的电影列表。(对应的豆瓣网页为[https://m.douban.com/subject_collection/movie_weekly_best](https://m.douban.com/subject_collection/movie_weekly_best)。)

3. 进入Radarr，在`设置 -> 列表`中新增一个列表，选择`Advanced List`中的`StevenLu Custom`，设置好参数后保存。一些常用参数：

* 名称: 可以和豆瓣列表的名字一样，方便记忆。
* 启用自动添加：打开后会自动添加豆瓣列表里的电影到库中。（建议打开）
* 添加时搜索：打开后在添加电影到库中时会自动开始搜索下载。（建议打开）
* URL: 填写完整的Doudarr链接。（请参考[豆瓣列表链接与Doudarr链接的映射关系](#豆瓣列表链接与doudarr链接的映射关系)）

4. 片刻后，应该能看到Radarr自动添加了豆瓣列表中的电影。也可以在Radarr的`电影 -> 发现`中查看。（右上角`选项`里取消勾选`包含Radarr推荐`，右上角`过滤`里选择`全部`。）

## 豆瓣列表链接与Doudarr链接的映射关系

豆瓣列表的链接有两种格式，请根据情况选择对应的Doudarr链接。

| 豆瓣列表链接格式 | Doudarr链接格式 | Doudarr链接示例 |
| --- | --- | --- |
| `https://m.douban.com/subject_collection/<豆瓣列表ID>` | `http://<Doudarr服务地址>/collection/<豆瓣列表ID>` | `http://localhost:8000/collection/movie_weekly_best` |
| `https://www.douban.com/doulist/<豆瓣列表ID>/` | `http://<Doudarr服务地址>/doulist/<豆瓣列表ID>` | `http://localhost:8000/doulist/43556565` |

## 注意事项

* 因为豆瓣的反爬策略，Doudarr限制了请求频率。首次启动Doudarr时，API请求较慢，需耐心等待。
* 记得将容器内的`/app/cache`目录映射到宿主机上，以免后续容器重建或升级时丢失缓存数据。

## 公共服务地址

为了方便大家使用，可以使用公共的Doudarr服务：[https://doudarr.azurewebsites.net](https://doudarr.azurewebsites.net)。公共服务的IMDb ID缓存可能更全面，可以更快加载出豆瓣列表中的电影。

请注意，这是一个公共服务，不保证稳定性和可用性。如果有条件，建议自行部署Doudarr。

## 项目特色

* 支持任意豆瓣列表。
* 使用IMDb ID作为电影的唯一标识，不会因为电影名字相近而导致添加错误的电影。

## FAQ

* 如何找到喜欢的豆瓣列表？

在豆瓣手机App中，依次选择`书影音 -> 电影 -> 豆瓣榜单`，可以浏览所有的榜单/片单（也叫豆列）。选择一个想要监控的豆瓣列表，点击进入，然后打开分享菜单，选择`复制链接`，即可获得该豆瓣列表的URL。
