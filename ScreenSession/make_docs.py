#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    make_docs.py : a script for generating html docs
#
#    Copyright (C) 2010-2011 Artur Skonecki http://github.com/skoneka
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import inspect
import re
import help
import six

TITLE = "screen-session"

img_base = "http://adb.cba.pl/screen-session/0.6.3/screenshots/"

HTML_BEG = \
    """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
<head>
<title>screen-session project</title>
<meta name="Generator" content="ScreenSession/make_docs.py">
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<meta name="keywords" content="screen-session, GNU Screen, utilities, tools, documentation, tmux, Screen">
<link rel="home" title="Home" href="http://adb.cba.pl">
</head>
<body bgcolor="#ffffff" text="#000000">
<a href="http://github.com/skoneka/screen-session"><img style="positIon: absolute; top: 0; right: 0; border: 0;" src="%(img_base)s/ribbon.png" alt="Fork me on GitHub"></a>
<h1 style="color: #990000;">screen-session</h1>
""" % \
    {'title': TITLE, 'version': help.VERSION, 'img_base': img_base}

HTML_END = """\
</body>
</html>
"""

MENU_ITEMS = (('index.html', 'About'), ('news.html', 'News'), 
              ('documentation.html', 'Documentation'),
              ('installation.html', 'Installation'),
              ('screenshots.html', 'Screenshots'),
              ('https://github.com/skoneka/screen-session/issues', 'Feedback'),
              ('https://github.com/skoneka/screen-session/downloads', 'Download'))

_urlfinderregex = re.compile(r'http([^\.\s]+\.[^\.\s]*)+[^\.\s]{2,}')

def linkify(text, maxlinklength):
    def replacewithlink(matchobj):
        url = matchobj.group(0)
        text = six.text_type(url)
        if len(text) > maxlinklength:
            halflength = maxlinklength / 2
            text = text[0:halflength] + '...' + text[len(text) - halflength:]

        return '<a href="' + url + '">' + text + '</a>'

    if text != None and text != '':
        return _urlfinderregex.sub(replacewithlink, text)
    else:
        return ''

def process_text(text):
    import re
    #text= re.findall(r"\b(?:(?:https?|ftp|file)://|www\.|ftp\.)[-A-Z0-9+&@#/%=~_|$?!:,.]*[A-Z0-9+&@#/%=~_|$]", text)
    text = linkify(text, 200)
    text = re.sub(' (?= )(?=([^"]*"[^"]*")*[^"]*$)', "&nbsp;", text)
    return text

def gen_menu(menu_items, current_url):
    menu = []
    for (url, title) in menu_items:
        if url == current_url:
            menu.append("""<b>%s</b>""" % title)
        else:
            menu.append("""<a href="%s">%s</a>""" % (url, title))
    return menu


def print_menu(menu):
    for (i, m) in enumerate(menu):
        if i != 0:
            print(' | ')
        print(m)


def start_page(url):
    menu = gen_menu(MENU_ITEMS, url)
    sys.stdout = open('www/%s' % url, 'w')
    print(HTML_BEG)
    print_menu(menu)
    for (murl, desc) in MENU_ITEMS:
        if murl == url:
            print("<h3>%s</h3>" % desc)
    return menu


def end_page(menu):
    import datetime
    today = datetime.date.today()
    date = today.strftime("%B %d, %Y")
    html = """
    <center>
    <h6>
    <a href="http://validator.w3.org/check?uri=referer">HTML 4.01 Transitional</a>&nbsp;
    Last modified: %s
    </h6>
    </center>
    """ % \
        date
    print(html)
    print(HTML_END)
    sys.stdout.close()


def write_index_redirect():
    sys.stdout = open('index.html', 'w')
    html = """\
<html>
<head>
<base href="www" />
<meta HTTP-EQUIV="REFRESH" content="0; url="index.html">
</head>
<a href="www/index.html">go to screen-session documentation</a>
<body>
</body>
</html>
"""
    print(html)
    sys.stdout.close()


