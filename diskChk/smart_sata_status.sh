#!/bin/sh
#caiyiyong
#2015-5-13
#zabbix 物理SATA磁盘坏道检测脚本
PATH=$PATH:/usr/sbin
megacli_bin='/opt/MegaRAID/MegaCli/MegaCli64'
allinfo=$1   
item=$2     
id=`echo $allinfo | awk -F':' '{print $1}'`



if [ "$1" == "-h" -o "$1" == "-help" ];then

echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
例：
#SAS|SCSI  Usa :./check_smart.sh 1::STAT: [Result_ok]
#                                [List ]
#                                [Reported_Uncorrect ]
#                                [Media_Wearout_Indicator ]
#                                [End_to_End_Error ]
#                                [Power_Up_hours ] 
#

#-h | -help:显示帮助
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
exit
fi




detection()
{

          Result_ok=`echo "$result" | egrep  "Status:|result:"| awk -F ": " '{print $2}'` #健康状态     
	  Reported_Uncorrect=`echo "$result" | egrep -i "Reported_Uncorrect"| awk  '{print $10}'`     #报告的不可纠正错误
	  List=`echo "$result" | egrep -i "Reallocated_Sector_Ct"| awk  '{print $10}'` #重定位扇区次数,出厂后产生的坏块个数
	  Media_Wearout_Indicator=`echo "$result" | egrep -i "Wearout"| awk  '{print $10}'`   #介质耗损指标
	  End_to_End_Error=`echo "$result" | egrep -i "End-to-End"| awk  '{print $10}'`   #终端校验出错  
	  Power_On_Hours=`echo "$result" | egrep -i "Power_On_Hours"| awk  '{print $10}' | awk -F"." '{print $1}'` #运行时间
	     
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
	      result=`smartctl -a -d sat+megaraid,$id /dev/sda`
	      echo "$result" > /tmp/zabbix_smart_$id
	      
      else
	      result=`cat /tmp/zabbix_smart_$id`
      fi
      detection

fi


eval echo \$$item
