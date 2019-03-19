#!/bin/env python
#-*- coding:utf-8 -*-

from config import monit_keys
from config import slave_keys
import re, os, json
import commands, signal,subprocess
import sys


def handler(signum, frame):
     exit()

def get_mysql_stats(port = 3306):
    cmd = "/usr/local/mysql/bin/mysql -uzabbixuser -pzabbixusermy4399 -h127.0.0.1 -N -P%s -e 'show global status'" % port
    stat_regex = re.compile(ur'(\w+):(\w+\.?[0-9]*)\n')
    mysql_status = commands.getoutput(cmd)
    stats = dict(stat_regex.findall(mysql_status.replace("\t",":")))
    return stats

def package_mysql_stats(stats = {}, port = 3306):
    p = []
    for key, vtype in monit_keys:
        value = -1
        if key in stats.keys():
            if key == 'Innodb_buffer_pool_pages_total':
                # 转换成字节
                value =  float(stats['Innodb_page_size']) * int(stats['Innodb_buffer_pool_pages_total'])
            elif key == 'Slave_running':
                if stats[key] == 'OFF':
                    value = 0
                else:
                    value = 1
            else:
                value = stats[key]
        elif stats:
            if key == 'Writes':
                value =  long(stats['Com_insert']) + long(stats['Com_update']) + long(stats['Com_delete'])
            elif key == 'Query_cache_hits':
                if stats['Qcache_hits'] != '0':
                    value = format_float(100* (float(stats['Qcache_hits']) / ( int(stats['Qcache_hits']) + int(stats['Qcache_inserts']) )))
                else:
                    value = 0
            elif key == 'Thread_cache_hits':
                value = format_float(100 * ( 1 - float(stats['Threads_created']) / int(stats['Connections'])))
            elif key == 'Innodb_buffer_read_hits':
                if stats['Innodb_buffer_pool_read_requests'] != '0':
                    value = format_float(100 * (1 - float(stats['Innodb_buffer_pool_reads']) / int(stats['Innodb_buffer_pool_read_requests'])))
            elif key == 'key_buffer_read_hits':
                if stats['Key_read_requests'] != '0':
                    value = format_float(100 * (1 - float(stats['Key_reads']) / int(stats['Key_read_requests'])))
                else:
                    value = 0
            elif key == 'Key_buffer_write_hits':
                if stats['Key_write_requests'] != '0':
                    value = format_float(100 * (1 - float(stats['Key_writes']) / int(stats['Key_write_requests'])))
                else:
                    value = 0
        p.append('%s{port="%s"} %s' % (key, port, value))
       
    return p

def get_slave_info(port = 3306):
    cmd = "/usr/local/mysql/bin/mysql -uzabbixuser -pzabbixusermy4399 -h127.0.0.1 -P%s -e 'show slave status\G'" % port
    stat_regex = re.compile(ur'(\w+): (\w+\.?[0-9]*)\n')
    slave_status = commands.getoutput(cmd)
    stats = dict(stat_regex.findall(slave_status.replace("\t",":")))
    p = []
    value = -1
    for key, vtype in slave_keys:
        if key in stats.keys():
            if key == 'Slave_IO_Running':
                if stats[key] == 'Yes':
                    value = 1
                else:
                    value = 0
            elif key == 'Slave_SQL_Running':
                if stats[key] == 'Yes':
                    value = 1
                else:
                    value = 0
            else:
                value = stats[key] 
           
            p.append('%s{port="%s"} %s' % (key, port, value))
    return p

# 保留两位小数
def format_float(num):
    return float('%.2f' % num)

def compare_instances(_file, l_alive_instances):
    if os.path.exists(_file):
        with open(_file, 'r') as f:
            old_instances = f.read()
        l_old_instances = json.loads(old_instances)
        print '''# HELP mysql_is_alive info
# TYPE mysql_is_alive gauge'''
        for port in l_old_instances:
            value = 1
            if port not in l_alive_instances:
                value = 0
            print 'mysql_is_alive{port="%s"} %s' % (port, value)
#        if l_old_instances != l_alive_instances:
#            for j in l_alive_instances:
#                if j not in l_old_instances:
#                    l_old_instances.append(j)
#            with open(_file, 'w') as f:
#                f.write(json.dumps(l_old_instances))
    else:
        with open(_file, 'w') as f:
            f.write(json.dumps(l_alive_instances))
        compare_instances(_file, l_alive_instances)

def main():
    cmd = "ps -ef |grep mysqld |grep 'port=' |awk -F '=' '{print $NF}'"
    # 用python执行ps grep会有重定向输出的问题，可用ipython来查看执行步骤
    port_regex = re.compile(ur'[0-9]{4}')
    mysql_instances = commands.getoutput(cmd)
    ll_mysql_instances = port_regex.findall(mysql_instances)
   # 判断实例存活并打印出来
    compare_instances('/tmp/mysql_instances', ll_mysql_instances)
#    # 若有实例则进行下一步
    if ll_mysql_instances:
        l_mysql_instances = []
        l_slave_instances = []
        # 遍历所有实例
        for i in ll_mysql_instances:
            port = i
            mysql_stats = get_mysql_stats(port)
            l_mysql_instances.append(package_mysql_stats(mysql_stats, port))
            if 'Slave_running' in mysql_stats.keys() and mysql_stats['Slave_running'] == 'ON':
                l_slave_instances.append(get_slave_info(port))
        # 循环所有实例所有指标
        for m in range(len(l_mysql_instances[0])):
            print '# HELP %s info' % l_mysql_instances[0][m].split('{')[0]
            print '# TYPE %s %s' % (l_mysql_instances[0][m].split('{')[0], monit_keys[m][1])
            for n in range(len(l_mysql_instances)):
                print 'mysql_%s' % l_mysql_instances[n][m]
        # 循环所有实例所有指标
        if l_slave_instances:
            for m in range(len(l_slave_instances[0])):
                print '# HELP %s info' % l_slave_instances[0][m].split('{')[0]
                print '# TYPE %s %s' % (l_slave_instances[0][m].split('{')[0], slave_keys[m][1])
                for n in range(len(l_slave_instances)):
                    print 'mysql_%s' % l_slave_instances[n][m]

if __name__ == '__main__':
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(8)
    main()
    signal.alarm(0)
