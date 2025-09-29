# ECS巡检报告

- 开始: 2025-09-29 03:02:44 UTC
- 结束: 2025-09-29 03:02:44 UTC
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
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | 29.868 | - | - | cn-beijing-d | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | 14.3 | - | 17.68 | cn-beijing-h | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | 6.93 | - | 22.0 | cn-beijing-d | Running |
| i-2zeevtwyz9h2ls5aka25 | 生产-阳光链-后端-live节点-002 | low | - | 20.18 | - | cn-beijing-a | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | 8.739 | - | - | cn-beijing-d | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | 1.964 | - | 6.72 | cn-beijing-h | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | - | - | 7.61 | cn-beijing-h | Running |
| i-2ze6mjqj6m1bjp3uuhsi | 生产-运维-公益基金会推广 | low | 0.605 | - | - | cn-beijing-a | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | 0.242 | - | - | cn-beijing-i | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |

## 明细（采样）
### i-2ze6mjqj6m1bjp3uuhsi (生产-运维-公益基金会推广)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.5452666666666667, p95=0.605, max=0.925
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "CPU": 0.516
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 0.563
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "CPU": 0.545
  }
]
```

### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.23875, p95=0.242, max=0.246
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 0.234,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "InternetRX": null
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.8250333333333333, p95=1.964, max=2.011
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "CPU": 1.854,
    "IntranetInRate": 2316.288,
    "DiskUsageUtilization": 6.72
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 1.806,
    "IntranetInRate": 646.075,
    "DiskUsageUtilization": 6.72
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "CPU": 1.675,
    "IntranetInRate": 702.19,
    "DiskUsageUtilization": 6.72
  }
]
```

### i-2zecc9f3sh2gux9giscv (生产-crm-驰云代理服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "InternetRX": null
  }
]
```

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.889266666666667, p95=8.739, max=9.354
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "CPU": 8.419
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 8.025
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "CPU": 8.845
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.100083333333332, p95=14.3, max=14.499
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "IntranetOutRate": 8808.994,
    "DiskUsageUtilization": 17.68
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 14.138,
    "IntranetOutRate": 9126.707,
    "DiskUsageUtilization": 17.68
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "IntranetOutRate": 9125.068,
    "DiskUsageUtilization": 17.68
  }
]
```

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.68375, p95=6.93, max=7.131
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "DiskUsageUtilization": 22.0
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 7.131,
    "DiskUsageUtilization": 22.0
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "DiskUsageUtilization": 22.0
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
    "TimeStamp": "2025-09-28T18:04:00Z",
    "InternetTX": null,
    "IntranetInRate": 22.246
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "InternetTX": null,
    "IntranetInRate": 29.856
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "InternetTX": null,
    "IntranetInRate": 45.715
  }
]
```

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zeevtwyz9h2ls5aka25 (生产-阳光链-后端-live节点-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "InternetRX": null,
    "MemoryUtilization": 20.157
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "InternetRX": null,
    "MemoryUtilization": 20.15
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "InternetRX": null,
    "MemoryUtilization": 20.147
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
    "TimeStamp": "2025-09-28T18:04:00Z",
    "InternetTX": null,
    "IntranetInRate": 18.653,
    "DiskUsageUtilization": 7.61
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "InternetTX": null,
    "IntranetInRate": 157.427,
    "DiskUsageUtilization": 7.61
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "InternetTX": null,
    "IntranetInRate": 7.042,
    "DiskUsageUtilization": 7.61
  }
]
```

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=29.1882, p95=29.868, max=31.041
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:04:00Z",
    "CPU": 29.011,
    "IntranetOutRate": 68897.86
  },
  {
    "TimeStamp": "2025-09-28T18:05:00Z",
    "CPU": 31.041,
    "IntranetOutRate": 68766.515
  },
  {
    "TimeStamp": "2025-09-28T18:06:00Z",
    "CPU": 29.178,
    "IntranetOutRate": 76179.182
  }
]
```
