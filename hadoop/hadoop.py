#!/bin/env python
# -*- coding:utf-8 -*-

# hadoop yarn监控
import requests


monit_queue_keys = {
    'capacity': 'gauge',
    'usedCapacity': 'gauge',
    'numApplications': 'gauge',
    'users': 'gauge',
#    'queueName': 'gauge',
    'numContainers': 'gauge'
}
monit_user_keys = {
#    'username': 'gauge',
    'memory': 'gauge',
    'vCores': 'gauge',
    'numPendingApplications': 'gauge',
    'numActiveApplications': 'gauge'
}
response = requests.get('http://qz50:8088/ws/v1/cluster/metrics')
d_metrics = response.json()['clusterMetrics']
for key, value in d_metrics.items():
   print '''# HELP %s info
# TYPE %s gauge
yarn_%s %s''' % (key, key, key, value)
#response = requests.get('http://qz50:8088/ws/v1/cluster/nodes')
#d_nodes_states = response.json()['nodes']
#l_nodes_states = d_nodes_states.items()[0][1]
#l_active_nodes = []
#l_lost_nodes = []
#l_dead_nodes = []
#for node in l_nodes_states:
#    if node['state'] == 'RUNNING':
#        l_active_nodes.append(node['nodeHostName'])
#    elif node['state'] == 'LOST':
#        l_lost_nodes.append(node['nodeHostName'])
#print '''# HELP yarn_dead_nodes info
## TYPE yarn_dead_nodes gauge'''
#for node in l_lost_nodes:
#    if node not in l_active_nodes and node not in  'QZ50 QZ51 QZ237':
#        print ('yarn_dead_nodes{hostname="%s"} 1' % node)

response = requests.get('http://qz50:8088/ws/v1/cluster/scheduler').json()['scheduler']
l_queues = response['schedulerInfo']['queues']['queue']
root_usedCapacity = response['schedulerInfo']['usedCapacity']
print '''# HELP %s info
# TYPE %s gauge
yarn_%s %s''' % ('root_usedCapacity', 'root_usedCapacity', 'root_usedCapacity', root_usedCapacity)

for key, vtype in monit_queue_keys.items():
    if key <> 'users':
        print '''# HELP %s info
# TYPE %s gauge''' % (key, key)
        for queue in l_queues:
            if key in queue.keys():
                print 'yarn_%s{queueName="%s"} %s' % (key, queue["queueName"], queue[key])
    else:
        for u_key in monit_user_keys.keys():
            print '''# HELP user_%s info
# TYPE user_%s gauge''' % (u_key, u_key)
            for queue in l_queues:
                if key in queue.keys() and queue[key] is not None:
                    for d_user_memtrics in (queue[key]['user']):
                        if u_key == 'numPendingApplications':
                            print('yarn_numPendingApps{queuename="%s", username="%s"} %s' % (queue["queueName"], d_user_memtrics['username'], d_user_memtrics['numPendingApplications']))
                        elif u_key == 'numActiveApplications':
                            print('yarn_numActiveApps{queuename="%s",username="%s"} %s' % (queue["queueName"],d_user_memtrics['username'], d_user_memtrics['numActiveApplications']))
                        elif u_key == 'memory':
                            print('yarn_memory{queuename="%s",username="%s"} %s' % (queue["queueName"],d_user_memtrics['username'], d_user_memtrics['resourcesUsed']['memory']))
                        elif u_key == 'vCores':
                            print('yarn_vCores{queuename="%s",username="%s"} %s' % (queue["queueName"],d_user_memtrics['username'], d_user_memtrics['resourcesUsed']['vCores']))
