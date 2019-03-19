#!/bin/env python
# -*- coding:utf-8 -*-

# nginx自动发现与监控

import urllib2
import commands, signal


def handler(signum, frame):
    exit()
signal.signal(signal.SIGALRM, handler)
signal.alarm(1)
cmd = "ps aux |grep 'nginx: master'"
nginx_instance = commands.getoutput(cmd)
if nginx_instance != '':
    url = 'http://127.0.0.1:8887/nginx-status'
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    nginx_stats = response.read()
    _list = nginx_stats.splitlines()
    l_stats = []
    l_stats.append(_list[0].split(' ')[0] + '_' + _list[0].split(' ')[1] +_list[0].split(' ')[2])
    l_stats.append(_list[1].split(' ')[1] + ': ' + _list[2].split(' ')[1])
    l_stats.append(_list[1].split(' ')[2] + ': ' + _list[2].split(' ')[2])
    l_stats.append(_list[1].split(' ')[3] + ': ' + _list[2].split(' ')[3])
    l_stats.append('connections_' + _list[3].split(' ')[0] + ' ' + _list[3].split(' ')[1])
    l_stats.append('connections_' + _list[3].split(' ')[2] + ' ' + _list[3].split(' ')[3])
    l_stats.append('connections_' + _list[3].split(' ')[4] + ' ' + _list[3].split(' ')[5])
    
    for i in l_stats:
        print '''# HELP nginx_%s info
# TYPE nginx_%s counter
nginx_%s %s''' % (i.split(':')[0], i.split(':')[0], i.split(':')[0], i.split(':')[1])
signal.alarm(0)
