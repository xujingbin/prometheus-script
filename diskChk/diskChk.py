#!/usr/bin/env python
# -*- coding: utf-8 -*-
#caiyiyoing
#20150513
#for zabbix 物理磁盘的低级别发现 用于坏道检测

import sys
import os
import platform
import re
import commands
#import monikey

sas_monit_keys = [
    ('Result_ok', 'gauge'),
    ('List', 'gauge'),
    ('Power_Up_hours', 'gauge'),
    ('Read_uncorr', 'gauge'),
    ('Write_uncorr', 'gauge'),
    ('Verify_uncorr', 'gauge'),

]
sata_monit_keys = [
    ('Result_ok', 'gauge'),
    ('List', 'gauge'),
    ('Power_Up_hours', 'gauge'),
    ('Reported_Uncorrect', 'gauge'),
    ('Media_Wearout_Indicator', 'gauge'),
    ('End_to_End_Error', 'gauge'),
]

def checkPythonVersionGt():
    #python version great then 2.4?
    pythonVersion = sys.version_info
    if pythonVersion[0] == 2 and pythonVersion[1] > 5:
        import subprocess
        import json
    else:
        try:
            import simplejson
        except ImportError:
            os.system('yum -y install python-simplejson ')

def getCmdResult(cmd):
    #get one line result
    if checkPythonVersionGt():
        ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    else:
        ret = os.popen(cmd).read().strip()
    return ret


# 循环所有disk设备
def get_info():
    cmd='sudo /usr/bin/python /usr/local/proms-agent/script/diskChk/hardware_collect.py diskInfo'
    diskAllinfo=[]
    diskAllstr=''
    diskinfo=eval(getCmdResult(cmd))
    for i in  diskinfo.values():
    	diskAllstr=diskAllstr+"\n"+"\n".join(i['diskDetail'])
    p = []
    for disk in  diskAllstr.split('\n'):
        p_everyDev = []
        if len(disk) != 0 and disk.split(':')[2] == "SAS":
            # 循环每个设备的所有指标
            for metric, mtype in sas_monit_keys:
                value = -1
                cmd = 'sudo /bin/bash /usr/local/proms-agent/script/diskChk/smart_sas_status.sh %s %s' % (disk.split(':')[0], metric)
                metric_value =  str(getCmdResult(cmd)) 
                if metric == 'Result_ok':
                    if metric_value == 'OK':
                        value = 1
                    else:
                        value = 0 
                else:
                    if metric_value == '':
                        metric_value = -1
                    value = metric_value
                p_everyDev.append('%s{dev="%s", type="sas"} %s' % (metric, disk.split(':')[0], value))
            p.append(p_everyDev)
            #print "SAS,id:"+disk.split(':')[0]+" Result_ok="+str(Result_ok)+" List="+str(List)+" Power_Up_hours="+str(Power_Up_hours)+" Read_uncorr="+str(Read_uncorr)+" Write_uncorr="+str(Write_uncorr)+" Verify_uncorr="+str(Verify_uncorr)
        elif len(disk) != 0 and disk.split(':')[2] != "SAS":
            for metric, mtype in sas_monit_keys:
                value = -1
                cmd = 'sudo /bin/bash /usr/local/proms-agent/script/diskChk/smart_sas_status.sh %s %s' % (disk.split(':')[0], metric)
                metric_value =  str(getCmdResult(cmd)) 
                if metric == 'Result_ok':
                    metric_value =  str(getCmdResult(cmd)) 
                    if metric_value == 'OK':
                        value = 1
                    else:
                        value = 0 
                else:
                    if metric_value == '':
                        metric_value = -1
                    value = metric_value
                    value = metric_value
                p_everyDev.append('%s{dev="%s", type="other"} %s' % (metric, disk.split(':')[0], value))
            p.append(p_everyDev)
    return p

# monitkey.py的两组都是6个指标 
if __name__ == '__main__':
    checkPythonVersionGt()
    p = get_info()
    for m in range(len(p[0])):
        print '# HELP %s info' % p[0][m].split('{')[0]
        print '# TYPE %s gauge' % (p[0][m].split('{')[0])
        for n in range(len(p)):
            print 'diskChk_%s' % p[n][m]
