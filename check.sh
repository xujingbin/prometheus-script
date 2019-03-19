#!/bin/bash
#-*- coding:utf-8 -*-

# 服务检查
#Exit code 0 - Check is passing
#Exit code 1 - Check is warning
#Any other code - Check is failing

function init(){
  cd /usr/local/proms-agent
  #lan ip
  IP=`ip addr show em2 | grep 'inet '| grep 'brd ' |awk '{print $2}' |awk -F '/' '{print $1}'`
  log_dir='/data1/logs/proms'
  ps -ef |grep 'proms-agent -l' |grep -v grep > /dev/null 2>&1
  if (( $? != 0 ));then
    nohup ./proms-agent -l $IP > $log_dir/proms-agent.log 2>$log_dir/proms-agent.err &
  else
    echo 'proms-agent process has exist'
  fi
  ps -ef |grep 'consul agent' |grep -v grep > /dev/null 2>&1
  if (( $? != 0 ));then
    nohup ./consul agent  -config-file=./script/conf/consul.json -enable-script-checks=true > $log_dir/consul.log 2>&1 &
  else
    echo './consul process has exist'
  fi
  find . -name "*.json" |xargs sed -i "s/10.0.0.218/$IP/g"
#  find . -name "*.json" |xargs sed -i "s/\"Address\": \"\"/\"Address\": \"$IP\"/g"
}

cd /usr/local/proms-agent
for service in `ls  script/conf/ |egrep 'nginx|mysql|haproxy|redis' |sed 's/.json//'`;do
  if [[ $service == 'redis' ]];then
    ps -ef |grep -v grep |grep 'redis-server' > /dev/null 2>&1
  elif [[ $service == 'nginx' ]];then
    ps -ef |grep -v grep |grep 'nginx: master' > /dev/null 2>&1
  elif [[ $service == 'mysql' ]];then
    ps -ef |grep -v grep |grep 'mysqld ' |grep 'socket'  > /dev/null 2>&1
  elif [[ $service == 'haproxy' ]];then
    ps -ef |grep -v grep |grep 'haproxy -f' > /dev/null 2>&1
  fi
  # 如果有实例运行,则进一步判断
  if [[ $? == 0 ]];then
    curl -s 127.0.0.1:8500/v1/agent/services |grep "\"$service\":" > /dev/null 2>&1
    # 如果没有注册服务，则注册
    if [[ $? != 0 ]];then
      curl -X PUT -d @/usr/local/proms-agent/script/conf/${service}.json 127.0.0.1:8500/v1/agent/service/register
      init
    fi
  fi
done
