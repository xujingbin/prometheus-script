#!/usr/bin/python
# -*- coding:utf8 -*-

import commands,subprocess
import re
import os
import sys, signal


def handler(signum, frame):
     exit()

def print_cpu_stat():
    p = {}
    with open('/proc/stat') as f:
        cpu_stat = f.readline()
    if os.path.exists('/dev/shm/cpu_stat'):
        with open('/dev/shm/cpu_stat', 'r') as f:
            cpu_stat_pre = f.read()
        with open('/dev/shm/cpu_stat', 'w') as f:
            f.write(cpu_stat)
    else:
        with open('/dev/shm/cpu_stat', 'w') as f:
            f.write(cpu_stat)
    cpu_stat = cpu_stat.split()
    cpu_stat_pre = cpu_stat_pre.split()
    total = 0
    for i in range(1, 9):
        total += (float(cpu_stat[i]) - float(cpu_stat_pre[i]))
    p['us'] = ((float(cpu_stat[1]) - float(cpu_stat_pre[1]))) / total * 100
    p['sy'] = ((float(cpu_stat[3]) - float(cpu_stat_pre[3]))) / total * 100
    p['id'] = ((float(cpu_stat[4]) - float(cpu_stat_pre[4]))) / total * 100
    p['wa'] = ((float(cpu_stat[5]) - float(cpu_stat_pre[5]))) / total * 100
    p['core_num'] = float(commands.getoutput('cat /proc/cpuinfo |grep processor |wc -l'))
    for key in p:
        print ('# HELP cpu_%s info' % key)
        print ('# TYPE cpu_%s gauge' % key)
        print ('cpu_%s %.2f' % (key, p[key]))

def print_load_stat():
    f = open("/proc/loadavg")
    con = f.read().split()
    f.close()
def print_load_stat():
    f = open("/proc/loadavg")
    con = f.read().split()
    f.close()
    print ('# HELP loadavg_1 info')
    print ('# TYPE loadavg_1 gauge')
    print ('loadavg_1 %s' % con[0])
    print ('# HELP loadavg_5 info')
    print ('# TYPE loadavg_5 gauge')
    print ('loadavg_5 %s' % con[1])
    print ('# HELP loadavg_15 info')
    print ('# TYPE loadavg_15 gauge')
    print ('loadavg_15 %s' % con[2])

'''Return the information in /proc/p 
as a dictionary'''
def print_mem_stat():
    monit_keys = ['MemTotal', 'Cached', 'Buffers', 'MemFree', 'SwapTotal', 'SwapFree']
    stat_regex = re.compile(r'(\w+)\:\s+(\d+)\skB\n')
    f = open("/proc/meminfo")
    stats = dict(stat_regex.findall(f.read()))
    f.close()
    p = []
    for metric in monit_keys:
        value = stats[metric]
        p.append(value)
        print ('# HELP %s info' % metric)
        print ('# TYPE %s gauge' % metric)
        print ('%s %s' % (metric, value))

def net_stat(p = []):
    lnum = 0
    with open('/proc/net/dev', 'r') as f:
        for line in f:
            lnum += 1
            if lnum >= 4:
                net_stat = []
                net_stat.append('net_inTotal{dev="%s"} %s' % (line.split(':')[0].strip(), line.split()[1].strip()))
                net_stat.append('net_outTotal{dev="%s"} %s' % (line.split(':')[0].strip(), line.split()[9].strip()))
                p.append(net_stat)
    return p

def io_stat(p = []):
    with open('/tmp/iostat.cache') as f:
        stats = f.read().split('\n\n')[2]
    lnum = 0
    for line in stats.split('\n'):
        lnum += 1
        ioinfo = []
        # 从第2行开始循环
        if lnum >= 2:
            l_line = line.split()
            ioinfo.append('io_mergreads{dev="%s"} %s' % (l_line[0], l_line[1]))
            ioinfo.append('io_mergwrites{dev="%s"} %s' % (l_line[0], l_line[2]))
            ioinfo.append('io_readTimes_per_second{dev="%s"} %s' % (l_line[0], l_line[3]))
            ioinfo.append('io_writeTimes_per_second{dev="%s"} %s' % (l_line[0], l_line[4]))
            ioinfo.append('io_readKB_per_second{dev="%s"} %s' % (l_line[0], l_line[5]))
            ioinfo.append('io_writeKB_per_second{dev="%s"} %s' % (l_line[0], l_line[6]))
            ioinfo.append('io_avgrq_size{dev="%s"} %s' % (l_line[0], l_line[7]))
            ioinfo.append('io_avgqu_size{dev="%s"} %s' % (l_line[0], l_line[8]))
            ioinfo.append('io_await{dev="%s"} %s' % (l_line[0], l_line[9]))
            ioinfo.append('io_svctm{dev="%s"} %s' % (l_line[0], l_line[10]))
            if len(l_line) == 14:
                ioinfo.append('io_util{dev="%s"} %s' % (l_line[0], l_line[13]))
            elif len(l_line) == 12:
                ioinfo.append('io_util{dev="%s"} %s' % (l_line[0], l_line[11]))
            p.append(ioinfo)
    return p

def print_disk_use():
    str_disk_size = commands.getoutput("/bin/df |awk '{print $6,$2}' |grep '/' ")
    print '# HELP disk_size info'
    print '# TYPE disk_size gauge'
    for disk_size in str_disk_size.splitlines():
        print 'disk_size{mounted="%s"} %s' % (disk_size.split()[0], disk_size.split()[1])
    str_disk_free = commands.getoutput("/bin/df |awk '{print $6,$4}' |grep '/' ")
    print '# HELP disk_free info'
    print '# TYPE disk_free gauge'
    for disk_free in str_disk_free.splitlines():
        print 'disk_free{mounted="%s"} %s' % (disk_free.split()[0], disk_free.split()[1])

def print_multi_devs(p =[], type = 'gauge'):
    for m in range(len(p[0])):
        print ('# HELP %s info' % p[0][m].split('{')[0])
        print ('# TYPE %s %s' % (p[0][m].split('{')[0], type))
        for n in range(len(p)):
            print ('%s' % p[n][m])

def print_task_num():
    task_num = commands.getoutput('ps -ef |wc -l')
    print '''# HELP sys_task_num info
# TYPE sys_task_num gauge
sys_task_num %s''' % task_num


if __name__ == '__main__':
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(3)
    print_cpu_stat()
    print_load_stat()
    print_mem_stat()
    print_multi_devs(net_stat(), 'counter')
    print_multi_devs(io_stat(), 'gauge')
    print_disk_use()
    print_task_num()
    signal.alarm(0)
