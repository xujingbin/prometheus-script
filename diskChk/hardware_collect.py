#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import platform
import re


#Detect Basic information
systemVersion = platform.platform()


def checkPythonVersionGt():
    #python version great then 2.4?
    pythonVersion = sys.version_info
    if pythonVersion[0] == 2 and pythonVersion[1] > 5:
        return True
    else:
        return False


if checkPythonVersionGt():
    import subprocess
    import json
else:
    try:
        import simplejson
    except ImportError:
        os.system('/usr/bin/yum -y install python-simplejson ')


def getCmdResult(cmd):
    #get one line result
    if checkPythonVersionGt():
        ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    else:
        ret = os.popen(cmd).read().strip()
    return ret


def resoutput(hardwareList):
    #output result
    if checkPythonVersionGt():
        print (json.dumps(hardwareList,indent=7))
    else:
        try:
            import simplejson

            print (simplejson.dumps(hardwareList,indent=7))
        except ImportError:
            print (str(hardwareList))


def getOutput(cmd):
    output = os.popen(cmd)
    lines = []
    for line in output:
        line = line.strip()
        if not re.match(r'^$', line):
            lines.append(line)
    return lines


def returnControllerNumber(output):
    for line in output:
        line = line.strip()
        if re.match(r'^Controller Count.*$', line):
            return int(line.split(':')[1].strip().strip('.'))


def returnControllerModel(output):
    for line in output:
        if re.match(r'^Product Name.*$', line.strip()):
            return line.split(':')[1].strip()


def returnControllerFirmware(output):
    for line in output:
        if re.match(r'^FW Package Build.*$', line.strip()):
            return line.split(':')[1].strip()


def returnArrayNumber(output):
    i = 0
    for line in output:
        if re.match(r'^Number of Virtual (Disk|Drive).*$', line.strip()):
            i = line.split(':')[1].strip()
    return i


def returnNextArrayNumber(output, curNumber):
    #Virtual Drive: 2 (Target Id: 2)
    for line in output:
        vdisk = re.match(r'^Virtual .*: \d+ \(Target Id: (\d+)\)$', line.strip())
        if vdisk and int(vdisk.group(1)) > curNumber:
            return int(vdisk.group(1))
    return -1


def returnArrayInfo(output, controllerid, arrayid):
    _id = 'c%du%d' % (controllerid, arrayid)
    operationlinennumber = False
    linenumber = 0
    ldpdcount = 0
    spandepth = 0

    for line in output:
        line = line.strip()
        if re.match(r'^Current Cache Policy\s*:.*$', line):
            CachePolicy = line.split(':')[1].strip()
            
        if re.match(r'Number Of Drives\s*((per span))?:.*[0-9]+$', line):
            ldpdcount = line.split(':')[1].strip()
        if re.match(r'Span Depth *:.*[0-9]+$', line):
            spandepth = line.split(':')[1].strip()
        if re.match(r'^RAID Level\s*:.*$', line):
            raidlevel = line.split(':')[1].split(',')[0].split('-')[1].strip()
            raid_type = 'RAID' + raidlevel
        if re.match(r'^Size\s*:.*$', line):
            # Size reported in MB
            if re.match(r'^.*MB$', line.split(':')[1]):
                size = line.split(':')[1].strip('MB').strip()
                size = str(int(round((float(size) / 1000)))) + 'G'
            # Size reported in TB
            elif re.match(r'^.*TB$', line.split(':')[1]):
                size = line.split(':')[1].strip('TB').strip()
                size = str(int(round((float(size) * 1000)))) + 'G'
            # Size reported in GB (default)
            else:
                size = line.split(':')[1].strip('GB').strip()
                size = str(int(round((float(size))))) + 'G'
        if re.match(r'^State\s*:.*$', line):
            state = line.split(':')[1].strip()


        if re.match(r'^Ongoing Progresses\s*:.*$', line):
            operationlinennumber = linenumber
        linenumber += 1
        if operationlinennumber:
            inprogress = output[operationlinennumber + 1]
        else:
            inprogress = 'None'

    if ldpdcount and (int(spandepth) > 1):
        ldpdcount = int(ldpdcount) * int(spandepth)
        if int(raidlevel) < 10:
            raid_type = raid_type + "0"

    return [_id, raid_type, size, state, inprogress,CachePolicy]


