#!/usr/bin/env python
# coding: utf8


def get_title_by_html(html, default=''):
    """从html是提取h1"""
    temp = html.split('<h1>')
    if len(temp) == 1:
        return default

    try:
        return temp[1].split('</h1>')[0]
    except Exception, e:
        pass
    return default