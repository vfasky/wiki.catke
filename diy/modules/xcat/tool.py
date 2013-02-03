# coding=utf-8
# 命令行工具

import sys
import os
import shutil

# 设置系统编码为utf8
code = sys.getdefaultencoding()
if code != 'utf8':
    reload(sys)
    sys.setdefaultencoding('utf8')

root_path = os.path.abspath(os.path.dirname(__file__))

def create_app(path, project=None):
    '''
    创建 app
    ==========

    ## demo

    ```
    #!shell
    python tool.py create ~/github/local/test xcat-test
    ```

    '''
    path = os.path.abspath(path)

    if os.path.isdir(path):
        print('Error: 目录已经存在')
        return False
  
    if None == project:
        project = path.split(os.sep).pop()

    tpl_path = os.path.join(
        root_path, 
        'tool', '_template'
    )

    shutil.copytree(tpl_path, path)
    _build_app(path, project)

def _build_app(path, project):
    '''
    根据配置,重构项目
    '''
    app_path = os.path.join(path, 'app.py')
    project_path = os.path.join(path, project)
    # 改名
    os.rename(os.path.join(path, 'project_name'), project_path)
    if os.path.isfile(app_path):
        # 读文件
        app_file = open(app_path)
        app_soure = app_file.read().replace('{{project}}', project)
        app_file.close()

        # 重写文件
        app_file = open(app_path, 'w')
        app_file.write(app_soure)
        app_file.close()
    else:
        print 'Error: %s 不存在!' % app_path
        return False

    # 将 xcat 放入module
    xcat_path = os.path.join(path, 'modules', 'xcat')
 
    shutil.copytree(
        root_path, 
        xcat_path
    )
    


# 执行脚本
if len(sys.argv) > 1:
    action = sys.argv[1]
    args   = sys.argv[2:]

    if 'create' == action:
        create_app(*args)


