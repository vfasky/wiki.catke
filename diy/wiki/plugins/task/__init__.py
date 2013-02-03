#coding=utf-8
import peewee , os
from xcat.plugins import Base , Register , get_config
from ...models import wiki
"""
demo:
    self.add_task("/tasks/foo")
"""

class AddTask(object):
    """添加任务"""

    def __init__(self, handler):
        self.handler = handler
        self.handler.add_task = self.add
   
    def add(self, url, level=0):
        if url.find('/') == 0:
            url = 'http://%s%s' % (self.handler.request.host , url)
        task = wiki.Task()
        task.url = url
        task.level = level
        task.save()

        return task.id


# 注册表
register = Register()

@register.handler()
class Task(Base):
    """
    绑定添加任务接口
    """

    @register.bind('before_execute' , ['*'])
    def bind_task_queue(self):
        add_task = AddTask(self._context['self'])
   
     

