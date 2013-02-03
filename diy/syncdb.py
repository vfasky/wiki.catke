# coding=utf-8

'''
  同步数据表

  @author vfasky@gmail.com
'''
import os
import sys

# 设置系统编码为utf8
reload(sys)
sys.setdefaultencoding('utf8')

# 加入第三方类库搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# 加载程序配置
from wiki import config
# 引入Database
from xcat import Database

# 加载数据库配置
Database.load_config(
    config.settings['database'].get(config.settings['run_mode'], False)
)
Database.connect()

import wiki.models
import wiki.models.wiki

for m in dir(wiki.models):
    model = getattr(wiki.models, m)

    if m != 'Model' and str(type(model)) == "<class 'peewee.BaseModel'>":
        if model.table_exists() == False:
            try:
                model.create_table()
            except Exception, e:
                pass
    elif str(type(model)) == "<type 'module'>":
        for m2 in dir(model):
            model2 = getattr(model, m2)
            if m2 not in ('Model') and str(type(model2)) == "<class 'peewee.BaseModel'>":
                if model2.table_exists() == False:
                    try:
                        model2.create_table()
                    except Exception, e:
                        pass


# 执行安装
if 0 == wiki.models.Role.select().count():
    ar = wiki.models.Role()
    ar.code = 'admin'
    ar.name = '管理者'
    ar.save()

    ar = wiki.models.Role()
    ar.code = 'user'
    ar.name = '用户'
    ar.save()



Database.close()
