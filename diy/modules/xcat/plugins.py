# coding=utf-8
import functools
import sys
import xcat
import xcat.web

from xcat import cache, models
from .utils import Json, Date

from tornado.web import RequestHandler, UIModule
from tornado.util import import_object 



'''
  基于事件的插件机制

    Request 执行流程 ：

      on_init -> before_execute -> before_render -> on_finish

'''

_application = False
_work_plugins = []
_config = {}
_list = {}


# 注册 application
def register_app(application):
    global _application 
    application.xcat_is_sync()
    _application = application
    init()


'''
  在工作的插件列表

  格式：

  {
    'on_init' : [
        { 'targets' : ['app.controllers.admin.*'] , 'plugin' : pluginObj , 'callback' : 'on_init' } ,
        ...
    ] ,
    'before_execute' : [
        { 'targets' : ['app.controllers.admin.*'] , 'plugin' : pluginObj , 'callback' : 'before_execute' } ,
        ...
    ] ,
    ...
  }
'''



'''
  初始化
'''
def init():
    
    # 创建表
    xcat.Database.connect(xcat.Database.READ)
    if False == models.Plugins.table_exists():
        models.Plugins.create_table()
    
    reset()
    xcat.Database.close()

'''
  重置
'''    
def reset():
    global _list , _config , _work_plugins

    _work_plugins = []
    _config       = {}
    _list         = {}

    for plugin_ar in models.Plugins.select().order_by(models.Plugins.id.desc()):
        _work_plugins.append(plugin_ar.name)
        _config[plugin_ar.name] = Json.decode(plugin_ar.config)

        plugin = import_object(str(plugin_ar.name))

        
        if _application:
            # 绑定 ui_modules
            for v in Json.decode(plugin_ar.ui_modules):
                _application.ui_modules[v.__name__] = import_object(str(v))
            
            # 绑定 header
            for v in Json.decode(plugin_ar.handlers):
                plugin_module = v.split('.handlers.')[0] + '.handlers'
                
                if plugin_module not in sys.modules.keys() :
                    import_object(str(plugin_module))
                else:
                    reload(import_object(str(plugin_module)))


        binds = Json.decode(plugin_ar.bind,{})
        for event in binds:
            _list.setdefault(event,[])
            for v in binds[event]:
                v['handler'] = plugin
                v['name'] = plugin_ar.name
                _list[event].append(v)

    xcat.web.Route.acl(_application)
    xcat.web.Route.routes(_application)  
    #print _work_plugins


def get_work_names():
    global _work_plugins
    return _work_plugins

'''
  取可用插件列表
'''
def get_list():
    global _list
    return _list

'''
  取插件的配置
'''
def get_config(plugin_name,default = {}):
    global _config
    return _config.get(plugin_name,default)

def set_config(plugin_name,config):
    global _config
    pl_ar = models.Plugins.get(models.Plugins.name == plugin_name)
    pl_ar.config = Json.encode(config)
    pl_ar.save()
    _config[plugin_name] = config


'''
  调用对应的插件
'''
def call(event, that):
    target   = that.__class__.__module__ + '.' + that.__class__.__name__
    handlers = []
    target   = target.split('handlers.').pop()

    for v in get_list().get(event,[]):
        if v['target'].find('*') == -1 and v['target'] == target:
            handlers.append(v)
        else:
            key = v['target'].split('*')[0]
            if target.find(key) == 0 or v['target'] == '*' :
                handlers.append(v)
    return handlers


class Events(object):
    '''
    handler 事件绑定
    '''
               
    '''
      控制器初始化时执行

        注： 这时数据库连接还未打开
    '''
    @staticmethod
    def on_init(method):

        @functools.wraps(method)
        def wrapper(self):
            handlers = call('on_init', self)
     
            for v in handlers:
                plugin = v['handler']()
                # 设置上下文
                plugin._context = {
                    'self' : self ,
                }
                if False == getattr(plugin,v['callback'])():
                    return False
            
            return method(self)

        return wrapper

    # 控制器执行前调用
    @staticmethod
    def before_execute(method):

        @functools.wraps(method)
        def wrapper(self, transforms, *args, **kwargs):
            self._transforms = transforms

            handlers = call('before_execute', self)
     
            for v in handlers:
                plugin = v['handler']()
                # 设置上下文
                plugin._context = {
                    'transforms' : transforms ,
                    'args'       : args ,
                    'kwargs'     : kwargs ,
                    'self'       : self
                }
           
                if False == getattr(plugin,v['callback'])():
                    return False

                transforms = plugin._context['transforms']
                args       = plugin._context['args']
                kwargs     = plugin._context['kwargs']

            return method(self, transforms, *args, **kwargs)

        return wrapper

    # 渲染模板前调用
    @staticmethod
    def before_render(method):

        @functools.wraps(method)
        def wrapper(self, template_name, **kwargs):
            handlers = call('before_render', self)
     
            for v in handlers:
                plugin = v['handler']()
                # 设置上下文
                plugin._context = {
                    'template_name' : template_name ,
                    'kwargs'        : kwargs ,
                    'self'          : self
                }
                if False == getattr(plugin,v['callback'])():
                    return False
                template_name = plugin._context['template_name']
                kwargs        = plugin._context['kwargs']
            return method(self, template_name, **kwargs)

        return wrapper

    # 完成http请求时调用
    @staticmethod
    def on_finish(method):

        @functools.wraps(method)
        def wrapper(self):
            handlers = call('on_finish', self)
     
            for v in handlers:
                plugin = v['handler']()
                # 设置上下文
                plugin._context = {
                    'self' : self ,
                }
                if False == getattr(plugin,v['callback'])():
                    return False
            return method(self)

        return wrapper

