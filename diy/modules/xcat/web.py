#coding=utf-8

import time 
import re 
import os 
import types
import functools
import mimetypes
import uuid 
import xcat.session

from xcat import Database, cache, \
                 plugins, acl

from .utils import Json, Date
from tornado.escape import linkify
from tornado.util import import_object
from tornado.web import RequestHandler, url, \
                        StaticFileHandler, Application

from jinja2 import Environment, FileSystemLoader

# 添加 .htc 支持
mimetypes.add_type('text/x-component', '.htc')

class StaticFileHandler(StaticFileHandler):
    
    def get(self, path, include_body=True):

        uri, ext = os.path.splitext(path)
        if ext.lower() in ('.eot', '.woff', 'ttf'):
            self.set_header('Access-Control-Allow-Origin', '*')
        super(StaticFileHandler, self).get(path, include_body)
  

class RequestHandler(RequestHandler):

    # 存放路由
    _route = False

    def finish(self, chunk=None):
        super(RequestHandler,self).finish(chunk)
        self.on__finish()

    @plugins.Events.on_finish
    def on__finish(self):
        # 关闭主从数据库连接
        Database.close()
        

    # 用于绑定中间件
    def prepare(self):
        pass

    # 没有权限时的处理
    def on_access_denied(self):
        self.write_error(403)

    @plugins.Events.on_init
    def initialize(self):
        # 记录开始时间
        self._start_time = time.time()


        # 打开从库连接
        #xcat.Database.connect(xcat.Database.READ)

    def is_ajax(self):
        return "XMLHttpRequest" == self.request.headers.get("X-Requested-With")

    # 多国语言
    def _(self, txt, plural_message=None, count=None):
        if txt == None:
            return txt
        return self.locale.translate(unicode(str(txt),'utf8'),plural_message,count)


    @property
    def session(self):
        # 取 session 配置
        session_seting = self.settings['session'][self.settings['run_mode']]

        # 初始化 session
        if self.get_secure_cookie('PYSESSID'):
            return getattr(xcat.session , session_seting['storage'])(
                self.get_secure_cookie('PYSESSID'),
                session_seting['left_time'],
                session_seting
            )
            
        else:
            session = getattr(xcat.session , session_seting['storage'])(
                False,
                session_seting['left_time'],
                session_seting
            )
            self.set_secure_cookie('PYSESSID' , session.id())
            return session

    @plugins.Events.before_execute
    @acl
    def _execute(self, transforms, *args, **kwargs):
        return super(RequestHandler,self)._execute(transforms, *args, **kwargs)

    @plugins.Events.before_render
    def render(self, template_name, **kwargs):
        return super(RequestHandler,self).render(template_name, **kwargs)

    def render_string(self, template_name, **kwargs):
      
        context = {
            'Date' : Date ,
            'url_for' : Route.url_for ,
            '_' : self._ ,
            'handler' : self ,
            'request' : self.request ,
            'current_user' : self.current_user,
            'locale' : self.locale,
            'static_url' : self.static_url,
            'xsrf_form_html' : self.xsrf_form_html,
            'json_encode': Json.encode,
            'linkify': linkify,
        }
        context.update(self.ui)

        context.update(kwargs)

        template = self.application.jinja_env.get_template(
            template_name,
            parent=self.get_template_path()
        )
        return template.render(**context)
        #return super(RequestHandler,self).render_string(template_name, **kwargs)
        

    def set_current_user(self,session):
        self.session['current_user'] = session

    def get_current_user(self):
        return self.session['current_user']

    def get_error_html(self, status_code = 'tip', **kwargs):
        return self.render_string('error/%s.html' % status_code, **kwargs)

    def write_error(self, status_code = 'tip', **kwargs):
        if self.is_ajax() and kwargs.get('msg',False) :
            return self.write({
                'success' : False ,
                'msg' : kwargs.get('msg')
            })
        return super(RequestHandler,self).write_error(status_code, **kwargs)

    # 取运行时间
    def get_run_time(self):
        return round(time.time() - self._start_time , 3)
  

