# ECS巡检报告

- 开始: 2025-09-29 05:51:53 UTC
- 结束: 2025-09-29 05:51:53 UTC
- 地域: ['cn-beijing']
- 实例数: 13
- 窗口: 1h
- 并发: 5
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 1
- 低风险: 12

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | 29.644 | - | 61.91 | cn-beijing-d | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | medium | - | - | 83.82 | cn-beijing-i | Running |
| i-2zed7senuu0ctl35xxqr | 生产-平台支撑-数据-01 | low | 33.789 | - | - | cn-beijing-c | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | - | 36.737 | - | cn-beijing-h | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | - | - | 36.49 | cn-beijing-d | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | 14.105 | - | - | cn-beijing-h | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | 7.551 | - | - | cn-beijing-d | Running |
| i-2zeevtwyz9h2ls5aka25 | 生产-阳光链-后端-live节点-002 | low | 2.629 | - | - | cn-beijing-a | Running |
| i-2ze6mjqj6m1bjp3uuhsi | 生产-运维-公益基金会推广 | low | 0.66 | - | - | cn-beijing-a | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | - | cn-beijing-h | Running |

## 明细（采样）
### i-2ze6mjqj6m1bjp3uuhsi (生产-运维-公益基金会推广)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.5641333333333333, p95=0.66, max=1.064
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "CPU": 0.573,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "CPU": 0.534,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "CPU": 0.66,
    "InternetTX": null
  }
]
```

### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: medium | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': True}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "InternetTX": null,
    "IntranetInRate": 1040.657,
    "DiskUsageUtilization": 83.82
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "InternetTX": null,
    "IntranetInRate": 870.673,
    "DiskUsageUtilization": 83.82
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "InternetTX": null,
    "IntranetInRate": 2445.585,
    "DiskUsageUtilization": 83.82
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zecc9f3sh2gux9giscv (生产-crm-驰云代理服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "InternetRX": null
  }
]
```

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "InternetTX": null,
    "IntranetOutRate": 9482.24
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "InternetTX": null,
    "IntranetOutRate": 8445.678
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "InternetTX": null,
    "IntranetOutRate": 9769.506
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.007166666666668, p95=14.105, max=14.19
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "CPU": 14.085,
    "InternetTX": null
  }
]
```

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.74075, p95=7.551, max=7.897
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "CPU": 6.711,
    "IntranetInRate": 3918.779
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "CPU": 6.665,
    "IntranetInRate": 4000.563
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "CPU": 6.829,
    "IntranetInRate": 5432.388
  }
]
```

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "IntranetInRate": 53.394,
    "DiskUsageUtilization": 36.49
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "IntranetInRate": 40.007,
    "DiskUsageUtilization": 36.49
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "IntranetInRate": 25.614,
    "DiskUsageUtilization": 36.49
  }
]
```

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=30.519483333333334, p95=33.789, max=34.072
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "CPU": 34.028,
    "IntranetOutRate": 17750.425
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "CPU": 33.668,
    "IntranetOutRate": 17310.378
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "CPU": 33.751,
    "IntranetOutRate": 19806.481
  }
]
```

### i-2zeevtwyz9h2ls5aka25 (生产-阳光链-后端-live节点-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.586316666666667, p95=2.629, max=2.643
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "CPU": 2.57,
    "IntranetInRate": 2563.413
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "CPU": 2.587,
    "IntranetInRate": 895.249
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "CPU": 2.577,
    "IntranetInRate": 4619.878
  }
]
```

### i-2zef1jdvkslc2zj3f6zn (生产-极速筹-李丹-jisuchou.net备案用)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "IntranetOutRate": 8853.23,
    "MemoryUtilization": 36.55
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "IntranetOutRate": 8719.974,
    "MemoryUtilization": 36.64
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "IntranetOutRate": 13216.29,
    "MemoryUtilization": 36.655
  }
]
```

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=29.234666666666666, p95=29.644, max=31.261
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T20:53:00Z",
    "CPU": 29.135,
    "InternetRX": null,
    "IntranetOutRate": 57926.041,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T20:54:00Z",
    "CPU": 29.309,
    "InternetRX": null,
    "IntranetOutRate": 72888.183,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T20:55:00Z",
    "CPU": 29.057,
    "InternetRX": null,
    "IntranetOutRate": 68021.589,
    "DiskUsageUtilization": 61.91
  }
]
```
