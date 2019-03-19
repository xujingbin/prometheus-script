#!/bin/env python
# -*- coding:utf-8 -*-

# haproxy自动发现与监控

import urllib2
import commands
import json

#cmd = "sudo ss -nlp |grep haproxy |awk '$4 ~/:80/ {print $4}'"
cmd = "ps -ef |grep haproxy |grep '\-f'"
instance = commands.getoutput(cmd)
monit_keys={
    'qcur': 'gauge', 
    'scur': 'gauge',
    'bin': 'counter',
    'bout': 'counter',
    'econ': 'gauge',
    'wretr': 'counter',
    'status': 'gauge',
    'rate': 'gauge',
    'rate_lim': 'gauge',
    'rate_max': 'gauge',
    'req_rate': 'gauge',
    'req_rate_max': 'gauge',
    'dreq': 'gauge',
    'qtime': 'gauge',
    'ctime': 'gauge',
    'hrsp_1xx': 'gauge',
    'hrsp_2xx': 'gauge',
    'hrsp_3xx': 'gauge',
    'hrsp_4xx': 'gauge',
    'hrsp_5xx': 'gauge',
    'hrsp_other': 'gauge',
}
if instance != '':
    cmd = "echo \"show stat json\" |sudo /usr/local/bin/socat /tmp/haproxy.socket1 stdio"
    stats = json.loads(commands.getoutput(cmd))
    for (key, vtype) in monit_keys.items():
        print '# HELP haproxy_%s info' % key
        print '# TYPE haproxy_%s %s' % (key, vtype)
        for j in stats:
            for i in j:  
                if i.get('field').get('name') == 'pxname':
                    pxname=i.get('value').get('value')
                if i.get('field').get('name') == 'svname':
                    svname=i.get('value').get('value')
                if i.get('field').get('name') == key:
                    value = i.get('value').get('value')
                    if type(value) == unicode:
                        if value in 'UP OPPEN':
                            value = 1
                        else:
                            value = 0
                    print 'haproxy_%s{backend="%s",server="%s"} %s' % (key, pxname, svname, value)
