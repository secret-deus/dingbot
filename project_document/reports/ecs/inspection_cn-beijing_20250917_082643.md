# ECS巡检报告

- 开始: 2025-09-17 08:26:43 UTC
- 结束: 2025-09-17 08:26:43 UTC
- 地域: ['cn-beijing']
- 实例数: 12
- 窗口: 1h
- 并发: 5
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 0
- 低风险: 12

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | - | 63.335 | 24.47 | cn-beijing-b | Running |
| i-2zed7senuu0ctl35xxqr | 生产-平台支撑-数据-01 | low | - | 68.442 | - | cn-beijing-c | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | - | - | 17.64 | cn-beijing-h | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | 10.306 | - | - | cn-beijing-a | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | - | cn-beijing-h | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | - | - | - | cn-beijing-d | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | - | - | - | cn-beijing-d | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | - | - | - | cn-beijing-d | Running |
| i-2zeevtwyz9h2ls5aka25 | 生产-阳光链-后端-live节点-002 | low | - | - | - | cn-beijing-a | Running |

## 明细（采样）
### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:27:00Z",
    "InternetRX": null,
    "IOPSWrite": 1.783
  },
  {
    "TimeStamp": "2025-09-16T23:28:00Z",
    "InternetRX": null,
    "IOPSWrite": 1.75
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "InternetRX": null,
    "IOPSWrite": 1.816
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
    "TimeStamp": "2025-09-16T23:27:00Z",
    "IntranetOutRate": 8864.972
  },
  {
    "TimeStamp": "2025-09-16T23:28:00Z",
    "IntranetOutRate": 12266.973
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "IntranetOutRate": 8720.52
  }
]
```

### i-2zecc9f3sh2gux9giscv (生产-crm-驰云代理服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=9.593966666666667, p95=10.306, max=10.628
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:27:00Z",
    "CPU": 9.244,
    "InternetTX": null,
    "IntranetInRate": 24.759
  },
  {
    "TimeStamp": "2025-09-16T23:28:00Z",
    "CPU": 9.431,
    "InternetTX": null,
    "IntranetInRate": 6.521
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "CPU": 9.408,
    "InternetTX": null,
    "IntranetInRate": 6.308
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
    "TimeStamp": "2025-09-16T23:27:00Z",
    "MemoryUtilization": 62.857,
    "DiskUsageUtilization": 24.47
  },
  {
    "TimeStamp": "2025-09-16T23:28:00Z",
    "MemoryUtilization": 62.905,
    "DiskUsageUtilization": 24.47
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "MemoryUtilization": 62.91,
    "DiskUsageUtilization": 24.47
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
    "TimeStamp": "2025-09-16T23:27:00Z",
    "InternetTX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:28:00Z",
    "InternetTX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "InternetTX": null,
    "IOPSRead": null
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:28:00Z",
    "InternetTX": null,
    "IntranetInRate": 4.705,
    "DiskUsageUtilization": 17.64
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "InternetTX": null,
    "IntranetInRate": 4.617,
    "DiskUsageUtilization": 17.64
  },
  {
    "TimeStamp": "2025-09-16T23:30:00Z",
    "InternetTX": null,
    "IntranetInRate": 16.241,
    "DiskUsageUtilization": 17.64
  }
]
```

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
    "TimeStamp": "2025-09-16T23:28:00Z",
    "InternetRX": null,
    "IOPSWrite": 8.933
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "InternetRX": null,
    "IOPSWrite": 10.183
  },
  {
    "TimeStamp": "2025-09-16T23:30:00Z",
    "InternetRX": null,
    "IOPSWrite": 9.8
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
    "TimeStamp": "2025-09-16T23:28:00Z",
    "InternetTX": null,
    "MemoryUtilization": 68.337
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "InternetTX": null,
    "MemoryUtilization": 68.332
  },
  {
    "TimeStamp": "2025-09-16T23:30:00Z",
    "InternetTX": null,
    "MemoryUtilization": 68.35
  }
]
```

### i-2zeevtwyz9h2ls5aka25 (生产-阳光链-后端-live节点-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zef1jdvkslc2zj3f6zn (生产-极速筹-李丹-jisuchou.net备案用)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:28:00Z",
    "InternetTX": null,
    "IOPSRead": null,
    "IOPSWrite": 0.483
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "InternetTX": null,
    "IOPSRead": null,
    "IOPSWrite": 0.533
  },
  {
    "TimeStamp": "2025-09-16T23:30:00Z",
    "InternetTX": null,
    "IOPSRead": null,
    "IOPSWrite": 0.45
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
    "TimeStamp": "2025-09-16T23:28:00Z",
    "InternetTX": null,
    "IntranetOutRate": 69168.878,
    "IOPSWrite": 17.55
  },
  {
    "TimeStamp": "2025-09-16T23:29:00Z",
    "InternetTX": null,
    "IntranetOutRate": 69467.477,
    "IOPSWrite": 18.266
  },
  {
    "TimeStamp": "2025-09-16T23:30:00Z",
    "InternetTX": null,
    "IntranetOutRate": 71696.52,
    "IOPSWrite": 16.883
  }
]
```
