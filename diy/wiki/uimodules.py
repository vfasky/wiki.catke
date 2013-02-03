# coding=utf-8

from tornado.web import UIModule
from xcat.web import Route
from .models import wiki, User

class Directory(UIModule):
    """wiki 目录"""
    def render(self):
        user = self.handler.current_user

        user_ar = User.get(User.id == user['user_id'])
        
        metadata = wiki.Metadata\
                       .select()\
                       .where(wiki.Metadata.user == user_ar)\
                       .where(wiki.Metadata.root_id == 0)\
                       .where(wiki.Metadata.is_dir == 1)

        if 0 == metadata.count():
            return ''

        wiki_list = metadata.get().directory()

        return self.render_string('wiki/sidebar.html', wiki_list=wiki_list)



