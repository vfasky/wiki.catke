#!/usr/bin/env python
# coding: utf8
import jieba
import jieba.analyse
import misaka as m
from misaka import HtmlRenderer, SmartyPants
from markupsafe import escape
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

# Create a custom renderer 
class BleepRenderer(HtmlRenderer, SmartyPants):
    def block_code(self, text, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                escape(text.strip())
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(text, lexer, formatter)


renderer = BleepRenderer()
md = m.Markdown(renderer,
                extensions = m.EXT_FENCED_CODE \
                           | m.EXT_STRIKETHROUGH \
                           | m.EXT_SUPERSCRIPT \
                           | m.EXT_TABLES )

def markdown(text):
    return md.render(text)

def extract_tags(txt):
    return jieba.analyse.extract_tags(txt) 