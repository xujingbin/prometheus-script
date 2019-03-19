#!/bin/sh
#caiyiyong
#2015-5-13
#zabbix 物理SAS磁盘坏道检测脚本

PATH=$PATH:/usr/sbin
megacli_bin='/opt/MegaRAID/MegaCli/MegaCli64'
allinfo=$1   
item=$2     
id=`echo $allinfo | awk -F':' '{print $1}'`




if [ "$1" == "-h" -o "$1" == "-help" ];then

echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
例：
#SAS|SCSI  Usa :./check_smart.sh 1::SAS: [Result_ok]
#                                	[List ]
#                                	[Read_uncorr ]
#                                	[Write_uncorr ]
#                                	[Verify_uncorr ]
#                                	[Power_Up_hours ] 
#

#-h | -help:显示帮助
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
exit
fi




detection()
{

      Result_ok=`echo "$result" | egrep  "Status:|result:"| awk -F ": " '{print $2}'` #健康状态     
      List=`echo "$result" | grep -i "grown defect list" | awk -F "=|: " '{print $2}'| awk -F " " '{print $1}'` #坏道
      Read_uncorr=`echo "$result" | grep -i "read:" | awk '{print $8}'`  #read不可纠正错误
      Write_uncorr=`echo "$result" | grep -i "write:" | awk '{print $8}'`  #write不可纠正错误
      Verify_uncorr=`echo "$result" | grep -i "verify:" | awk '{print $8}'` #核实的不可纠正错误
      Power_Up_hours=`echo "$result" | grep -i "number of hours powered up" | awk -F"= " '{print $2}'| awk -F"." '{print $1}' ` #运行时间
	     
}


#---------------判断阵列卡类型-----------------------


if [ "`echo $id | grep /dev/s`" != "" ];then
	disk_type='nomegaraid'
else
	disk_type='megaraid'
fi



#------主流程开始-------根据磁盘类型运行主检测模块----------------


#nomegaraid

if [ "$disk_type" == 'nomegaraid' ];then
      if [ "$item" == "List" ];then
	      result=`smartctl -a $id`
              echo "$result" > /tmp/zabbix_smart_`echo $id | awk -F '/' '{print $3}'`
 
      else
              refile=`echo $id | awk -F '/' '{print $3}'`
              result=`cat /tmp/zabbix_smart_$refile`

      fi
      detection

fi

#megaraid
if [ "$disk_type" == 'megaraid' ];then
      if [ "$item" == "List" ];then
	      result=`smartctl -a -d megaraid,$id /dev/sda`
	      echo "$result" > /tmp/zabbix_smart_$id
	      
      else
	      result=`cat /tmp/zabbix_smart_$id`
      fi
      detection

fi


eval echo \$$item
