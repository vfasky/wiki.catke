#!/usr/bin/env python
# coding=utf-8
import os
import sys

# 设置系统编码为utf8
reload(sys)
sys.setdefaultencoding('utf8')

# 加入第三方类库搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# 加载程序配置
from wiki import config
from xcat import cache, Database

# 取缓存实例
cache.client = getattr(
    cache, 
    config.settings['xcat_cache'][config.settings['run_mode']]
)()

# 加载数据库配置
Database.load_config(
    config.settings['database'].get(config.settings['run_mode'], False)
)

import xcat.web
import xcat.plugins

from wiki import uimodules

# 加载UImodel
config.settings['ui_modules'] = uimodules

# run app
from wiki.handlers import *
application = xcat.web.Application([], **config.settings)

# 为插件注册 application
xcat.plugins.register_app(application)

# 安装定时任务插件
xcat.plugins.install('wiki.plugins.task')


if __name__ == "__main__":
    import tornado.ioloop
    address = os.environ.get('OPENSHIFT_DIY_IP','0.0.0.0')
    application.listen(
        config.settings['port'][config.settings['run_mode']],
        address=address
    )
    tornado.ioloop.IOLoop.instance().start()