def returndiskInfo(output, controllerid):
    arrayid = False
    diskid = False
    table = []
    state = 'undef'
    model = 'undef'
    for line in output:
        line = line.strip()
        if re.match(r'^Virtual (Disk|Drive): [0-9]+.*$', line):
            arrayid = line.split('(')[0].split(':')[1].strip()
        if re.match(r'Firmware state: .*$', line):
            state = line.split(':')[1].strip()
        if re.match(r'Inquiry Data: .*$', line):
            model = line.split(':')[1].strip()
            model = re.sub(' +', ' ', model)
        if re.match(r'PD: [0-9]+ Information.*$', line):
            diskid = line.split()[1].strip()
        if re.match(r'Raw Size:+.*$', line):
            disksize = line.split()[2].strip() + line.split()[3].strip()

        if re.match(r'^Device Id\s*:.*$', line):
            deviceId = line.split(':')[1].strip()
        if re.match(r'^PD Type\s*:.*$', line):
            pdType = line.split(':')[1].strip()
        if arrayid and state != 'undef' and model != 'undef' and diskid:
            table.append([str(arrayid), str(diskid), state, model, disksize,deviceId,pdType])
            state = 'undef'
            model = 'undef'

    return table


def returnSmartInfo(output):
    table = []
    try:
        disk_sn = re.findall(r'Serial number:(.*)', output, re.I)[0].strip()
    except Exception, e:
        disk_sn = "Unknow"
    try:
        disk_size = re.findall(r'User Capacity:.*\[(.*)\]', output, re.I)[0].strip()
    except Exception, e:
        disk_size = "Unknow"
    try:
        disk_pro = re.findall(r'(Product:|Model Family:)(.*)', output, re.I)[0][1].strip()
    except Exception, e:
        disk_pro = "Unknow"
    try:
        disk_Ven = re.findall(r'(Vendor:|Device Model:)(.*)', output, re.I)[0][1].strip()
    except Exception, e:
        disk_Ven = "Unknow"

    try:
        disk_type = re.findall(r'(Transport protocol:|ATA Standard is:)(.*)', output)[0][1].strip()
    except Exception, e:
        disk_Ven = "Unknow"

    table = [disk_size, disk_sn, disk_pro, disk_Ven,disk_type]
    return table


def returnFdiskInfo():
    cmd = r"/sbin/parted -l | grep -i '/dev/' | sed -r 's/^.*\/dev\/([a-z0-9\/_\-]+).*/\1/i' 2>/dev/null"
    output = os.popen(cmd).readlines()

    return output


def installMptstatus():
    systemOsCmd = "cat /etc/issue | sed -n 1p"
    systemBitCmd = "/bin/uname -m"
    if re.search(r' 5\.', getCmdResult(systemOsCmd)):
        os.system("/usr/bin/wget -O /root/soft/daemonize-1.5.6-1.el5.x86_64.rpm  http://115.182.52.17/software/daemonize-1.5.6-1.el5.x86_64.rpm ; \
                   /usr/bin/wget -O /root/soft/mpt-status-1.2.0-3.el5.centos.x86_64.rpm http://115.182.52.17/software/mpt-status-1.2.0-3.el5.centos.x86_64.rpm ;\
                   rpm -ivh /root/soft/daemonize-1.5.6-1.el5.x86_64.rpm;rpm -ivh /root/soft/mpt-status-1.2.0-3.el5.centos.x86_64.rpm")

    if re.search(r' 6\.', getCmdResult(systemOsCmd)):
        os.system("/usr/bin/wget -O /root/soft/daemonize-1.7.3-1.el6.x86_64.rpm http://115.182.52.17/software/daemonize-1.7.3-1.el6.x86_64.rpm ;\
                   /usr/bin/wget -O /root/soft/mpt-status-1.2.0-3.el6.x86_64.rpm http://115.182.52.17/software/mpt-status-1.2.0-3.el6.x86_64.rpm ;\
                   rpm -ivh /root/soft/daemonize-1.7.3-1.el6.x86_64.rpm ;rpm -ivh /root/soft/mpt-status-1.2.0-3.el6.x86_64.rpm")
    if os.path.exists('/dev/mptctl') == False:
        os.system("mknod /dev/mptctl c 10 220;/sbin/modprobe mptctl")


def returnmptArray(output):
    mptArray = []
    cmd = "echo '%s' | awk -F' |,' '{print $1}'" % (output)
    group = getCmdResult(cmd)
    cmd = "echo '%s' | awk -F' |,' '{print $5}'" % (output)
    vType_raw = getCmdResult(cmd)
    if vType_raw == 'IM':
        vType = 'raid 1'
    if vType_raw == 'IS':
        vType = 'raid 0'
    cmd = "echo '%s'| awk -F' |,' '{print $10$11}'" % (output)
    raidsize = getCmdResult(cmd)
    cmd = "echo '%s' | awk -F' |,' '{print $7}'" % (output)
    diskNumber = getCmdResult(cmd)
    mptArray = [group, vType, raidsize, diskNumber]
    return mptArray


