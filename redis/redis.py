#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os, re, sys, json, signal, commands
#import profile
#from pudb import set_trace; set_trace()

def handler(signum, frame):
     sys.exit()

monit_keys = {
    'connected_clients': 'gauge',
    'blocked_clients': 'counter',
    'used_memory': 'gauge',
    'used_memory_rss': 'gauge',
    'max_memory': 'gauge',
    'mem_fragmentation_ratio': 'gauge',
    'total_commands_processed': 'counter',
    'rejected_connections': 'counter',
    'expired_keys': 'counter',
    'total_net_input_bytes': 'gauge',
    'total_net_output_bytes': 'gauge',
    'evicted_keys': 'counter',
    'client_biggest_input_buf': 'counter',
    'client_longest_output_list': 'counter',
    'keyspace_hits': 'counter',
    'keyspace_misses': 'counter',
    'used_cpu_sys': 'counter',
    'used_cpu_user': 'counter',
}

class RedisStats:
    redis_cli = '/usr/local/bin/redis-cli'
    stat_regex = re.compile(ur'(\w+):([0-9]+\.?[0-9]*)\r')
    stat_regex2 = re.compile(ur'(cmdstat_\w+):(.*)\r')

#    @profile
    def __init__(self, _port='6379', _host='127.0.0.1' ,status='info all'):
        self._host=_host
        self._port=_port
        self.cmd = '%s -h %s -p %s %s' % (self.redis_cli, _host, _port, status)


#    @profile
    def get_info(self):
        result = commands.getoutput(self.cmd).strip()
        stats = dict(self.stat_regex.findall(result))
        # 记录cmdstat_指令
        stats2 = dict(self.stat_regex2.findall(result))
        p = {}
        for (key, vtype) in monit_keys.items():
            if key == 'max_memory':
                value = commands.getoutput('%s -h %s -p %s config get maxmemory |grep -v maxmemory' % (self.redis_cli, self._host, self._port)).strip()
                p[key] = '{port="%s"} %s' % (self._port, value)
            else:
                if key in stats.keys():
                    value = stats[key]
                    p[key] = '{port="%s"} %s' % (self._port, value)
        for (key2, value2) in stats2.items():
            # key2 = key2.split('cmdstat_')[1]
            calls = value2.split(',')[0].split('=')[1]
            usec = value2.split(',')[1].split('=')[1]
            usec_per_call = value2.split(',')[2].split('=')[1]
            p[key2+'_calls'] = '{port="%s"} %s' % (self._port, calls)
            p[key2+'_usec'] = '{port="%s"} %s' % (self._port, usec)
            p[key2+'_usec_per_call'] = '{port="%s"} %s' % (self._port, usec_per_call)
#        p = dict(p, **stats2)
#        print(stats2)
        return p

def get_all_instances_metrics(_redis_all_ports='', l_all_metrics=[]):
    # 循环每个实例,每个实例的数据都append到l_all_metrics列表中
    for i in _redis_all_ports.strip().split('\n'):
        if ':' in i:
            host = i.split(':')[0]
            port = i.split(':')[1]
        else:
            host = '127.0.0.1'
            confFile=i
            port = commands.getoutput("grep port %s |cut -d ' ' -f 2" % confFile).strip()
        if host == '*':
            host=commands.getoutput("ip addr show em2 | grep 'inet ' |awk '{print $2}' |awk -F '/' '{print $1}'").strip()
        _redis = RedisStats(port, host)
        l_all_metrics.append(_redis.get_info())
    return l_all_metrics


def print_metrics_info(l_all_metrics=[]):
    d_all_metrics = {}
    # 把list转成dict:{'metric':['{port="%s"} %s % (port, value)']}
    for m in l_all_metrics:
        for (k, v) in m.items():
            if d_all_metrics.get(k) is None:
                d_all_metrics[k] = []
            d_all_metrics[k].append(v)
    for (metric, value) in d_all_metrics.items():
        if metric in monit_keys.keys():
            print '# HELP redis_%s info' % metric
            print '# TYPE redis_%s %s' % (metric, monit_keys[metric])
