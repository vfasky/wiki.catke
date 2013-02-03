#coding=utf-8
import os
from .utils import md5
try:
    import pylibmc
except Exception, e:
    pass

class File(object):
    """基于文件的缓存"""

    cache_path = 'temp'

    def __init__(self):
        if False == os.path.isdir(self.cache_path):
            os.mkdir(self.cache_path)

    def get_path(self, key):
        return os.path.join(self.cache_path, '%s.cache' % md5(key))

    def get(self, key, default=None):
        path = self.get_path(key)
        if False == os.path.isfile(path):
            return default

        cache_file = open(path)
        data = cache_file.read()
        cache_file.close()
        return data

    def set(self, key, value):
        path = self.get_path(key)
        cache_file = open(path, 'w')
        cache_file.write(str(value))
        cache_file.close()


class SaePylibmc(object):
    """基于 sae MC 的缓存"""

    mc = False
    if 'SERVER_SOFTWARE' in os.environ:
        mc = pylibmc.Client()

    def get(self, key, default=None):
        ret = self.mc.get(key)
        if not ret:
            return default
        return ret

    def set(self, key, value):
        self.mc.set(key, value)


client = False
        