class Menu(object):
    """菜单定义"""

    _data = {
        'content' : [] ,
        'system' : [] ,
        'plugin' : [] ,
        'other' : [] ,
    }

    _type = [
        'content' , # 内容
        'system' , # 系统
        'plugin' , # 插件
        'other' , # 其它
    ]

    def __init__(self, type_name):
        if type_name not in self._type:
            type_name = 'other' 

        self.type_name = type_name


    def __call__(self, handler_class):
       
        item = {
            'url' : route.url_for(handler_class.route_name) ,
            'title' : handler_class.__doc__
        }
        if item not in self._data[self.type_name]:
            self._data[self.type_name].append(item)
    

        handler_class._menu = {
            'type_name' : self.type_name ,
            'item' : item , 
        }
        return handler_class

    @classmethod
    def remove(cls, item):
        if item['item'] in cls._data[item['type_name']]:
            cls._data[item['type_name']].remove(item['item'])
            
        #cls._list.remove(cls._list.index(item))
        #
    @classmethod
    def reset(cls):
        cls._data = {
            'content' : [] ,
            'system' : [] ,
            'plugin' : [] ,
            'other' : [] ,
        }

    @classmethod
    def list(cls):
        return cls._data

menu = Menu

'''
    表单加载器
'''
def form(name):

    def load(method):
        
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            #print self._locale.code
            form_name = name
            if name.find('.') == 0 :
                module_name = self.__class__.__module__
                if len(module_name.split('.')) == 4 :
                    arr = module_name.split('.')
                    arr.pop()
                    module_name = '.'.join(arr)
                form_name = module_name + '.forms' + name
    

            translate = None
            if hasattr(self,'_'):
                translate = self._

            
            # 加载表单
            self.form = import_object(form_name)(
                translate = translate ,
                handler = self
            )
            

            # 封装 form.validate
            def get_form_data():
                form = self.form
                args = self.request.arguments
                if form.validate(args):
                    return form.values()
                return False

            self.get_form_data = get_form_data

            return method(self, *args, **kwargs)

        return wrapper

    return load

class _404Handler(RequestHandler):


    def get(self, url):
        if hasattr(self,'is_reload'):
            return self.redirect(url)

        return self.write_error(404)

    def post(self, url):
        return self.get(url)


