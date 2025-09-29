# ECS巡检报告

- 开始: 2025-09-29 02:49:57 UTC
- 结束: 2025-09-29 02:49:57 UTC
- 地域: ['cn-beijing']
- 实例数: 13
- 窗口: 1h
- 并发: 5
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 0
- 低风险: 13

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | 29.321 | - | 61.91 | cn-beijing-d | Running |
| i-2zed7senuu0ctl35xxqr | 生产-平台支撑-数据-01 | low | 33.881 | - | - | cn-beijing-c | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | 7.247 | - | 36.47 | cn-beijing-d | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | 11.847 | - | - | cn-beijing-b | Running |
| i-2zeevtwyz9h2ls5aka25 | 生产-阳光链-后端-live节点-002 | low | 2.599 | - | - | cn-beijing-a | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | 1.964 | - | - | cn-beijing-h | Running |
| i-2ze6mjqj6m1bjp3uuhsi | 生产-运维-公益基金会推广 | low | 0.549 | - | - | cn-beijing-a | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | 0.259 | - | - | cn-beijing-i | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | - | - | - | cn-beijing-d | Running |

## 明细（采样）
### i-2ze6mjqj6m1bjp3uuhsi (生产-运维-公益基金会推广)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.5398333333333334, p95=0.549, max=0.618
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:55:00Z",
    "CPU": 0.541
  },
  {
    "TimeStamp": "2025-09-28T18:00:00Z",
    "CPU": 0.523
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 0.535
  }
]
```

### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.23866666666666667, p95=0.259, max=0.268
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:51:00Z",
    "CPU": 0.256,
    "InternetRX": null,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T17:52:00Z",
    "CPU": 0.225,
    "InternetRX": null,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T17:53:00Z",
    "CPU": 0.233,
    "InternetRX": null,
    "InternetTX": null
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.8012166666666667, p95=1.964, max=1.998
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:51:00Z",
    "CPU": 1.57,
    "IntranetOutRate": 9573.171
  },
  {
    "TimeStamp": "2025-09-28T17:52:00Z",
    "CPU": 1.609,
    "IntranetOutRate": 9894.843
  },
  {
    "TimeStamp": "2025-09-28T17:53:00Z",
    "CPU": 1.71,
    "IntranetOutRate": 9828.215
  }
]
```

### i-2zecc9f3sh2gux9giscv (生产-crm-驰云代理服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:51:00Z",
    "IntranetInRate": 6.188
  },
  {
    "TimeStamp": "2025-09-28T17:52:00Z",
    "IntranetInRate": 16.821
  },
  {
    "TimeStamp": "2025-09-28T17:53:00Z",
    "IntranetInRate": 6.331
  }
]
```

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=11.45375, p95=11.847, max=12.418
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:55:00Z",
    "CPU": 11.252
  },
  {
    "TimeStamp": "2025-09-28T18:00:00Z",
    "CPU": 11.172
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 11.511
  }
]
```

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:51:00Z",
    "IntranetOutRate": 8503.705
  },
  {
    "TimeStamp": "2025-09-28T17:52:00Z",
    "IntranetOutRate": 10103.603
  },
  {
    "TimeStamp": "2025-09-28T17:53:00Z",
    "IntranetOutRate": 8935.56
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.6915666666666676, p95=7.247, max=7.573
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:51:00Z",
    "CPU": 6.849,
    "IntranetInRate": 50.527,
    "DiskUsageUtilization": 36.46
  },
  {
    "TimeStamp": "2025-09-28T17:52:00Z",
    "CPU": 6.604,
    "IntranetInRate": 24.35,
    "DiskUsageUtilization": 36.46
  },
  {
    "TimeStamp": "2025-09-28T17:53:00Z",
    "CPU": 6.32,
    "IntranetInRate": 51.703,
    "DiskUsageUtilization": 36.47
  }
]
```

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=33.245066666666666, p95=33.881, max=34.146
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:51:00Z",
    "CPU": 33.78
  },
  {
    "TimeStamp": "2025-09-28T17:52:00Z",
    "CPU": 31.52
  },
  {
    "TimeStamp": "2025-09-28T17:53:00Z",
    "CPU": 33.334
  }
]
```

### i-2zeevtwyz9h2ls5aka25 (生产-阳光链-后端-live节点-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.5873333333333335, p95=2.599, max=2.604
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:51:00Z",
    "InternetRX": null,
    "IntranetOutRate": 70.1
  },
  {
    "TimeStamp": "2025-09-28T17:52:00Z",
    "InternetRX": null,
    "IntranetOutRate": 74.774
  },
  {
    "TimeStamp": "2025-09-28T17:53:00Z",
    "InternetRX": null,
    "IntranetOutRate": 71.191
  }
]
```

### i-2zef1jdvkslc2zj3f6zn (生产-极速筹-李丹-jisuchou.net备案用)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=29.297250000000002, p95=29.321, max=30.694
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:51:00Z",
    "IntranetInRate": 4837.512,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T17:52:00Z",
    "IntranetInRate": 5030.57,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T17:53:00Z",
    "IntranetInRate": 5209.975,
    "DiskUsageUtilization": 61.91
  }
]
```
