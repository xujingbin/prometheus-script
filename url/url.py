#!/bin/env python
# -*- coding:utf-8 -*-

# url监控


import urllib

l_url = ['http://10.0.0.93:8083/cg/ping.php',
         'http://10.0.0.221:8083/cg/ping.php']
p = []
for url in l_url:
    req = urllib.urlopen(url).code
    if req == 200:
        p.append((url ,1))
    else:
        p.append((url, 0))

print '''# HELP url_status info
# TYPE url_status gauge'''
for key,value in p:
   print  'url_status{url="%s"} %s' % (key, value)
