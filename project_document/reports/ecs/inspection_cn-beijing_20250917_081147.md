# ECS巡检报告

- 开始: 2025-09-17 08:11:47 UTC
- 结束: 2025-09-17 08:11:47 UTC
- 地域: ['cn-beijing']
- 实例数: 12
- 窗口: 1h
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 0
- 低风险: 12

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | - | 50.525 | - | cn-beijing-d | Running |
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | - | - | 61.62 | cn-beijing-d | Running |
| i-2zeevtwyz9h2ls5aka25 | 生产-阳光链-后端-live节点-002 | low | 2.669 | - | - | cn-beijing-a | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | 1.991 | - | - | cn-beijing-h | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | - | - | - | cn-beijing-b | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | - | - | - | cn-beijing-d | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | - | - | - | cn-beijing-h | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | - | - | - | cn-beijing-d | Running |

## 明细（采样）
### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:12:00Z",
    "IntranetInRate": 916.957
  },
  {
    "TimeStamp": "2025-09-16T23:13:00Z",
    "IntranetInRate": 1008.298
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "IntranetInRate": 24401.373
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.7911525423728814, p95=1.991, max=2.017
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:12:00Z",
    "CPU": 1.702
  },
  {
    "TimeStamp": "2025-09-16T23:13:00Z",
    "CPU": 1.819
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "CPU": 1.754
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
    "TimeStamp": "2025-09-16T23:12:00Z",
    "IOPSRead": 0.016
  },
  {
    "TimeStamp": "2025-09-16T23:13:00Z",
    "IOPSRead": 0.033
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "IOPSRead": 0.016
  }
]
```

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:12:00Z",
    "InternetTX": null,
    "IntranetOutRate": 11788.014
  },
  {
    "TimeStamp": "2025-09-16T23:13:00Z",
    "InternetTX": null,
    "IntranetOutRate": 12018.483
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "InternetTX": null,
    "IntranetOutRate": 11252.804
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
    "TimeStamp": "2025-09-16T23:12:00Z",
    "InternetRX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:13:00Z",
    "InternetRX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "InternetRX": null,
    "IOPSRead": null
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
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:13:00Z",
    "InternetRX": null,
    "IntranetInRate": 2668.544,
    "IOPSRead": null,
    "MemoryUtilization": 50.337
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "InternetRX": null,
    "IntranetInRate": 4712.038,
    "IOPSRead": null,
    "MemoryUtilization": 50.355
  },
  {
    "TimeStamp": "2025-09-16T23:15:00Z",
    "InternetRX": null,
    "IntranetInRate": 26642.705,
    "IOPSRead": null,
    "MemoryUtilization": 50.367
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
    "TimeStamp": "2025-09-16T23:13:00Z",
    "IntranetInRate": 1265.39,
    "IntranetOutRate": 15233.706,
    "IOPSWrite": 15.383
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "IntranetInRate": 1442.201,
    "IntranetOutRate": 17938.705,
    "IOPSWrite": 14.183
  },
  {
    "TimeStamp": "2025-09-16T23:15:00Z",
    "IntranetInRate": 2903.381,
    "IntranetOutRate": 16146.432,
    "IOPSWrite": 14.933
  }
]
```

### i-2zeevtwyz9h2ls5aka25 (生产-阳光链-后端-live节点-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.6226166666666666, p95=2.669, max=2.963
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:13:00Z",
    "CPU": 2.608,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "CPU": 2.568,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-16T23:15:00Z",
    "CPU": 2.619,
    "InternetRX": null
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
    "TimeStamp": "2025-09-16T23:13:00Z",
    "IntranetOutRate": 66.399,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "IntranetOutRate": 68.038,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:15:00Z",
    "IntranetOutRate": 65.543,
    "IOPSRead": null
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
    "TimeStamp": "2025-09-16T23:13:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 30.774,
    "IOPSWrite": 16.65,
    "DiskUsageUtilization": 61.62
  },
  {
    "TimeStamp": "2025-09-16T23:14:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 34.248,
    "IOPSWrite": 18.75,
    "DiskUsageUtilization": 61.62
  },
  {
    "TimeStamp": "2025-09-16T23:15:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 203.962,
    "IOPSWrite": 17.483,
    "DiskUsageUtilization": 61.62
  }
]
```
