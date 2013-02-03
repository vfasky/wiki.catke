#!/usr/bin/env python
# coding: utf8
import os 
import math

from xcat.web import RequestHandler, route
from xcat.third import DropboxMixin
from xcat.utils import Json, Date
from tornado.web import asynchronous

from ..task.helper import markdown
from ...models import User, UserOAuth, wiki

@route(r"/task/sync")
class Sync(RequestHandler):
    """同步"""
    def get(self):
        # 分段同步, 每次同步 10 用户, 前期每 15 分钟同步一次
        
        # 总根目录数
        count = wiki.Metadata.select()\
                             .where(wiki.Metadata.root_id == 0)\
                             .where(wiki.Metadata.is_dir == 1)\
                             .count()

        # 计算要分多少段
        count = int( math.ceil( count / 10 ) )

      
        if 0 == count:
            self.add_task(route.url_for('task.SyncStep', 1))
            return
        for page in range(1, count):
            self.add_task(route.url_for('task.SyncStep', page))


@route(r"/task/sync-step/(\d+)$")
class SyncStep(RequestHandler):
    """分段同步"""

    def get(self, page):
        page = int(page)
        if page < 1:
            return 
        ar = wiki.Metadata.select()\
                          .where(wiki.Metadata.root_id == 0)\
                          .where(wiki.Metadata.is_dir == 1)\
                          .paginate(page, 10)\
                          .order_by(wiki.Metadata.id.asc())

        
        for v in ar:
            self.add_task(
                route.url_for('task.SyncPath', v.user.id, v.id),
                1
            )

@route(r"/task/sync-path/(\d+)-(\d+)$")
class SyncPath(RequestHandler, DropboxMixin):
    """同步目录下的文件"""

    @asynchronous
    def get(self, user_id, id):
        id = int(id)
        if id == 0:
            # 初始化根目录
            user = User.select().where(User.id == user_id)

            if 0 == user.count():
                self.write('Not User')
                return self.finish()

            user = user.get()
            path = '/'
            self.metadata = False

            if 0 != wiki.Metadata.select()\
                                 .where(wiki.Metadata.user == user)\
                                 .count():

                self.write('Has been initialized')
                return self.finish()
               
        else:
            metadata = wiki.Metadata.select()\
                           .where(wiki.Metadata.id == id)

            if 0 == metadata.count():
                self.write('Not Data')
                return self.finish()

            metadata = metadata.get()

            # 判断是否目录
            if '1' != str(metadata.is_dir):
                self.write('Not Dir')
                return self.finish()

            user = metadata.user
            path = metadata.path
            self.metadata = metadata

        self.user = user
        self.dropbox_request('api', 
                             '/1/metadata/sandbox%s' % path, 
                             self.callback,
                             user.access_token,
                             list="true")

    def callback(self, response):
        if response.error:
            self.write('Init User(%s) Metadata Error : %s' 
                        % (self.user.id, response.error) )
            return self.finish()

        json = Json.decode(response.body)

        if len(json.get('path','')) > 255:
            self.write('Path Too long.')
            return self.finish()
        
        hash_key = json.get('hash', False) or json.get('rev','')

        if '' == hash_key:
            # 中文目录,先删除处理
            self.metadata.remove()
            return self.finish()

        if self.metadata:
            metadata = self.metadata
            # 没有变更
            if hash_key == str(metadata.hash_key):
                return self.finish()
        else:
            # 初始化根目录
            metadata = wiki.Metadata()
            metadata.user = self.user
            metadata.path = json['path']
            metadata.bytes = json['bytes']
            metadata.is_dir = json['is_dir'] and 1 or 0

        if json.get('modified', False):
            metadata.modified = Date.str_to_time(json['modified'].split('+')[0], '%a, %d %b %Y %H:%M:%S ')
        
        metadata.hash_key = hash_key
        metadata.save()


        # 取目录下文件 path 列表, 与新数据比对
        # 存在的 path 删除, 列表中留下的path ,
        # 就是需要删除的 文件 / 目录
        path_list = []
        for v in wiki.Metadata.select(wiki.Metadata.path)\
                              .where(wiki.Metadata.root_id == metadata.id):
            path_list.append(v.path)

        for v in json.get('contents', []):
            if len(json['path']) < 255:
                if v['path'] in path_list:
                    path_list.remove(v['path'])

                is_dir = v['is_dir'] and 1 or 0
                hash_key = v.get('rev', False) or v['hash']

                if 0 == is_dir:
                    uri, ext = os.path.splitext(v['path'])
                    # 不支持的文件类型, 跳过
                    if ext.lower() not in self.settings['support_ext']:
                        continue  

                # 判断是否存在
                ar = wiki.Metadata.select()\
                                  .where(wiki.Metadata.root_id == metadata.id)\
                                  .where(wiki.Metadata.path == v['path'])\
                                  .where(wiki.Metadata.is_dir == is_dir)

                if ar.count() == 0:
                    ar = wiki.Metadata()
                    ar.user = self.user
                    ar.root_id = metadata.id
                    ar.path = v['path']
                    ar.is_dir = is_dir
                else:
                    ar = ar.get()
                    # 没有更改, 跳过
                    if hash_key == ar.hash_key:
                        continue   

                ar.bytes = v['bytes']
                ar.hash_key = hash_key
                if v.get('modified', False):
                    ar.modified = Date.str_to_time(v['modified'].split('+')[0], '%a, %d %b %Y %H:%M:%S ')
                ar.save()

                if v['is_dir']:
                    self.add_task(
                        route.url_for('task.SyncPath', self.user.id, ar.id),
                        1
                    )
                else:
                    self.add_task(
                        route.url_for('task.SyncFile', ar.id),
                        2
                    )
        
        # 删除不存在的文件/目录
        for v in path_list:
            ar = wiki.Metadata.select()\
                                  .where(wiki.Metadata.root_id == metadata.id)\
                                  .where(wiki.Metadata.path == v)
            if ar.count() != 0:                  
                ar.get().remove()
           

        self.finish()


@route(r"/task/sync-file/(\d+)$")
class SyncFile(RequestHandler, DropboxMixin):
    """同步文件"""

    @asynchronous
    def get(self, id):
        metadata = wiki.Metadata.select()\
                       .where(wiki.Metadata.id == id)

        if 0 == metadata.count():
            self.write('Not Data')
            return self.finish()

        metadata = metadata.get()

        # 判断是否目录
        if '1' == str(metadata.is_dir):
            self.write('Is Dir')
            return self.finish()

        user = metadata.user
        self.user = user
        self.metadata = metadata
        
        self.dropbox_request('api-content', 
                             '/1/files/sandbox%s' % metadata.path, 
                             self.callback,
                             user.access_token,
                             list="true")

    def callback(self, response):
        if response.error:
            self.write('get File(%s) Error : %s' 
                        % (self.metadata.id, response.error) )
            return self.finish()

        metadata = self.metadata

        uri, ext = os.path.splitext(metadata.path)
        ext = ext.lower().split('.').pop() 
        source = str(response.body)
        html = False

        if hasattr(self, 'format_%s' %  ext):
            html = getattr(self, 'format_%s' %  ext)(source)

        if html:
            data = wiki.Data.select()\
                            .where(wiki.Data.metadata == metadata)

        if 0 == data.count():
            data = wiki.Data()
            data.metadata = metadata
            data.user = self.user
        else:
            data = data.get()

        data.source = source
        data.html = html
        data.save()

        # 提取 tags
        data.build_tags()
    
        self.finish()

    def format_md(self, source):
        """格式化 markdown"""
        return markdown(source)