#        elif "_calls" in metric:
#            print '# TYPE redis_calls info'
#            print '# TYPE redis_calls counter'
#        elif "_usec" in metric:
#            print '# TYPE redis_usec info'
#            print '# TYPE redis_usec counter'
        elif "_usec_per_call" in metric:
            print '# TYPE redis_%s info' % (metric)
            print '# TYPE redis_%s gauge' % (metric)
        else:
            print '# TYPE redis_%s info' % (metric)
            print '# TYPE redis_%s counter' % (metric)
        for v in d_all_metrics[metric]:
            if "_calls" in metric:
                v = v.split('}')[0] + ', cmd="' + metric.split('_calls')[0].split('cmdstat_')[1] + '"}' + v.split('}')[1]
                print('redis_calls%s' % v)
            elif "_usec_per_call" in metric:
                v = v.split('}')[0] + ', cmd="' + metric.split('_usec_per_call')[0].split('cmdstat_')[1] + '"}' + v.split('}')[1]
                print('redis_usec_per_call%s' % v)
            elif "_usec" in metric:
                v = v.split('}')[0] + ', cmd="' + metric.split('_usec')[0].split('cmdstat_')[1] + '"}' + v.split('}')[1]
                print('redis_usec%s' % v)
            else: 
                print('redis_%s%s' % (metric, v))

def compare_instances(_file, l_alive_instances):
    if os.path.exists(_file):
        with open(_file, 'r') as f:
            old_instances = f.read()
        if not old_instances:
            with open(_file, 'w') as f:
                f.write(json.dumps(l_alive_instances))
            compare_instances(_file, l_alive_instances)
        else:
            l_old_instances = json.loads(old_instances)
            print '''# HELP redis_is_alive info
# TYPE redis_is_alive gauge'''
            for i in l_old_instances:
                value = 1
                if ':' in i:
                    port = i.split(':')[1]
                    host = i.split(':')[0]
                    if host in '0.0.0.0' '127.0.0.1' '*':
                        host = '127.0.0.1'
                else:
                    host = '127.0.0.1'
                    if i != '':
                        confFile=i
                        port = commands.getoutput("grep port %s |cut -d ' ' -f 2" % confFile).strip()
                    else:
                        port=6379
               
                ping_result = commands.getoutput("redis-cli -h %s -p %s ping" % (host, port))
                if ping_result != 'PONG':
                    value = 0
                if i not in l_alive_instances:
                    value = 0
                print 'redis_is_alive{port="%s"} %s' % (port, value)
            if set(l_old_instances) != set(l_alive_instances):
                for j in l_alive_instances:
                    if j not in l_old_instances:
                        l_old_instances.append(j)
                with open(_file, 'w') as f:
                    f.write(json.dumps(l_old_instances))
    else:
        with open(_file, 'w') as f:
            f.write(json.dumps(l_alive_instances))
        compare_instances(_file, l_alive_instances)

def str_to_list(str):
    l = []
    for i in str.split('\n'):
        l.append(i)
    return l

if __name__ == "__main__":
    cmd = "ps -ef |egrep './redis-server|redis-server ' |grep -v grep |awk '{print $9}' |sort |uniq"
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(7)
    #ps -ef |grep 'redis-server' |grep -v grep |awk '{print $2,$9}'  该命令出现三种结果
    #29454 0.0.0.0:6392
    #30834
    #10823 /etc/redisConf/redis7.conf
    redis_all_ports =  commands.getoutput(cmd)
    l_redis_all_instances = str_to_list(redis_all_ports)
    compare_instances('/tmp/redis_instances', l_redis_all_instances)
    # 判断是否有运行redis实例
    if redis_all_ports:
        l_all_metrics=get_all_instances_metrics(redis_all_ports)
        print_metrics_info(l_all_metrics)
    else:
        print 'does not have a redis'
    signal.alarm(0)
