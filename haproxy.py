#!/bin/env python
# -*- coding:utf-8 -*-

# haproxy自动发现与监控

import urllib2
import commands

#cmd = "sudo ss -nlp |grep haproxy |awk '$4 ~/:80/ {print $4}'"
cmd = "ps -ef |grep 'haproxy -f' |grep -v grep"
instance = commands.getoutput(cmd)
if instance != '':
    cmd = "echo \"show stat\" |sudo /usr/local/bin/socat /tmp/haproxy.socket1 stdio | awk -F ',' '{print $1,$2,$3,$5,$9,$10,$14,$16,$18,$25}'"
    stats1 = commands.getoutput(cmd)
    cmd = "echo \"show stat\" |sudo /usr/local/bin/socat /tmp/haproxy.socket2 stdio | awk -F ',' '{print $1,$2,$3,$5,$9,$10,$14,$16,$18,$25}'"
    stats2 = commands.getoutput(cmd)
    _list = stats1.splitlines()
    _list2 = stats2.splitlines()
    l_stats = []
    for i in range(6, len(_list)):
        _l_stats = []
        for j in range(len(_list[i].strip().split(' '))):
            value = _list[i].split(' ')[j]
            if j>1:
                v_status = _list[i].split(' ')[j]
                value = -1
                if v_status == 'UP':
                    value = 1
                elif v_status == 'no':
                    value = 0
                elif 'DOWN' in v_status:
                    value = 0
                elif 'MAINT' in v_status:
                    value = -1
                else:
                    value = int(_list[i].split(' ')[j]) + int(_list2[i].split(' ')[j])
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