"""
    extensions.route

    Example:

    @route(r'/', name='index')
    class IndexHandler(tornado.web.RequestHandler):
        pass

    class Application(tornado.web.Application):
        def __init__(self):
            handlers = [
            # ...
            ] + Route.routes()

    @link https://github.com/laoqiu/pypress-tornado/blob/master/pypress/extensions/routing.py
"""
class Route(object):

    _routes   = {}
    _acl = []
    

    def __init__(self, pattern,  kwargs={}, name=None, host='.*$', allow=None, deny=None):
        self.pattern = pattern
        self.kwargs = {}
        self.name = name
        self.host = host
        self.allow = allow
        self.deny  = deny


    def __call__(self, handler_class):
      
        URI   = handler_class.__module__ + '.' + handler_class.__name__
        name  = self.name or URI.split('.handlers.').pop()
        handler_class.route_name = name

        # acl
        allow = self.allow 
        deny  = self.deny 
        
        if allow or deny:
            index = False
            for acl in self._acl:
                if acl['URI'] == URI:
                    index = self._acl.index(acl)
                    break
     
            if False == index:
                item = {'URI' : URI, 'allow' : [], 'deny' : []}
                self._acl.append(item)
                index = self._acl.index(item)
    
            if allow:
                for r in allow:
                    if r not in self._acl[index]['allow']:
                        self._acl[index]['allow'].append(r)
                        
            if deny:
                for r in deny:
                    if r not in self._acl[index]['deny']:
                        self._acl[index]['deny'].append(r)
                    

        spec = url(self.pattern, handler_class, self.kwargs, name=name)

        self._routes.setdefault(self.host, [])
        if spec not in self._routes[self.host]:
            self._routes[self.host].append(spec)

        # 存放路由规则
        handler_class._route = spec
        return handler_class

    @classmethod
    def reset(cls):
        cls._acl = []
        cls._routes = {}

    @classmethod
    def reset_handlers(cls,application):
        settings = application.settings

        # 重置 handlers
        if settings.get("static_path") :
            path = settings["static_path"]
         
            static_url_prefix = settings.get("static_url_prefix",
                                             "/static/")
            static_handler_class = settings.get("static_handler_class",
                                                StaticFileHandler)
            static_handler_args = settings.get("static_handler_args", {})
            static_handler_args['path'] = path
            for pattern in [re.escape(static_url_prefix) + r"(.*)",
                            r"/(favicon\.ico)", r"/(robots\.txt)"]:

                item = url(pattern, static_handler_class, static_handler_args)
                cls._routes.setdefault('.*$', [])
                if item not in cls._routes['.*$'] :
                    cls._routes['.*$'].insert(0, item) 

        # 404
        item = url(r"/(.+)$", _404Handler)
        if item not in cls._routes['.*$'] :
            cls._routes['.*$'].append(item) 
                    
        


    @classmethod
    def acl(cls, application=None):
        if application:
            application.settings['acls'] = cls._acl
        else:
            return cls._acl
    
    @classmethod
    def routes(cls, application=None):
        if application:
            cls.reset_handlers(application)
            application.handlers = []
            application.named_handlers = {}
            for host, handlers in cls._routes.items():
                application.add_handlers(host, handlers)

  
        else:
            return reduce(lambda x,y:x+y, cls._routes.values()) if cls._routes else []

    @classmethod
    def url_for(cls, name, *args):
        named_handlers = dict([(spec.name, spec) for spec in cls.routes() if spec.name])
        if name in named_handlers:
            return named_handlers[name].reverse(*args).replace('%2F','/')
        raise KeyError("%s not found in named urls" % name)


route = Route


class Application(Application):
    _sync_id = 0
    _c_sync_key = 'xcat.web.Application.id'
    

    def xcat_sync_ping(self):
        # 更新同步信号    
        self._sync_id = str(uuid.uuid4())
        # 同步 id
        cache.client.set(self._c_sync_key, self._sync_id)
        
        self.xcat_reload()

    def xcat_is_sync(self):
        return self._sync_id == cache.client.get(self._c_sync_key, 0)


    def xcat_sync(self):
        # 标记已经同步
        self._sync_id = cache.client.get(self._c_sync_key, 0)

    def xcat_reload(self):

        Route.reset()
        Menu.reset()

        # 重新加载 app handlers
        app_handlers = self.settings['app_path'].split(os.path.sep).pop() + '.handlers'
        handlers = import_object(app_handlers)
     
        for name in handlers.__all__:
            handler_module = import_object(app_handlers + '.' + name)
            reload(handler_module)
            for v in dir(handler_module):
                o = getattr(handler_module,v)
                if type(o) is types.ModuleType:
                    reload(o)
                
              
        # 重载插件   
        plugins.reset()

        # 标记已同步
        self.xcat_sync()

   

    def __init__(self, handlers=None, default_host="", transforms=None,
                 wsgi=False, **settings):

        # 配置 jinja2
        self.jinja_env = Environment(
            loader = FileSystemLoader(settings['template_path']),
            auto_reload = settings['debug'],
            autoescape = settings['autoescape']
        )

        return super(Application,self).__init__(
            handlers,
            default_host,
            transforms,
            wsgi,
            **settings
        )


    def __call__(self, request):

        if False == self.xcat_is_sync():
            #print '同步'
            self.xcat_reload()
            
        return super(Application,self).__call__(request)

