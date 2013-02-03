# coding=utf-8

import sys
import os

# 设置系统编码为utf8
code = sys.getdefaultencoding()
if code != 'utf8':
    reload(sys)
    sys.setdefaultencoding('utf8')

# 加入第三方类库搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# 加载程序配置
from {{project}} import config
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

# run app
from {{project}}.handlers import *
application = xcat.web.Application([], **config.settings)

# 为插件注册 application
xcat.plugins.register_app(application)

# 本地环境，启动 server
import tornado.ioloop
application.listen(config.settings['port'][config.settings['run_mode']])
tornado.ioloop.IOLoop.instance().start()