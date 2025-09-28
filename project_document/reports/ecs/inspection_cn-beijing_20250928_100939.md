# ECS巡检报告

- 开始: 2025-09-28 10:09:39 UTC
- 结束: 2025-09-28 10:09:39 UTC
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
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | medium | - | - | 87.54 | cn-beijing-d | Running |
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | - | - | 61.9 | cn-beijing-d | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | 11.455 | - | 36.64 | cn-beijing-d | Running |
| i-2zeevtwyz9h2ls5aka25 | 生产-阳光链-后端-live节点-002 | low | - | - | 42.79 | cn-beijing-a | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | 14.228 | - | - | cn-beijing-h | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | 12.23 | - | - | cn-beijing-b | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | - | - | 7.62 | cn-beijing-h | Running |
| i-2ze6mjqj6m1bjp3uuhsi | 生产-运维-公益基金会推广 | low | - | - | - | cn-beijing-a | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | - | cn-beijing-h | Running |

## 明细（采样）
### i-2ze6mjqj6m1bjp3uuhsi (生产-运维-公益基金会推广)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:11:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "InternetRX": null
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:11:00Z",
    "InternetTX": null,
    "IntranetInRate": 915.319
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "InternetTX": null,
    "IntranetInRate": 2545.39
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "InternetTX": null,
    "IntranetInRate": 671.197
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
    "TimeStamp": "2025-09-28T01:11:00Z",
    "IntranetInRate": 2486.135
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "IntranetInRate": 2659.396
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "IntranetInRate": 915.319
  }
]
```

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=12.021333333333333, p95=12.23, max=12.497
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:15:00Z",
    "CPU": 12.126
  },
  {
    "TimeStamp": "2025-09-28T01:20:00Z",
    "CPU": 11.931
  },
  {
    "TimeStamp": "2025-09-28T01:25:00Z",
    "CPU": 11.996
  }
]
```

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: medium | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': True}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:11:00Z",
    "DiskUsageUtilization": 87.54
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "DiskUsageUtilization": 87.54
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "DiskUsageUtilization": 87.54
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.152500000000002, p95=14.228, max=14.436
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:11:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "InternetRX": null
  }
]
```

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:11:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "InternetRX": null
  }
]
```

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.46725, p95=11.455, max=12.963
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:11:00Z",
    "CPU": 9.092,
    "DiskUsageUtilization": 36.63
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "CPU": 6.724,
    "DiskUsageUtilization": 36.63
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "CPU": 6.656,
    "DiskUsageUtilization": 36.63
  }
]
```

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:11:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "InternetRX": null
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
    "TimeStamp": "2025-09-28T01:11:00Z",
    "DiskUsageUtilization": 42.79
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "DiskUsageUtilization": 42.79
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "DiskUsageUtilization": 42.79
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
    "TimeStamp": "2025-09-28T01:11:00Z",
    "InternetTX": null,
    "DiskUsageUtilization": 7.62
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "InternetTX": null,
    "DiskUsageUtilization": 7.62
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "InternetTX": null,
    "DiskUsageUtilization": 7.62
  }
]
```

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:11:00Z",
    "InternetRX": null,
    "DiskUsageUtilization": 61.89
  },
  {
    "TimeStamp": "2025-09-28T01:12:00Z",
    "InternetRX": null,
    "DiskUsageUtilization": 61.89
  },
  {
    "TimeStamp": "2025-09-28T01:13:00Z",
    "InternetRX": null,
    "DiskUsageUtilization": 61.89
  }
]
```
