# ECS巡检报告

- 时间: 2025-09-17 03:07:19 UTC
- 地域: cn-hangzhou
- 实例数: 3
- 窗口: 1h
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 0
- 低风险: 3

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-bp1hh4jmc5lq815psq6v | 生产-微爱-区块链-002 | low | 0.093 | - | - | cn-hangzhou-b | Running |
| i-bp1j4jvdujrtenkmndyt | 生产-crm-驰云中心服务器-安卓 | low | - | - | - | cn-hangzhou-h | Running |
| i-bp13yabzr5882mivlycf | 生产-微爱-区块链-单点临时使用-001 | low | - | - | - | cn-hangzhou-b | Running |

## 明细（采样）
### i-bp1j4jvdujrtenkmndyt (生产-crm-驰云中心服务器-安卓)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T18:08:00Z",
    "InternetRX": null,
    "IOPSWrite": 1.966
  },
  {
    "TimeStamp": "2025-09-16T18:09:00Z",
    "InternetRX": null,
    "IOPSWrite": 5.6
  },
  {
    "TimeStamp": "2025-09-16T18:10:00Z",
    "InternetRX": null,
    "IOPSWrite": 8.733
  }
]
```

### i-bp13yabzr5882mivlycf (生产-微爱-区块链-单点临时使用-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T18:08:00Z",
    "IntranetInRate": 6084.434
  },
  {
    "TimeStamp": "2025-09-16T18:09:00Z",
    "IntranetInRate": 6414.113
  },
  {
    "TimeStamp": "2025-09-16T18:10:00Z",
    "IntranetInRate": 5105.323
  }
]
```

### i-bp1hh4jmc5lq815psq6v (生产-微爱-区块链-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.08498305084745764, p95=0.093, max=0.098
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T18:08:00Z",
    "CPU": 0.083,
    "InternetRX": null,
    "InternetTX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T18:09:00Z",
    "CPU": 0.085,
    "InternetRX": null,
    "InternetTX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T18:10:00Z",
    "CPU": 0.081,
    "InternetRX": null,
    "InternetTX": null,
    "IOPSRead": null
  }
]
```