def checkBaseEnv(LsmodInfo):
    ret = {}
    ret['error'] = ''
    if not os.path.exists('/usr/sbin/dmidecode'):
        ret['error'] = ret['error'] + "dmindecode command is not exists"
        os.system("yum -y install dmidecode ")
    if not os.path.exists('/sbin/lspci'):
        ret['error'] = ret['error'] + "lspci command is not exists"
        os.system("yum -y install pciutils ")
    if not os.path.exists('/sbin/parted'):
        ret['error'] = ret['error'] + "parted is not exists"
        os.system("yum -y install parted ")
    if not os.path.exists("/usr/sbin/smartctl"):
        ret['error'] = ret['error'] + "smart is not exists"
        os.system('yum install -y smartmontools')

    if re.search("megaraid|megasr", LsmodInfo):
        if not os.path.exists('/opt/MegaRAID/MegaCli/MegaCli64'):
            ret['error'] = ret['error'] + "MegaCli64 is not exists"
            os.system("/usr/bin/wget -O /root/soft/megacli.tar.gz http://115.182.52.17/software/megacli.tar.gz;\
                        tar zxvf /root/soft/megacli.tar.gz -C /root/soft/;rpm -ivh /root/soft/linux/Lib_Utils-1.00-09.noarch.rpm ;\
                        rpm -ivh  /root/soft/linux/MegaCli-8.00.48-1.i386.rpm")
    if re.search("mptsas", LsmodInfo):
        if not os.path.exists('/usr/sbin/mpt-status'):
            ret['error'] = ret['error'] + "mpt-status is not exists"
            installMptstatus()

    if ret['error'] == '':
        return {}
    return ret