def write_index():
    url = 'index.html'
    menu = start_page(url)
    print("<samp>")
    for line in open('README', 'r'):
        print(process_text(line) + '<br>')
    print("</samp>")
    end_page(menu)


def write_screenshots():
    url = 'screenshots.html'
    menu = start_page(url)
    images = (('saver-800x600.png', 'session saver'),
              ('layoutlist-800x600.png', 'layoutlist'),
              ('manager-800x600.png', 'sessions manager'),
              ('regions-800x600.png', 'regions tool'))
    for (f, desc) in images:
        print("""<br>%s<br><a href="%s"><img alt="%s screenshot" src="%s"></a><br><br>""" % \
            (desc, img_base + f, desc, img_base + 'thumbs/' + f))

    end_page(menu)


def write_installation():
    url = 'installation.html'
    menu = start_page(url)
    print("<samp>")
    for line in open('INSTALL', 'r'):
        print(process_text(line) + '<br>')
    print("</samp>")
    end_page(menu)


def write_gnu_screen():
    url = 'gnu_screen.html'
    menu = start_page(url)
    end_page(menu)


def write_news():
    url = 'news.html'
    menu = start_page(url)
    print("<samp>")
    for line in open('NEWS', 'r'):
        print(process_text(line) + '<br>')
    print("</samp>")
    end_page(menu)


def write_documentation():
    url = 'documentation.html'
    menu = start_page(url)
    helps_tools = []
    helps_saver = []
    help_main = None
    max_command_len = 0
    for (name, obj) in inspect.getmembers(help):
        if name.startswith('help_'):
            name = name.split('_', 1)[1]

            #text = str(obj)

            text = process_text(str(obj)).split('\n')
            for (l, line) in enumerate(text):
                if line.strip() == "":
                    icomment = l + 1
                    break
            if name.startswith('saver_'):
                name = name.split('_', 1)[1]
                if len(name) > max_command_len:
                    max_command_len = len(name)
                helps_saver.append((name, icomment, text))
            elif name == 'help':
                help_main = text
            else:
                if len(name) > max_command_len:
                    max_command_len = len(name)
                helps_tools.append((name, icomment, text))
    print("""screen-session is a collection of utilities for GNU Screen.<br><br>""")
    print("""<samp>""")
    for l in help_main[1:]:
        if l.startswith('Session saver modes:'):
            break;
        print("%s<br>\n" % l)
    print("""</samp>""")

    def doc_print_index_row(href, name, comment):
        print("""<tr><td><a href="#%s">%s</a></td><td>&nbsp;%s</td></tr>""" % \
            (href, name, comment))

    #for line in help_main:
    #    print("%s<br>"%line)

    print("""<h4>Session saver modes:</h4>""")
    print("""<table>""")
    for (name, icomment, text) in helps_saver:
        doc_print_index_row(name, name, text[icomment])
    print("""</table>""")
    print("""<h4>Tools:</h4>""")
    print("""<table>""")
    for (name, icomment, text) in helps_tools:
        doc_print_index_row(name, name.replace('_', '-'), text[icomment])
    print("""</table>""")

    for (name, icomment, text) in helps_saver:
        print("""<a name="%s"></a>""" % name)
        print("""<h3 style="color: #990000;"><b># %s</b></h3>""" % name.replace('_', '-'))
        print("""<samp>""")
        for l in text:
            print("%s<br>\n" % l)
        print("""</samp><hr>""")

    for (name, icomment, text) in helps_tools:
        print("""<a name="%s"></a>""" % name)
        print("""<h3 style="color: #990000;"># %s</h3>""" % name.replace('_', '-'))
        print("""<samp>""")
        for l in text:
            print("%s<br>\n" % l)
        print("""</samp><hr>""")
    end_page(menu)


if __name__ == '__main__':
    write_index()
    write_news()
    write_documentation()
    write_installation()
    # write_gnu_screen()
    write_screenshots()
