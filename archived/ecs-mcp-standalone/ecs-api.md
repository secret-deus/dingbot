调用DescribeInstanceMonitorData查询一台ECS实例的监控信息。可查询的指标包括ECS实例的vCPU使用率、突发性能实例积分、接收的数据流量、发送的数据流量、平均带宽等。

接口说明
调用该接口时，您需要注意：

一次最多返回 400 条数据，需满足（EndTime–StartTime）/Period小于等于 400 的条件限制，即返回参数TotalCount不能超过 400，否则将返回InvalidParameter.TooManyDataQueried的错误提示。

一次最多能查询近 30 天内的监控信息，即指定的参数StartTime距今不能超过 30 天。

当返回信息中缺少部分内容时，可能是系统没有获取到相应的信息。例如，当时实例处于已停止（Stopped）状态。

该接口暂无法获取 EBM 弹性裸金属实例的 CPU 基础监控信息，您可通过安装云监控插件获取 CPU 监控信息。具体操作，请参见安装云监控插件。

调试
您可以在OpenAPI Explorer中直接运行该接口，免去您计算签名的困扰。运行成功后，OpenAPI Explorer可以自动生成SDK代码示例。

调试
授权信息
下表是API对应的授权信息，可以在RAM权限策略语句的Action元素中使用，用来给RAM用户或RAM角色授予调用此API的权限。具体说明如下：

操作：是指具体的权限点。
访问级别：是指每个操作的访问级别，取值为写入（Write）、读取（Read）或列出（List）。
资源类型：是指操作中支持授权的资源类型。具体说明如下：
对于必选的资源类型，用前面加 * 表示。
对于不支持资源级授权的操作，用全部资源表示。
条件关键字：是指云产品自身定义的条件关键字。
关联操作：是指成功执行操作所需要的其他权限。操作者必须同时具备关联操作的权限，操作才能成功。
操作	访问级别	资源类型	条件关键字	关联操作
ecs:DescribeInstanceMonitorData	get
*Instance
acs:ecs:{#regionId}:{#accountId}:instance/{#instanceId}
无
无
请求参数
名称	类型	必填	描述	示例值
InstanceId	string	是
待查询的实例 ID。

i-bp1a36962lrhj4ab****
StartTime	string	是
获取数据的起始时间点。按照ISO 8601标准表示，并使用 UTC +0 时间，格式为 yyyy-MM-ddTHH:mm:ssZ。如果指定的秒（ss）不是00，则自动换算为下一分钟。

2014-10-29T23:00:00Z
EndTime	string	是
获取数据的结束时间点。按照ISO 8601标准表示，并使用 UTC +0 时间，格式为 yyyy-MM-ddTHH:mm:ssZ。如果指定的秒（ss）不是00，则自动换算为下一分钟。

2014-10-30T08:00:00Z
Period	integer	否
获取监控数据的间隔时间，单位：秒。取值范围：

60。
600。
3600。
默认值：60。

60
返回参数
名称	类型	描述	示例值
object
RequestId	string
请求 ID。

473469C7-AA6F-4DC5-B3DB-A3DC0DE3C83E
MonitorData	array<object>
实例的监控数据集合。

InstanceMonitorData	object
CPUCreditBalance	float
突发性能实例积分总数。

120
BPSRead	integer
实例云盘（包括系统盘和数据盘）的读带宽，单位：Byte/s。

1000
InternetTX	integer
在查询监控信息时（TimeStamp），实例在指定的间隔时间（Period）内发送的公网数据流量。单位：kbits。

343
CPU	integer
实例 vCPU 的使用比例，单位：百分比（%）。

2
CPUCreditUsage	float
突发性能实例已使用的积分数。

30
IOPSWrite	integer
实例云盘（包括系统盘和数据盘）的 I/O 写操作，单位：次/s。

200
IntranetTX	integer
在查询监控信息时（TimeStamp），实例在指定的间隔时间（Period）内发送的内网数据流量。单位：kbits。

343
InstanceId	string
实例 ID。

i-bp1a36962lrhj4****
BPSWrite	integer
实例云盘（包括系统盘和数据盘）的写带宽，单位：Byte/s。

13585
CPUNotpaidSurplusCreditUsage	float
超额未支付积分。

0.5
CPUAdvanceCreditBalance	float
超额积分（突发性能实例积分超限部分）。

0.4
IOPSRead	integer
实例云盘（包括系统盘和数据盘）的 I/O 读操作，单位：次/s。

1000
InternetBandwidth	integer
实例的公网带宽，单位时间内的网络流量，单位：kbits/s。

10
InternetRX	integer
在查询监控信息时（TimeStamp），实例在指定的间隔时间（Period）内接收的公网数据流量。单位：kbits。

122
TimeStamp	string
查询监控信息的时间戳。

2014-10-30T05:00:00Z
IntranetRX	integer
在查询监控信息时（TimeStamp），实例在指定的间隔时间（Period）内接收的内网数据流量。单位：kbits。

122
IntranetBandwidth	integer
实例的内网带宽，单位时间内的网络流量，单位：kbits/s。

10
示例
正常返回示例

JSON格式


{
  "RequestId": "473469C7-AA6F-4DC5-B3DB-A3DC0DE3C83E",
  "MonitorData": {
    "InstanceMonitorData": [
      {
        "CPUCreditBalance": 120,
        "BPSRead": 1000,
        "InternetTX": 343,
        "CPU": 2,
        "CPUCreditUsage": 30,
        "IOPSWrite": 200,
        "IntranetTX": 343,
        "InstanceId": "i-bp1a36962lrhj4****",
        "BPSWrite": 13585,
        "CPUNotpaidSurplusCreditUsage": 0.5,
        "CPUAdvanceCreditBalance": 0.4,
        "IOPSRead": 1000,
        "InternetBandwidth": 10,
        "InternetRX": 122,
        "TimeStamp": "2014-10-30T05:00:00Z",
        "IntranetRX": 122,
        "IntranetBandwidth": 10
      }
    ]
  }
}
错误码
HTTP status code	错误码	错误信息	描述
HTTP status code	错误码	错误信息	描述
400	InvalidStartTime.Malformed	The specified parameter "StartTime" is not valid.	指定的StartTime参数不符合规范。
400	InvalidEndTime.Malformed	The specified parameter "EndTime" is not valid.	传入的参数EndTime不符合规则。
400	InvalidPeriod.ValueNotSupported	The specified parameter "Period" is not valid.	-
400	InvalidStartTime.TooEarly	The specified parameter "StartTime" is too early.	-
400	InvalidParameter.TooManyDataQueried	Too many data queried.	监控数据节点超出范围。
400	Throttling	Request was denied due to request throttling.	请求被流控。
400	InvalidStartTime.ValueNotSupported	The specified parameter StartTime is later than EndTime.	结束时间不能早于开始时间。
404	InvalidInstanceId.NotFound	The specified InstanceId does not exist.	指定的实例ID无效。
500	InternalError	The request processing has failed due to some unknown error.	内部错误，请重试。
