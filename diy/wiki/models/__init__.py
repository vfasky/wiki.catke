# coding=utf-8
import peewee 
from xcat.utils import Json
from xcat.models import Model

class User(Model):
    """用户表"""
    
    name = peewee.CharField(max_length=100,unique=True)

    email = peewee.CharField(unique=True)

    # 注册时间
    reg_time = peewee.IntegerField()

    @property
    def access_token(self):
        # 取 oauth
        user_oauth = UserOAuth.select()\
                              .where(UserOAuth.user == self)\
                              .get()

        return user_oauth.get_token() 

    # 为用户进行登陆
    def login(self, handler):
        
        # 写入 session 
        handler.set_current_user({
            'user_id' : self.id,
            'username' : self.name,
            'roles' : self.role_codes(),
            'token': self.access_token
        })

    # 取角色代码
    def role_codes(self):
        codes = []
        for v in Role.select(Role.code).join(UserRole)\
                     .join(User).where(User.id == self.id):
            codes.append(v.code)
        return codes

    # 取角色id
    def role_ids(self):
        ids = []
        for v in Role.select(Role.id).join(UserRole)\
                     .join(User).where(User.id == self.id):
            ids.append(v.id)
        return ids

class Role(Model):
    """角色"""

    code = peewee.CharField(unique=True)
    name = peewee.CharField(null=True)
    
class UserRole(Model):
    """用户角色绑定"""

    # 对应的用户
    user = peewee.ForeignKeyField(User)
    # 对应的角色
    role = peewee.ForeignKeyField(Role)


class UserOAuth(Model):
    """用户 OAuth 授权表"""

    # 对应的用户
    user = peewee.ForeignKeyField(User)

    # oauth 来源
    source = peewee.CharField(default='dropbox')

    # oauth 的用户标识
    oauth_id = peewee.CharField(index=True)

    # 授权信息
    access_token = peewee.CharField(max_length=255)

    def set_token(self, access_token):
        self.access_token = Json.encode(access_token)

    def get_token(self):
        return Json.decode(self.access_token,None)
        

                        