#!/bin/env python
# -*- coding:utf-8 -*-

# haproxy自动发现与监控

import urllib2
import commands

cmd = "ps -ef |grep haproxy |grep '\-f'"
instance = commands.getoutput(cmd)
if instance != '':
    cmd = "echo \"show stat\" |sudo socat /tmp/haproxy.socket stdio | awk -F ',' '{print $1,$2,$3,$5,$9,$10,$14,$16,$18,$25}'"
    stats = commands.getoutput(cmd)
    _list = stats.splitlines()
    l_stats = []
    for i in range(6, len(_list)):
        _l_stats = []
        for j in range(len(_list[i].strip().split(' '))):
            value = -1
            if _list[i].split(' ')[j] == 'UP':
                value = 1
            elif _list[i].split(' ')[j] == 'no':
                value = 0
            elif _list[i].split(' ')[j] == 'DOWN':
                value = 0
            else:
                value = _list[i].split(' ')[j]
            _l_stats.append(value)
#            d_stats[_list[0].split(' ')[j+1]] = '{host=%s, group=%s} %s' % (_list[i].split(' ')[1], _list[i].split(' ')[0],_list[i].split(' ')[j])
        l_stats.append(_l_stats)
    for m in range(3, len(_list[0].strip().split(' '))):
        if _list[0].strip().split(' ')[m] == 'bin' or _list[0].strip().split(' ')[m] == 'bout':
            print '# HELP %s info' % _list[0].strip().split(' ')[m]
            print '# TYPE %s counter' % (_list[0].strip().split(' ')[m])
        else:
            print '# HELP %s info' % _list[0].strip().split(' ')[m]
            print '# TYPE %s gauge' % (_list[0].strip().split(' ')[m])
        for i in range(len(l_stats)-1):
            print ('haproxy_%s{webSer="%s",node="%s"} %s' % (_list[0].strip().split(' ')[m], l_stats[i][0],l_stats[i][1],l_stats[i][m-1])) 
