# coding=utf-8
import peewee 
import requests

from xcat.utils import Json, Filters, Date
from xcat.models import Model
from markupsafe import escape
from ..models import User

class Task(Model):
    """定时任务"""
    
    # 任务优先级
    level = peewee.IntegerField(max_length=2, index=True, default=0)
    # 要访问的url
    url = peewee.CharField()



class Metadata(Model):
    """wiki 元数据"""

    # 所属用户
    user = peewee.ForeignKeyField(User)
    # 用户判断文件是否更改
    hash_key = peewee.CharField(index=True)
    # 所在路径
    path = peewee.CharField(index=True)
    # 大小
    bytes = peewee.FloatField()
    # 是否目录
    is_dir = peewee.IntegerField(max_length=2, index=True)
    # 父级元数据的id
    root_id = peewee.IntegerField(default=0)
    # 取后修改时间
    modified = peewee.IntegerField(default=0)

    def directory(self,level=0):
        if 3 < level:
            return []
        # 列目录
        wiki_list = []
        ar = Metadata.select()\
                     .where(Metadata.root_id == self.id)\
                     .order_by(Metadata.is_dir.asc(),Metadata.id.asc())

        for v in ar:
            item = {
                'path' : v.path.strip('/'),
                'name' : str(v.path).split('/').pop().split('.')[0],
                'is_dir' : str(v.is_dir),
                'list' : []
            }
            if str(v.is_dir) == '1':
                item['list'] = v.directory(level+1)
            wiki_list.append(item)

        return wiki_list


    def remove(self):
        if '1' == str(self.is_dir):
            for v in Metadata.select()\
                             .where(Metadata.root_id == self.id):
                v.remove()

        # 删除内容
        data = Data.select()\
                   .where(Data.metadata == self)

        if data.count() != 0 :
            data.get().remove()

        # 删除事务
        task_affair = TaskAffairs.delete()\
                                 .where(TaskAffairs.metadata == self)\
                                 .execute()

        Metadata.delete()\
                .where(Metadata.id == self.id).execute()


class TaskAffairs(Model):
    """任务事务,同步失败后回滚"""

    # 对应的元数据
    metadata = peewee.ForeignKeyField(Metadata)

    # 添加的时间
    time = peewee.IntegerField(index=True)

    # 父事务
    parent = peewee.IntegerField(default=0)

    # 所有事务列表
    parents = peewee.CharField(default=',', index=True)

    # 是否目录
    is_dir = peewee.IntegerField(max_length=2)

    # 旧的同步id
    old_hash_key = peewee.CharField()

    @staticmethod
    def add(metadata, parent_id):
        """添加事务"""
        parent_id = int(parent_id)

        # 删除大于1天的旧事务
        TaskAffairs.delete()\
                   .where(
                        TaskAffairs.time <= (Date.time() - 3600 * 24) 
                    )\
                    .where(
                        TaskAffairs.metadata == metadata
                    )\
                    .execute()

        # 检验上级事务
        parent_affair = False
        if 0 != parent_id:
            parent_affair = TaskAffairs.select()\
                                       .where(TaskAffairs.id == parent_id)

            if 0 == parent_affair.count():
                parent_id = 0
            else:
                parent_affair = parent_affair.get()
                if parent_affair.metadata.id != metadata.root_id:
                    parent_id = 0

        # 创建事务
        task_affair = TaskAffairs()
        task_affair.metadata = metadata
        task_affair.time = Date.time()
        task_affair.is_dir = metadata.is_dir
        task_affair.old_hash_key = metadata.hash_key

        if parent_affair and 0 != parent_id:
            task_affair.parent = parent_id
            task_affair.parents = "%s%s," % (parent_affair.parents, parent_id)
            
        task_affair.save()
        return task_affair

    # 回滚事务
    def rollback(self):
        self.metadata.hash_key = self.old_hash_key
        self.metadata.save()

        if int(self.parent) != 0 :
            ids = str(self.parents).strip(',').split(',')
            if len(ids) > 0 :
                ar = TaskAffairs.select()\
                                .where(TaskAffairs.id << ids)\
                                .where(TaskAffairs.is_dir == 1)

                for v in ar:
                    v.metadata.hash_key = v.old_hash_key
                    v.save()



class Data(Model):
    """wiki 文件格式化后的数据"""

    # 所属用户
    user = peewee.ForeignKeyField(User)
    # 对应的元数据
    metadata = peewee.ForeignKeyField(Metadata)
    # 格式化后的数据
    html = peewee.TextField()
    # 源文件
    source = peewee.TextField()

    def remove(self):
        DataTags.delete()\
                .where(DataTags.data == self)\
                .execute()

        Data.delete()\
            .where(Data.id == self.id)\
            .execute()

    def build_tags(self):
        txt  = escape(Filters.to_text(self.source))
        from ..handlers.task.helper import extract_tags
        seg_list = extract_tags(txt) 
        #seg_list = list(seg_list)
       
        # 删除旧关联
        DataTags.delete()\
                .where(DataTags.data == self)\
                .execute()

        for tag in seg_list:
            tag = tag.replace('#', '').strip()
            if '' == tag:
                continue

            tags = Tags.select().where(Tags.tag == tag)

            if 0 == tags.count():
                tags = Tags()
                tags.tag = tag
                tags.save()
            else:
                tags = tags.get()

            data_tags = DataTags()
            data_tags.data = self
            data_tags.tag = tags
            data_tags.save()
            
       


class Tags(Model):
    """从 wiki 中提取的tags"""
    tag = peewee.CharField(index=True)


class DataTags(Model):
    """ wiki 跟 tag 关联"""
    data = peewee.ForeignKeyField(Data)
    tag  = peewee.ForeignKeyField(Tags)