if __name__ == '__main__':
    #check raidControl


    LsmodInfo = os.popen('/sbin/lsmod').read().strip()
    r = checkBaseEnv(LsmodInfo)
    if r != {}:
        r = checkBaseEnv(LsmodInfo)
        if r != {}:
            resoutput(r)
            sys.exit(1)

    SASInfo = os.popen('/sbin/lspci | grep SAS').read().strip()
    raidControl = "UNknow"
    if re.search("2208", SASInfo):
        raidControl = {"0": "PERC H710"}

    if re.search("1078", SASInfo):
        raidControl = {"0": "PERC 6/i"}

    if re.search("2008", SASInfo):
        raidControl = {"0": "PERC H310"}

    if re.search("SAS1068E", SASInfo):
        raidControl = {"0": "PERC SAS 6/iR"}

    if re.search("SAS1064", SASInfo):
        raidControl = {"0": "LSI SAS1064"}


    #checkDisk num and size
    binarypath = "/opt/MegaRAID/MegaCli/MegaCli64"
    mptpath = "/usr/sbin/mpt-status"
    smartpath = "/usr/sbin/smartctl"
    ScsiInfo = os.popen('cat /proc/scsi/scsi').read().strip()

    diskInfo = {}
    diskDetail = []


    #阵列卡是megaraid 类型的，例如H710  perc 6/i  五洲MegaSR  H310  做阵列的情况
    if re.search("megaraid|megasr", LsmodInfo):
        cmd = binarypath + ' -adpCount -NoLog'
        output = getOutput(cmd)
        controllernumber = returnControllerNumber(output)

        controllerid = 0
        raidControl = {}
        while controllerid < controllernumber:
            cmd = '%s -AdpAllInfo -a%d -NoLog' % (binarypath, controllerid)
            output = getOutput(cmd)
            controllermodel = returnControllerModel(output)
            firmwareversion = returnControllerFirmware(output)
            raidControl.update({controllerid: controllermodel})
            controllerid += 1

        controllerid = 0
        while controllerid < controllernumber:
            cmd = '%s -LdInfo -Lall -a%d -NoLog' % (binarypath, controllerid)
            arrayoutput = getOutput(cmd)
            arrayid = returnNextArrayNumber(arrayoutput, -1)
            cmd = '%s -LdGetNum -a%d -NoLog' % (binarypath, controllerid)
            output = getOutput(cmd)
            arraynumber = int(returnArrayNumber(output))

            while arraynumber > 0:
                cmd = '%s -LDInfo -l%d -a%d -NoLog' % (binarypath, arrayid, controllerid)
                output = getOutput(cmd)
                arrayinfo = returnArrayInfo(output, controllerid, arrayid)


                cmd = '%s -LdPdInfo  -a%d -NoLog' % (binarypath, controllerid)
                output = getOutput(cmd)
                arraydisk = returndiskInfo(output, controllerid)
                
                diskDetail = []
                for array in arraydisk:
                    if ('c%du%s' % (controllerid, array[0]) == arrayinfo[0]):
                        diskDetail.append(array[5]+ ":"+array[4] + ":" +array[6] +":"+ array[3]+ ":" + array[2])
                diskNumber = len(diskDetail)
                diskInfo.update({arrayinfo[0]: {'vType': arrayinfo[1], 'size': arrayinfo[2], 'diskNumber': diskNumber,'state':arrayinfo[3],'inprogress':arrayinfo[4],'CachePolicy':arrayinfo[5],
                                                'diskDetail': diskDetail}})
                arrayid = returnNextArrayNumber(arrayoutput, arrayid)
                arraynumber -= 1
            controllerid += 1


    #阵列卡是mptsas类型      SAS 6/iR  H200     五洲SAS1064  做阵列的情况(只支持做了一组阵列的情况)
    if re.search("mptsas", LsmodInfo):
        cmd = "%s -p" % (mptpath)
        output = os.popen(cmd).readlines()
	scsiid = re.compile(r'Found SCSI id=([0-9]),.*')
	for line in output:
		st = line.strip()
		m = scsiid.match(st)
	if m:
		scsiinfo = m.groups()
		scsi = scsiinfo[0]
	else :
		scsi=0
	cmd = "%s -i %s" % (mptpath,scsi)
        output = os.popen(cmd).readlines()
        mptobj = re.compile(r'(.*) vol_id ([0-9]) type (IM|IS), ([0-9]) phy, ([0-9]+) GB, state (.*),.*')
        phyidobj = re.compile(r'.* phy ([0-9]) scsi_id.*')

        diskNumber = 0
        phyarray = []
        for line in output:
            st = line.strip()
            m = mptobj.match(st)
            if m:
                mptinfo = m.groups()
		state = mptinfo[5]
		group = mptinfo[0]
                if mptinfo[2] == 'IM':
                    vType = 'raid 1'
                else:
                    vType = 'raid 0'
                raidsize = int(mptinfo[4])
                diskNumber = int(mptinfo[3])
            if diskNumber >= 1:
                m = phyidobj.match(st)
                if m:
                    phyinfo = m.groups()
                    phyarray.append(int(phyinfo[0]))
        if diskNumber >= 1:
            phyarray.sort()
            diskDetail = []
            if not os.path.exists(smartpath):
                print ("smartcli is not exists")
                sys.exit(1)

            pi = 0
            ki = -1
            ni = 0
            import glob
            #for phyId in phyarray:
            for ta in glob.glob('/dev/sg?'):
                deviceName = '/dev/sg'+str(pi)
                cmd = "%s -i %s " % (smartpath, deviceName)
                output = os.popen(cmd).read().strip()
                if (re.findall(r'Device type:.*disk', output) or re.findall(r'ATA Standard is: .*ATA.*', output)) and not re.findall(r'Product:.*Logical Volume|VIRTUAL',output, re.I):
                    #ki = ki + 1
                    #if phyarray[ni] == ki:
                        #ni = ni + 1
		        SmartArray = returnSmartInfo(output)
		        diskDetail.append(deviceName + ":" + SmartArray[0] +  ":" + SmartArray[4] +":" + SmartArray[3] + " " + SmartArray[2] + " " + SmartArray[1])
                        #if ni == len(phyarray) :
                        #    break
                pi = pi + 1
            diskInfo.update(
                {group: {'vType': vType,'state':state, 'size': str(raidsize)+' GB', 'diskNumber': diskNumber, 'diskDetail': diskDetail}})

    #其他不做阵列的硬盘情况（H710  perc 6i一定要做阵列，所以下面不会找到其他没做阵列的硬盘）   
    #smart 信息中有Transport protocol 说明没有阵列

    FdiskInfo = returnFdiskInfo()
    for diskraw in FdiskInfo:
        diskDetail = []
        disk = diskraw.strip()
        cmd = "%s -i /dev/%s " % (smartpath, disk)
        output = os.popen(cmd).read().strip()
        if re.search(r'Transport protocol|ATA Standard is', output):
            SmartArray = returnSmartInfo(output)
            group = "/dev/" + disk
            #try:
            #    vType = re.findall(r'(Transport protocol:|ATA Standard is:)(.*)', output)[0][1].strip()
            #except Exception, e:
            #    vType = SmartArray[2]
	    vType = SmartArray[4]
            size = SmartArray[0]
            diskNumber = 1
            diskDetail.append(group+":"+SmartArray[0] + ":" +vType+":"+ SmartArray[3] + " " + SmartArray[2] + " " + SmartArray[1])
            diskInfo.update({group: {'vType': vType, 'size': size, 'diskNumber': diskNumber, 'diskDetail': diskDetail}})

    if diskInfo == {}:
        for diskraw in FdiskInfo:
            disk = diskraw.strip()
            group = "/dev/" + disk
            cmd = "fdisk -s " + group
            output = getCmdResult(cmd)
            if output == "":
                continue
            disksize = int(output) / 1024 / 1024
            disksize = str(disksize) + 'GB'
            diskInfo.update({
            group: {'vType': 'UNknow', 'size': disksize, 'diskNumber': 'UNknow', 'diskDetail': 'UNkonw', 'last': '1'}})


    #define command
    deviceIpCmd = "/sbin/ip a | grep inet | egrep -v 'inet6|127.0.0.1'  | awk -F' ' '{print $NF,$2}' | awk -F'/' '{print $1}'"
    deviceTypeCmd = "/usr/sbin/dmidecode -t 1|grep Manufacturer|cut -d ':' -f2|cut -d ' ' -f2"
    deviceModleCmd = "/usr/sbin/dmidecode -t 1|grep 'Product Name'|cut -d : -f2"
    deviceSnCmd = "/usr/sbin/dmidecode -t 1|grep 'Serial Number'|cut -d : -f2"
    #memorySlotsNumberCmd = "/usr/sbin/dmidecode |grep -A16 'Memory Device$'|grep -c 'Size'"
    memorySlotsInUsedCmd = "/usr/sbin/dmidecode |grep -A16 'Memory Device$'|grep 'Size'| grep -c 'MB'"
    #memorySizeEachCmd = " /usr/sbin/dmidecode |grep -A16 'Memory Device$'|grep 'Size' | grep MB |head -n 1 | awk '{print $2}'"
    memorySizeEachCmd = "/usr/sbin/dmidecode|grep -P -A5 'Memory\s+Device'|grep Size|grep -v Range | awk -F'Size:' '{print $2}'"
    physicalCpuModelCmd = "cat /proc/cpuinfo |grep 'model name' |head -n 1|cut -d : -f2"
    physicalCpuCoresCmd = "cat /proc/cpuinfo |grep 'physical id' | sort -r -n  -k4 | head -n 1 | cut -d : -f2"
    physicalNetWorkCardsCmd = "/sbin/lspci|grep 'Ethernet controller' -c"
    systemOSCmd = "cat /etc/issue | sed -n 1p"
    systemBitCmd = "/bin/uname -m"
    systemHostnameCmd = "/bin/hostname"

    hardwareList = {}
    hardwareList.update({"deviceType": getCmdResult(deviceTypeCmd)})
    hardwareList.update({"deviceModle": getCmdResult(deviceTypeCmd)+" "+getCmdResult(deviceModleCmd)})
    hardwareList.update({"deviceSn": getCmdResult(deviceSnCmd)})
    hardwareList.update({"memorySlotsInUsed": getCmdResult(memorySlotsInUsedCmd)})
    memorySizeAll=getCmdResult(memorySizeEachCmd).split('\n')
    memorySizeEach={}
    for i in range(0,len(memorySizeAll)):
	memorySizeEach.update({i:memorySizeAll[i]})
    #hardwareList.update({"memorySizeEach": getCmdResult(memorySizeEachCmd).split('\n')})
    hardwareList.update({"memorySizeEach": memorySizeEach})

    ipAll=getCmdResult(deviceIpCmd).split('\n')
    ipEach={}
    
    for i in range(0,len(ipAll)):
	ipEach.update({i:ipAll[i]})
    hardwareList.update({"ipEach": ipEach})

    cupCores = getCmdResult(physicalCpuCoresCmd)
    if cupCores == '':
        cupCores = 1
    else:
        cupCores = int(cupCores) + 1
    hardwareList.update({"cpuCores": cupCores})
    hardwareList.update({"cpuModel": getCmdResult(physicalCpuModelCmd)+" * "+str(cupCores)})
    hardwareList.update({"networkCards": getCmdResult(physicalNetWorkCardsCmd)})
    hardwareList.update({"systemOS": getCmdResult(systemOSCmd) + getCmdResult(systemBitCmd)})
    hardwareList.update({"raidControl": raidControl})
    hardwareList.update({"diskInfo": diskInfo})
    hardwareList.update({"hostName": getCmdResult(systemHostnameCmd)})
    #hardwareList.update({"disk":disk})


    file1 = sys.argv[1]
    #resoutput(hardwareList)
    if file1 == 'all' :
	resoutput(hardwareList)

    else:
	resoutput(hardwareList[file1])

