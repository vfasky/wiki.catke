#!/usr/bin/env python
# coding: utf8
import os
from xcat.web import RequestHandler, route
from xcat.third import DropboxMixin
from xcat.utils import Json, Date
from tornado.web import asynchronous
from ..task.helper import markdown
from ...models import User, UserOAuth, Role, UserRole, wiki


@route(r"/")
class Index(RequestHandler):
    '''喵星人 wiki'''

    def get(self):
        path = os.path.join(self.settings['root_path'], 'README.md')
        html = ''

        if os.path.isfile(path):
            md_file = open(path)
            md = md_file.read()
            md_file.close()
            html = markdown(md)


        self.render('default/index.html', html=html)

@route(r"/login")
class Login(RequestHandler, DropboxMixin):
    '''登陆'''

    @asynchronous
    def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self._on_auth)
            return
        self.authorize_redirect(callback_uri=self.request.full_url())

    def _on_auth(self, user):
        if not user:
            return self.write_error(msg="未能取得用户信息")

        self.uid = user['uid']
        self.access_token = user['access_token']

        # 取用户详细信息
        self.dropbox_request('api', '/1/account/info/', 
                             self._on_check_user,
                             self.access_token
                            )

    def _on_check_user(self, response):
        # 检查用户信息
        user_info = Json.decode(response.body)
        response.rethrow()

        user_oauth = UserOAuth.select()\
                              .where(UserOAuth.source == 'dropbox')\
                              .where(UserOAuth.oauth_id == self.uid)

        # 判断用户是否已经注册
        if 0 == user_oauth.count():
            return self.reg_usr(user_info)

        # 更新 access_token
        user_oauth = user_oauth.get()
        user_oauth.set_token(self.access_token)
        user_oauth.save()

        user = user_oauth.user

        # 为用户进行登陆
        user.login(self)


        # 执行一次手动更新
        ar = wiki.Metadata.select()\
                          .where(wiki.Metadata.user == user)\
                          .where(wiki.Metadata.is_dir == 1)\
                          .where(wiki.Metadata.root_id == 0)

        # 墙的存在,可能初始化不成功,再执行
        if ar.count() == 0:
            self.add_task(
                route.url_for('task.SyncPath', user.id, 0),
                99
            )
        else:
            self.add_task(
                route.url_for('task.SyncPath', user.id, ar.get().id),
                1
            )
        
        self.redirect(route.url_for('wiki.Index'))

    def reg_usr(self, user_info):
        # 注册用户
        user = User()
        user.name  = user_info['display_name']
        user.email = user_info['email']
        user.reg_time = Date.time()
        user.save()

        # 绑定角色
        user_role = UserRole()
        user_role.user = user
        user_role.role = Role.get(Role.code == 'user')
        user_role.save()

        # 绑定 oauth
        user_oauth = UserOAuth()
        user_oauth.user = user
        user_oauth.oauth_id = self.uid
        user_oauth.set_token(self.access_token)
        user_oauth.save()

        # 为用户进行登陆
        user.login(self)

        # 添加同步任务
        self.add_task(
            route.url_for('task.SyncPath', user.id, 0),
            99
        )

        self.redirect(route.url_for('wiki.Index'))
  