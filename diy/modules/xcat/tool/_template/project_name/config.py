# coding=utf-8
import os

# app所在目录
app_path = os.path.dirname(__file__)
# 项目根目录
root_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
)


# 程序配置
settings = {
    'debug': True,
    'gzip': True,
    'cookie_secret': 'catke-Xcat-app',
    'app_path': app_path,
    'root_path': root_path,
    'static_path': os.path.join(root_path, 'static'),
    'template_path': os.path.join(app_path, 'views'),
    'autoescape': None,
    'run_mode': 'devel', #运行模式有: devel、deploy
    # 数据库
    'database': {
        'devel': {
            'adapter': 'Sqlite',
            'config': {
                'default' : {
                    'database': 'caeke.db',
                }
            }
        }
    },
    # session
    'session': {
        'devel': {
            'left_time': 3600 * 24,
            'storage': 'DB', # Memory,DB,SaePylibmc
            'model': 'xcat.models.Session'
        }
    },
    # 框架缓存方案
    'xcat_cache' : {
        'devel': 'File' ,
    },
    'acls': [],
    'login_url': '/login',
    'version': '1.0.0-dev',
    'port': {
        'devel': 8080,
        'deploy': 8080
    },

}