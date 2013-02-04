#!/usr/bin/env python
# coding: utf8
import os 

from xcat.web import RequestHandler, route
from xcat.utils import Json, Date
from tornado.web import asynchronous
from ..wiki.helper import get_title_by_html
from ..task.helper import markdown
from ...models import wiki, User

@route(r"/wiki/", allow=['user'])
class Index(RequestHandler):
    """wiki 首页"""

    def get(self):
        user = self.current_user

        # 检查 /index.md 是否存在
        user_ar = User.get(User.id == user['user_id'])
        ar = wiki.Metadata\
                 .select()\
                 .where(wiki.Metadata.user == user_ar)\
                 .where(wiki.Metadata.path == '/index.md')

        if 0 == ar.count():
            # 显示帮助页面
            path = os.path.join(self.settings['root_path'], 'README.md')
            html = ''

            if os.path.isfile(path):
                md_file = open(path)
                md = md_file.read()
                md_file.close()
                html = markdown(md)

        else:
            metadata = ar.get()
            ar = wiki.Data.select()\
                          .where(wiki.Data.metadata == metadata)

            if 0 == ar.count():
                
                self.add_task(
                    route.url_for('task.SyncFile', metadata.id),
                    99
                )
                return self.write_error(msg='页面正在同步中, 请稍候刷新')
            
            html = ar.get().html

        self.render('wiki/index.html',
                    html = html,
                    title = get_title_by_html(html)
                   )

  
@route(r"/wiki/(.+)$", allow=['user'])
class File(RequestHandler):
    """对应的 wiki 页面"""

    def get(self, path):
        path = "/%s" % path.strip()
        user = self.current_user

        # 检查 对应的页面 是否存在
        user_ar = User.get(User.id == user['user_id'])
        ar = wiki.Metadata\
                 .select()\
                 .where(wiki.Metadata.user == user_ar)\
                 .where(wiki.Metadata.path == path)

        if 0 == ar.count():
            return self.write_error(msg='页面不存在')

        metadata = ar.get()
        ar = wiki.Data.select()\
                      .where(wiki.Data.metadata == metadata)

        if 0 == ar.count():
            self.add_task(
                    route.url_for('task.SyncFile', metadata.id),
                    99
                )
            return self.write_error(msg='页面正在同步中, 请稍候刷新')

        ar = ar.get()

        # 查找相关wiki
        related = []
        for v in ar.get_related():
            item = {
                'tag' : v.tag.tag ,
                'url' : route.url_for('wiki.File', v.data.metadata.path.strip('/'))
            }
            related.append(item)
   

        html = ar.html

        self.render('wiki/index.html',
                    html = html,
                    title = get_title_by_html(html),
                    related = related
                   )