# 卸载插件
def uninstall(plugin_name):
    global _application
    register = import_object(plugin_name.strip() + '.register')
    
    name = register._handler.__module__ + \
           '.' + register._handler.__name__

    ar = models.Plugins.select()\
               .where(models.Plugins.name == name)

    if ar.count() == 1 :
        plugin = import_object(name)()
        plugin.uninstall()

        models.Plugins.delete()\
              .where(models.Plugins.name == name)\
              .execute()

        # 通知 application 同步
        if _application:
            _application.xcat_sync_ping()


# 安装插件
def install(plugin_name):
    global _application
    register = import_object(plugin_name.strip() + '.register')
    
    name = register._handler.__module__ + \
           '.' + register._handler.__name__


    if models.Plugins.filter(models.Plugins.name == name).count() == 0 :       
        plugin = import_object(name)()
        plugin.install()

        # 尝试自加加载 ui_modules.py
        try:
            ui_modules = import_object(plugin_name + '.uimodules')
            for v in dir(ui_modules):
                if issubclass(getattr(ui_modules,v), UIModule) \
                and v != 'UIModule':
                    plugin.add_ui_module(v)
        except Exception, e:
            pass

        # 尝试自加加载 handlers.py
        try:
            handlers = import_object(plugin_name + '.handlers')
            reload(handlers)
            for v in dir(handlers):
              
                if issubclass(getattr(handlers,v), RequestHandler) \
                and v != 'RequestHandler':

                    plugin.add_handler(v)
        except Exception, e:
            pass


        handlers = []
        for v in plugin._handlers:
            handlers.append(
                v.__module__ + '.' + v.__name__
            )

        ui_modules = []
        for v in plugin._ui_modules:
            ui_modules.append(
                v.__module__ + '.' + v.__name__
            )

        pl = models.Plugins()
        pl.name        = name
        pl.bind        = Json.encode(register._targets)
        pl.handlers    = Json.encode(handlers)
        pl.ui_modules  = Json.encode(ui_modules)

        if plugin.get_form() :
            pl.config = Json.encode(plugin.get_form().get_default_values())
        pl.save()

        # 通知 application 同步
        if _application:
            _application.xcat_sync_ping()
        
class Register(object):
    '''
    插件注册表
    '''
    
    def __init__(self):
        self._handler = False
        self._targets = {}
        self._events  = (
            'on_init' , 
            'before_execute' , 
            'before_render' ,
            'on_finish' ,
        )

    # 注册对象
    def handler(self):
        def decorator(handler):
            self._handler = handler
            return handler
        return decorator

    # 绑定事件
    def bind(self, event, targets):
        def decorator(func):
            if event in self._events:
                self._targets.setdefault(event,[])
                for v in targets :
                    self._targets[event].append({
                        'target' : v ,
                        'callback' : func.__name__
                    })
            return func
        return decorator



class Base(object):
    """
      插件的基类
    """

    def __init__(self):

        self.model = self.__class__.__module__

  
        # 运行时的上下文
        self._context = {}

        # 插件的控制器
        self._handlers = []

        # ui modules
        self._ui_modules = []


    '''
      安装时执行

    '''
    def install(self):
        pass

    '''
      卸载时执行
    '''
    def uninstall(self):
        pass

    def get_form(self):
        return False

    # 取配置
    @property
    def config(self):
        return get_config( self.__class__.__module__ \
                           + '.' + self.__class__.__name__ , {} )

    def set_config(self, config):
        full_name = self.__class__.__module__ + '.' + self.__class__.__name__
        set_config(full_name, config)

    '''
      添加控制器
    '''
    def add_handler(self, handler):
        handler = self.__class__.__module__ + '.handlers.' + handler
        handler = import_object(handler)
        if handler not in self._handlers:
            self._handlers.append(handler)

    '''
      添加 UI models
    '''
    def add_ui_module(self, ui_module):
        ui_module = self.__class__.__module__ + '.uimodules.' + ui_module
        ui_module = import_object(ui_module)
        if ui_module not in self._ui_modules:
            self._ui_modules.append(ui_module)

