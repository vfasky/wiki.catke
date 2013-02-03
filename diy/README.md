Hi, 欢迎来 "喵客 wiki"
=====================

## 关于这网站

> 这是一个解决用 **Markdown** 写笔记, 难于同步及管理的网站

- 网站受 [farbox.com](http://www.farbox.com/) 启发
- 样式借鉴 [Mou](http://mouapp.com/)
- 网站处于 **内测阶段**
- 网站与 Dropbox 同步间隔是 15 分钟

## 如何使用?

- 你需要一个 [Dropbox](https://www.dropbox.com) 账号
- 通过这个 [页面](/login) 授权
- 然后在本机进入 Dropbox 目录 `Apps/catke-wiki/`, 创建并编辑 `index.md`
- 大概 **15** 分钟后, 打开这个 [页面](https://catke.sinaapp.com/wiki/) `^_^ (恭喜,你入门了)`

### 一些注意事项

- 文件夹及文件名不能太长, 因为我们支持的路径长度只有 **255** 个字符
- 网站在中国, 一些众所周知的, 我们不提供开放的 wiki ( 每个用户只能登陆查看自己的 wiki ); 当然, 这不符 wiki 精神, 所以当程序稳定下来, 我们就开源. 

## 关于wiki导航

导航是根据`文件夹`结构生成的, 目前支持三层

## 关于文章目录

```
## 表示一级目录
### 表示二级目录
#### 表示三级目录
```

很不幸, 我们仍然只支持三层

### 关于Markdown语法支持

- 支持 Markdown 标准[语法](http://wowubuntu.com/markdown/index.html)
- 支持 Table [语法](http://michelf.ca/projects/php-markdown/extra/#table)
- 支持 代码高亮

#### 代码高亮 demo


    ``` python
    print 'hello word!'
    ```

效果:

``` python
print 'hello word!'
```

## 关于网站管理

- 网站不会有任何管理面板, 一切添加,编辑,删除都在本机 或 [Dropbox](https://www.dropbox.com) 完成
- 网站对 Dropbox 文件的操作是 **只读** , 不会对你的文件有任何破坏性影响

## 一些 Markdown 写作工具

- [Mou](http://mouapp.com/) [osx]
- [MarkdownPad](http://markdownpad.com/) [window]
- [ReText](http://sourceforge.net/p/retext/home/ReText/) [linux]

## 关于开源

> 你可以从 [这里](#) 下载到源码, 欢迎 Fork

### 如何部署?

#### 在 openShift 上安装

> 假定你已经有 openShift 的账号, 并已经安装 `rhc` 客户端

## 需要帮助?

有问题联系二小, vfasky[at]gmail.com