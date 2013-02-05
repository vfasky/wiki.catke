Hi, 欢迎来 "喵客 wiki" test
=====================

## 关于这网站

> 这是一个解决用 **Markdown** 写笔记, 难于同步及管理的网站

- 网站受 [farbox.com](http://www.farbox.com/) 启发
- 样式借鉴 [Mou](http://mouapp.com/)
- 网站处于 **内测阶段**
- 网站与 Dropbox 同步间隔是 15 分钟

## 关于开源

> 你可以从 [这里](https://github.com/vfasky/wiki.catke) 下载到源码, 欢迎 Fork

### 如何部署?

#### 在 openShift 上安装

> 假定你已经有 [openShift](https://openshift.redhat.com) 的账号, 并已经安装 `rhc` 客户端

##### 1. 创建 DIY 应用

[https://openshift.redhat.com/app/console/application_types?search=diy](https://openshift.redhat.com/app/console/application_types?search=diy)

![](http://ww3.sinaimg.cn/large/a74e55b4jw1e1gisoznojj.jpg)

点击`Do-It-Yourself`

![](http://ww3.sinaimg.cn/large/a74ecc4cjw1e1giv0jovrj.jpg)

##### 2. 登陆 ssh, 安装 python 2.7

访问 [https://openshift.redhat.com/app/console/applications/wiki](https://openshift.redhat.com/app/console/applications/wiki)

![](http://ww1.sinaimg.cn/large/a74ecc4cjw1e1gj2eplksj.jpg)

在终端登陆后, 按照 [这里](https://openshift.redhat.com/community/blogs/enabling-python-27-on-a-paas-with-the-openshift-diy-app-type) 的教程安装 python 2.7.3, Setuptools, PIP

> 注: 成功安装到 PIP 就行了
> 当然,你还需要在openShift添加 mysql, cron 服务


然后下载源码, 进入 `diy/wiki` 目录, 编辑 `config.py`

``` python
 'dropbox': {
      'key' : 'you Dropbox key', 
      'secret' : 'you Dropbox secret'
 }
```  

提交 git , 初始化完成后(大概需要 5 秒), 就能访问你的应用了
