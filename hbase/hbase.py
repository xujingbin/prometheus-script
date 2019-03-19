#!/usr/bin/python
#-*- coding:utf-8 -*-

import requests
import sys, signal
import types
from decimal import Decimal
from decimal import getcontext
def handler(signum, frame):
    sys.exit()
# from requests.auth import HTTPBasicAuth


def collect_ipc(host, port):
    try:
        r = requests.get('http://%s:%s/jmx?qry=%s' % (host, port, 'Hadoop:service=HBase,name=RegionServer,sub=IPC'))
        result = {}
        output = r.json()
        result['receivedBytes'] = output['beans'][0]['receivedBytes']
        result['sentBytes'] = output['beans'][0]['sentBytes']
        result['numOpenConnections'] = output['beans'][0]['numOpenConnections']
        for key in result:
            print ('# HELP hbase_%s info' % key)
            print ('# TYPE hbase_%s gauge' % key)
            print ('hbase_%s %s' % (key, result[key]))
    except requests.RequestException as e:
        print ('collect_ipc exception')
        return 0

def collect_region(host, port):
    try:
        result = {}
        r = requests.get('http://%s:%s/jmx?qry=%s' % (host, port, 'java.lang:type=Memory'))
        output = r.json()
        result['HeapMemoryUsage_max'] = output['beans'][0]['HeapMemoryUsage']['max']
        result['HeapMemoryUsage_used'] = output['beans'][0]['HeapMemoryUsage']['used']
        r = requests.get('http://%s:%s/jmx?qry=%s' % (host, port, 'Hadoop:service=HBase,name=RegionServer,sub=Server'))
        output = r.json()
        result['blockCacheCount'] = output['beans'][0]['blockCacheCount']
        result['blockCacheEvictionCount'] = output['beans'][0]['blockCacheEvictionCount']
        result['blockCacheFreeSize'] = output['beans'][0]['blockCacheFreeSize']
        result['blockCacheHitCount'] = output['beans'][0]['blockCacheHitCount']
        result['blockCacheMissCount'] = output['beans'][0]['blockCacheMissCount']
        result['blockCacheSize'] = output['beans'][0]['blockCacheSize']
        result['compactionQueueLength'] = output['beans'][0]['compactionQueueLength']
        result['flushQueueLength'] = output['beans'][0]['flushQueueLength']
        result['memStoreSize'] = output['beans'][0]['memStoreSize']
        result['storeFileIndexSize'] = output['beans'][0]['storeFileIndexSize']
        result['totalRequestCount'] = output['beans'][0]['totalRequestCount']
        result['readRequestCount'] = output['beans'][0]['readRequestCount']
        result['writeRequestCount'] = output['beans'][0]['writeRequestCount']
        for key in result:
            print ('# HELP hbase_%s info' % key)
            print ('# TYPE hbase_%s gauge' % key)
            print ('hbase_%s %s' % (key, result[key]))
    except requests.RequestException as e:
        result = 0

def regulate_size(size):
   #if type(size) is types.IntType:
   #     return round(Decimal(str(size)) / 1024 / 1024, 2) # MB
    return size

def get_processCallTime(host, port):
    monit_keys = ('ProcessCallTime_num_ops', 'ProcessCallTime_min', 'ProcessCallTime_max', 'ProcessCallTime_mean', 'ProcessCallTime_25th_percentile', 'ProcessCallTime_median',
        'ProcessCallTime_75th_percentile', 'ProcessCallTime_90th_percentile', 'ProcessCallTime_95th_percentile',
        'ProcessCallTime_98th_percentile', 'ProcessCallTime_99th_percentile', 
        'queueSize', 'QueueCallTime_num_ops', 'QueueCallTime_min', 'QueueCallTime_max', 'QueueCallTime_mean',
        'QueueCallTime_25th_percentile', 'QueueCallTime_median', 'QueueCallTime_75th_percentile',
        'QueueCallTime_90th_percentile', 'QueueCallTime_95th_percentile', 'QueueCallTime_98th_percentile',
        'QueueCallTime_99th_percentile', 
    )
    result = {}
    r = requests.get('http://%s:%s/jmx?qry=%s' % (host, port, 'Hadoop:service=HBase,name=RegionServer,sub=IPC'))
    output = r.json().get('beans')[0]
    for key in monit_keys:
        result[key] = output.get(key)
    for key in result:
        print ('''# HELP hbase_%s info
# TYPE hbase_%s  gauge
hbase_%s %s''' % (key, key, key, result[key]))
    print ('''# HELP hbase_QueueCallTime_999th_percentile info
# TYPE hbase_QueueCallTime_999th_percentile  gauge
hbase_QueueCallTime_999th_percentile %s''' % output.get('QueueCallTime_99.9th_percentile'))
    print ('''# HELP hbase_ProcessCallTime_999th_percentile info
# TYPE hbase_ProcessCallTime_999th_percentile gauge
hbase_ProcessCallTime_999th_percentile %s''' % output.get('ProcessCallTime_99.9th_percentile'))
    
def get_scanTime(host, port):
    monit_keys = ('ScanTime_num_ops', 'ScanTime_min', 'ScanTime_max', 'ScanTime_mean', 'ScanTime_25th_percentile', 'ScanTime_median',
        'ScanTime_75th_percentile', 'ScanTime_90th_percentile', 'ScanTime_95th_percentile',
        'ScanTime_98th_percentile', 'ScanTime_99th_percentile',
    )
    result = {}
    r = requests.get('http://%s:%s/jmx?qry=%s' % (host, port, 'Hadoop:service=HBase,name=RegionServer,sub=Server'))
    output = r.json().get('beans')[0]
    for key in monit_keys:
        result[key] = output.get(key)
    for key in result:
        print ('''# HELP hbase_%s info
# TYPE hbase_%s gauge
hbase_%s %s''' % (key, key, key, result[key]))
    print ('''# HELP hbase_ScanTime_999th_percentile info
# TYPE hbase_ScanTime_999th_percentile gauge
hbase_ScanTime_999th_percentile %s''' % output.get('ScanTime_99.9th_percentile'))

if __name__ == '__main__':
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(3)
    collect_ipc('localhost', 16030) 
    collect_region('localhost', 16030) 
    get_processCallTime('localhost', 16030)
    get_scanTime('localhost', 16030)
    signal.alarm(0)
