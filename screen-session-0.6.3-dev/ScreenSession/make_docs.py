#!/usr/bin/env python2
import sys,inspect,re
import help

TITLE = "screen-session documentation (version: %s)"%help.VERSION

HTML_CSS = """
<style type="text/css">
.menu{
    width: 100%; /* The menu should be the entire width of it's surrounding object, in this case the whole page */
    background-color: #333;} /* dark grey bg */

.menu ul{
    margin: 0;
    padding: 0;
    float: left;}

.menu ul li{
    display: inline;} /* Makes the link all appear in one line, rather than on top of each other */

.menu ul li a{
    float: left; 
    text-decoration: none; /* removes the underline from the menu text */
    color: #fff; /* text color of the menu */
    padding: 10.5px 11px; /* 10.5px of padding to the right and left of the link and 11px to the top and bottom */
    background-color: #333;}

.menu ul li a:visited{ /* This bit just makes sure the text color doesn't change once you've visited a link */
    color: #fff;
    text-decoration: none;}

.menu ul li a:hover, .menu ul li .current{
    color: #fff;
    background-color:#0b75b2;} /* change the background color of the list item when you hover over it */
</style>
"""

HTML_BEG = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
<head>
<title>%s</title>
<meta name="Generator" content="Vim/7.3">
<meta http-equiv="content-type" content="text/html; charset=UTF-8">

<link rel="home" title="Home" href="http://adb.cba.pl">
%s
</head>
<body bgcolor="#ffffff" text="#000000">
<a title="go to the index page" href=index.html accesskey="0">&gt;&gt; Index</a>
</head>
<body bgcolor="#ffffff" text="#000000">
<a title="go to the index page" href=index.html accesskey="0">&gt;&gt; Index</a>
<h1 style="color: #990000;">%s</h1>
<h6>Last modified:&nbsp;&nbsp; 14 July 2011
<br>by:&nbsp;&nbsp;Artur Skonecki&nbsp;&nbsp;admin&lt;[at]&gt;adb.cba.pl</h6>
<br>
<br>
<hr>
 
"""%(TITLE, HTML_CSS, TITLE)

HTML_END = """\
<a title="go to the index page" href=index.html >&gt;&gt; Index</a>
</body>
</html>
"""

MENU_ITEMS = (
        ('index.html', 'index'),\
        ('modes.html', 'modes'),\
        ('installation.html', 'installation'),\
        ('screenshots.html', 'screenshots'),\
        ('about.html', 'about')\
        )

def gen_menu(menu_items, current_url):
    menu = []
    for url,title in menu_items:
        if url == current_url:
            menu.append("""<a href="%s"><b>%s</b></a>"""%(url,title))
        else:
            menu.append("""<a href="%s">%s</a>"""%(url,title))
    return menu

def print_menu(menu):
    print("""<div class="menu"><ul>""")
    for m in menu:
        print('<li>'+m+'</li>')
    print("""</ul><br style="clear:left"/></div>""")
'''
<div class="site-links">                                                                                  <a href="/de/downloads/">Downloads</a><span class="separator"> | </span><a href="/de/documentation/">Dokumentation</a><span class="separator"> | </span><strong>Bibliotheken</strong><span class="separator"> | </span><a href="/de/community/">Community</a><span class="separator"> | </span><a href="/de/news/">Neuigkeiten</a><span class="separator"> | </span><a href="/de/about/">ber Ruby</a>        </div>
'''
        
def start_page(url):
    menu = gen_menu(MENU_ITEMS, url)
    sys.stdout = open('www/%s' % url,'w')
    print(HTML_BEG)
    print_menu(menu)
    return menu

def end_page(menu):
    print_menu(menu)
    print(HTML_END)
    sys.stdout.close()

def write_index_redirect():
    sys.stdout = open('index.html' ,'w')
    print("""\
<html>
<head>
<base href="www" />
<meta HTTP-EQUIV="REFRESH" content="0; url="index.html">
</head>
<a href="www/index.html">go to screen-session documentation</a>
<body>
</body>
</html>
""")
    sys.stdout.close()
    
def write_index():
    url = 'index.html'
    menu = start_page(url)
    print("""<h3>index</h3>""")
    end_page(menu)

def write_screenshots():
    url = 'screenshots.html'
    menu = start_page(url)
    print("""<h3>screenshots</h3>""")
    end_page(menu)

def write_installation():
    url = 'installation.html'
    menu = start_page(url)
    print("""<h3>installation</h3>""")
    end_page(menu)

def write_about():
    url = 'about.html'
    menu = start_page(url)
    print("""<h3>about</h3>""")
    end_page(menu)

def write_modes():
    url = 'modes.html'
    menu = start_page(url)
    helps = []
    helps_saver = []
    print("""<h3>tools:</h3>""")
    print("""<ol>""")
    for name,obj in inspect.getmembers(help):
        if name.startswith('help_'):
            name = name.split('_',1)[1]
            #text = str(obj)
            text = re.sub(' (?= )(?=([^"]*"[^"]*")*[^"]*$)', "&nbsp;", str(obj))
            if name.startswith('saver_'):
                helps_saver.append((name.split('_',1)[1],text))
            else:
                helps.append((name,text))
                print("""<li> <a href="#%s">%s</a></li>"""%(name,name.replace('_','-')))

    print("""</ol>""")
    print("""<h3>session saver modes:</h3>""")
    print("""<ol>""")
    for name,text in helps_saver:
        print("""<li> <a href="#%s">%s</a></li>"""%(name,name))
    print("""</ol>""")

    for name,text in helps_saver:
        print("""<a name="%s"></a>"""%name)
        print("""<h3 style="color: #990000;"><b># %s</h3></b>"""%name.replace('_','-'))
        print("""<samp>""")
        for l in text.split('\n'):
            print("%s<br>\n"%l)
        print("""</samp><hr>""")

    for name,text in helps:
        print("""<a name="%s"></a>"""%name)
        print("""<h3 style="color: #990000;"># %s</h3>"""%name.replace('_','-'))
        print("""<samp>""")
        for l in text.split('\n'):
            print("%s<br>\n"%l)
        print("""</samp><hr>""")
    end_page(menu)
    
if __name__ == '__main__':
    #write_index_redirect()
    write_index()
    write_modes()
    write_installation()
    write_screenshots()
    write_about()
