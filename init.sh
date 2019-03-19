#!/bin/bash

user=`whoami`
cd /usr/local/proms-agent
#lan ip
IP=`ip addr show em2 | grep 'inet ' | grep 'brd ' |grep '10.'|awk '{print $2}' |awk -F '/' '{print $1}'`
log_dir='/data/logs/proms'
if [[ ! -d $log_dir ]];then
  sudo mkdir -p $log_dir
fi
if [[ ! -d '/tmp/consul/' ]];then
  sudo mkdir -p /tmp/consul/
fi
sudo chown -R $user $log_dir
sudo chown -R $user /tmp/consul/ > /dev/null 2>&1
ps -ef |grep -v grep |grep proms-agent
#if (( $? != 0 ));then
  nohup ./proms-agent -l $IP > /dev/null 2>&1 &
#else
#  echo 'proms-agent process has exist'
#fi
ps -ef |grep 'consul agent' |grep -v grep
if (( $? != 0 ));then
  # nohup  ./consul agent -data-dir=/tmp/consul -bind=$IP -enable-script-checks=true -datacenter=sen_hua_kan_dan_qiao -retry-join="10.0.0.194" > $log_dir/consul.log 2>&1 &
  sed -i "s/0.0.0.0/$IP/g" ./script/conf/consul.json
  nohup ./consul agent  -config-file=./script/conf/consul.json -enable-script-checks=true > /dev/null 2>&1 &
else
  echo './consul process has exist'
fi
find . -name "*.json" |xargs sed -i "s/10.0.0.218/$IP/g" 
sleep 1
curl -X PUT -d @/usr/local/proms-agent/script/conf/check.json localhost:8500/v1/agent/service/register
curl -X PUT -d @/usr/local/proms-agent/script/conf/sys.json localhost:8500/v1/agent/service/register
#curl -X PUT -d @/usr/local/proms-agent/script/conf/diskChk.json localhost:8500/v1/agent/service/register
