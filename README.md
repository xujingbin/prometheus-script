### 步骤
1. 对服务端开放7080端口，目前服务端部署在测试机器10.0.0.194上
2. 将目录拷贝至/usr/local/proms-agent下，修改script/conf/的json文件的tag值，改成机器所属group，如"统计项目",consul.json的"datacenter","retry_join"参数
3. 每个数据中心配置三个consul server，用script/bak下的consul-server.json替换script/conf下的consul.json并在init.sh、check.sh的相应启动位置添加启动参数-bootstrap-expect=3,修改配置文件的配置
4. 执行init.sh脚本，并添加至开机启动如：echo su - xujingbin  -c \"sh /usr/local/proms-agent/script/init.sh\" |sudo tee -a /etc/rc.d/rc.local
5. prometheus服务端上目前只添加了sys(loadavg,cpu,memory,net),url,nginx,redis,mysql服务，有新加服务类型须在prometheus.yml添加并reload即可,其中redis监听端口与内网ip没有统一，为排除redis-cluster监听的多个端口情况，所以在添加到其他机房时，需修改redis.py的实例发现语句
6. 图形展示由grafana负责，所以需要单独添加到grafana上，服务发现由consul负责，是自下而上模式，告警由alertmanager完成,目前邮件模式只添加了全站

### consul 
![consul 架构图](script/bak/consul.png)

### 什么是 TSDB (Time Series Database):

**我们可以简单的理解为.一个优化后用来处理时间序列数据的软件,并且数据中的数组是由时间进行索引的.**   

时间序列数据库的特点:

* 大部分时间都是写入操作
* 写入操作几乎是顺序添加;大多数时候数据到达后都以时间排序.
* 写操作很少写入很久之前的数据,也很少更新数据.大多数情况在数据被采集到数秒或者数分钟后就会被写入数据库.
* 删除操作一般为区块删除,选定开始的历史时间并指定后续的区块.很少单独删除某个时间或者分开的随机时间的数据.
* 数据一般远远超过内存大小,所以缓存基本无用.系统一般是 IO 密集型
* 读操作是十分典型的升序或者降序的顺序读,
* 高并发的读操作十分常见.

### 相关文档：
1. [Prometheus的架构及持久化](http://www.cnblogs.com/vovlie/p/Prometheus_CONCEPTS.html)
2. [对监控系统的一些思考](http://www.360doc.com/content/16/1218/17/35463447_615775576.shtml)
3. [prometheus特性](http://www.cnblogs.com/vovlie/p/Prometheus_CONCEPTS.html)
4. [时间序列数据库比较 TSDB](http://www.uml.org.cn/sjjm/2016032210.asp?artid=17785)
