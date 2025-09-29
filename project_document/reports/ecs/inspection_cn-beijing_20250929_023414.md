# ECS巡检报告

- 开始: 2025-09-29 02:34:14 UTC
- 结束: 2025-09-29 02:34:14 UTC
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
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | 30.128 | - | 61.91 | cn-beijing-d | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | 12.558 | - | 24.62 | cn-beijing-b | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | 14.345 | - | 17.68 | cn-beijing-h | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | 9.503 | - | - | cn-beijing-h | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | 8.519 | - | - | cn-beijing-d | Running |
| i-2ze6mjqj6m1bjp3uuhsi | 生产-运维-公益基金会推广 | low | 0.57 | - | - | cn-beijing-a | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | - | cn-beijing-h | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | - | - | - | cn-beijing-d | Running |

## 明细（采样）
### i-2ze6mjqj6m1bjp3uuhsi (生产-运维-公益基金会推广)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.5331833333333333, p95=0.57, max=0.906
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:35:00Z",
    "CPU": 0.519
  },
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "CPU": 0.521
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "CPU": 0.513
  }
]
```

### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:35:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "InternetRX": null
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
    "TimeStamp": "2025-09-28T17:35:00Z",
    "IntranetInRate": 1811.114,
    "IntranetOutRate": 73.381
  },
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "IntranetInRate": 800.768,
    "IntranetOutRate": 70.338
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "IntranetInRate": 2359.022,
    "IntranetOutRate": 71.061
  }
]
```

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=11.376583333333334, p95=12.558, max=13.504
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:35:00Z",
    "CPU": 11.364,
    "InternetRX": null,
    "DiskUsageUtilization": 24.62
  },
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "CPU": 11.209,
    "InternetRX": null,
    "DiskUsageUtilization": 24.62
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "CPU": 11.548,
    "InternetRX": null,
    "DiskUsageUtilization": 24.62
  }
]
```

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.954, p95=8.519, max=8.641
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:35:00Z",
    "CPU": 7.115
  },
  {
    "TimeStamp": "2025-09-28T17:40:00Z",
    "CPU": 7.417
  },
  {
    "TimeStamp": "2025-09-28T17:45:00Z",
    "CPU": 7.325
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.092, p95=14.345, max=14.428
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:35:00Z",
    "CPU": 13.991,
    "IntranetInRate": 16.838,
    "DiskUsageUtilization": 17.68
  },
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "CPU": 14.141,
    "IntranetInRate": 5.608,
    "DiskUsageUtilization": 17.68
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "CPU": 14.247,
    "IntranetInRate": 5.013,
    "DiskUsageUtilization": 17.68
  }
]
```

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:35:00Z",
    "IntranetOutRate": 17639.833
  },
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "IntranetOutRate": 16940.509
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "IntranetOutRate": 17859.925
  }
]
```

### i-2zeevtwyz9h2ls5aka25 (生产-阳光链-后端-live节点-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 13674.769
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 9886.515
  },
  {
    "TimeStamp": "2025-09-28T17:38:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 9505.86
  }
]
```

### i-2zef1jdvkslc2zj3f6zn (生产-极速筹-李丹-jisuchou.net备案用)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=9.031016666666666, p95=9.503, max=9.637
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "CPU": 9.23,
    "IntranetInRate": 6.823
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "CPU": 9.289,
    "IntranetInRate": 18.245
  },
  {
    "TimeStamp": "2025-09-28T17:38:00Z",
    "CPU": 8.978,
    "IntranetInRate": 7.284
  }
]
```

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=29.2892, p95=30.128, max=35.167
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:36:00Z",
    "CPU": 29.373,
    "IntranetInRate": 221.259,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T17:37:00Z",
    "CPU": 29.212,
    "IntranetInRate": 57.144,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T17:38:00Z",
    "CPU": 29.11,
    "IntranetInRate": 37.482,
    "DiskUsageUtilization": 61.91
  }
]
```
