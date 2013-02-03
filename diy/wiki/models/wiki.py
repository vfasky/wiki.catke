# coding=utf-8
import peewee 
import requests

from xcat.utils import Json, Filters
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

       
        data = Data.select()\
                   .where(Data.metadata == self)

        if data.count() != 0 :
            data.get().remove()

        Metadata.delete()\
                .where(Metadata.id == self.id).execute()




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

