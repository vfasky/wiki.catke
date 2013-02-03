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
    'cookie_secret': 'catke-wiki-app',
    'app_path': app_path,
    'root_path': root_path,
    'static_path': os.path.join(root_path, 'static'),
    'template_path': os.path.join(app_path, 'views'),
    'autoescape': False,
    'support_ext': ('.md'),# 支持的扩展名
    'run_mode': 'devel',  # 运行模式有: devel、deploy
    # 数据库
    'database': {
        'devel': {
            'adapter': 'MySQL',
            'config': {
                'default': {
                    'host': '127.0.0.1',
                    'port': 3306,
                    'database': 'wiki',
                    'user': 'root',
                }
            }
        }
    },
    # session
    'session': {
        'devel': {
            'left_time': 3600 * 24,
            'storage': 'DB',  # Memory,DB,SaePylibmc
            'model': 'xcat.models.Session'
        }
    },
    # 框架缓存方案
    'xcat_cache': {
        'devel': 'File',
    },
    'acls': [],
    'login_url': '/login',
    'version': '1.0.0-dev',
    'port': {
        'devel': 8180,
        'deploy': 8080,
    },
    'dropbox': {
        'key' : '', 
        'secret' : ''
    },
}

if 'OPENSHIFT_DIY_IP' in os.environ:
    # OPENSHIFT 环境
    settings.update({
        'run_mode': 'deploy'
    })

    # 数据库配置
    settings['database']['deploy'] = {
        'adapter': 'MySQL',
        'config': {
            'default': {
                'host': os.environ['OPENSHIFT_MYSQL_DB_HOST'],
                'port': int(os.environ['OPENSHIFT_MYSQL_DB_PORT']),
                'database': os.environ['OPENSHIFT_GEAR_NAME'],
                'user': os.environ['OPENSHIFT_MYSQL_DB_USERNAME'],
                'passwd': os.environ['OPENSHIFT_MYSQL_DB_PASSWORD']
            }
        }
    }
    # session
    settings['session']['deploy'] = {
        'left_time': 3600 * 24,
        #'storage': 'Memory',
        'storage': 'DB', # Memory,DB,SaePylibmc
        'model': 'xcat.models.Session'
    }
    # 框架缓存
    settings['xcat_cache']['deploy'] = 'File'
