#coding=utf-8

'''
  计划任务, 每分钟跑一次

  @author vfasky@gmail.com
'''
import os , sys
# 设置系统编码为utf8
reload(sys)
sys.setdefaultencoding('utf8')

# 加入第三方类库搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

import requests

# 加载程序配置
from wiki import config
# 引入Database
from xcat import Database

# 加载数据库配置
Database.load_config(
    config.settings['database'].get(config.settings['run_mode'], False)
)
Database.connect()

from wiki.models import wiki

# 按每个url 3秒超时算, 1分钟要get 20个url
for v in wiki.Task.select()\
                  .order_by(wiki.Task.level.desc())\
                  .limit(20):

    requests.get(v.url, timeout=2.8)
    print "get %s" % v.url
    # 删除任务
    wiki.Task.delete().where(wiki.Task.id == v.id).execute()


if 0 == wiki.Task.select().count():
    #没有需要执行的任务, 重新同步
    task = wiki.Task()
    task.level = 0
    host = '127.0.0.1:8180'
    if 'OPENSHIFT_APP_DNS' in os.environ:
        host = os.environ['OPENSHIFT_APP_DNS']
    task.url = "http://%s/task/sync" % host
    task.save()