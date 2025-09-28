# ECS巡检报告

- 开始: 2025-09-28 10:34:38 UTC
- 结束: 2025-09-28 10:34:38 UTC
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
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | 31.969 | - | 61.9 | cn-beijing-d | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | - | 62.492 | - | cn-beijing-h | Running |
| i-2zeevtwyz9h2ls5aka25 | 生产-阳光链-后端-live节点-002 | low | - | - | 42.79 | cn-beijing-a | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | 10.358 | - | 8.0 | cn-beijing-a | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | 9.593 | - | - | cn-beijing-d | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | 6.822 | - | - | cn-beijing-d | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | - | - | 7.62 | cn-beijing-h | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | 1.977 | - | - | cn-beijing-h | Running |
| i-2ze6mjqj6m1bjp3uuhsi | 生产-运维-公益基金会推广 | low | - | - | - | cn-beijing-a | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |

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
    "TimeStamp": "2025-09-28T01:36:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "InternetTX": null
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.7167999999999999, p95=1.977, max=2.082
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:36:00Z",
    "CPU": 1.559,
    "IntranetOutRate": 71.906
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "CPU": 1.646,
    "IntranetOutRate": 69.132
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "CPU": 1.694,
    "IntranetOutRate": 109.854
  }
]
```

### i-2zecc9f3sh2gux9giscv (生产-crm-驰云代理服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=9.785833333333333, p95=10.358, max=15.389
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:36:00Z",
    "CPU": 9.443,
    "DiskUsageUtilization": 8.0
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "CPU": 9.522,
    "DiskUsageUtilization": 8.0
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "CPU": 9.998,
    "DiskUsageUtilization": 8.0
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
    "TimeStamp": "2025-09-28T01:36:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "InternetRX": null
  }
]
```

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:36:00Z",
    "InternetTX": null,
    "MemoryUtilization": 62.342
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "InternetTX": null,
    "MemoryUtilization": 62.34
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "InternetTX": null,
    "MemoryUtilization": 62.337
  }
]
```

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.640833333333333, p95=6.822, max=6.861
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:40:00Z",
    "CPU": 6.606
  },
  {
    "TimeStamp": "2025-09-28T01:45:00Z",
    "CPU": 6.553
  },
  {
    "TimeStamp": "2025-09-28T01:50:00Z",
    "CPU": 6.822
  }
]
```

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.557416666666667, p95=9.593, max=9.976
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:36:00Z",
    "IntranetOutRate": 170.331
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "IntranetOutRate": 175.548
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "IntranetOutRate": 260.79
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
    "TimeStamp": "2025-09-28T01:36:00Z",
    "InternetTX": null,
    "IntranetInRate": 1498.453
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "InternetTX": null,
    "IntranetInRate": 14096.384
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "InternetTX": null,
    "IntranetInRate": 1485.755
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
    "TimeStamp": "2025-09-28T01:36:00Z",
    "InternetTX": null,
    "DiskUsageUtilization": 42.79
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "InternetTX": null,
    "DiskUsageUtilization": 42.79
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "InternetTX": null,
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
    "TimeStamp": "2025-09-28T01:36:00Z",
    "InternetRX": null,
    "IntranetInRate": 2440.533,
    "DiskUsageUtilization": 7.62
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "InternetRX": null,
    "IntranetInRate": 982.084,
    "DiskUsageUtilization": 7.62
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "InternetRX": null,
    "IntranetInRate": 1034.922,
    "DiskUsageUtilization": 7.62
  }
]
```

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=31.039916666666667, p95=31.969, max=32.922
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T01:36:00Z",
    "DiskUsageUtilization": 61.89
  },
  {
    "TimeStamp": "2025-09-28T01:37:00Z",
    "DiskUsageUtilization": 61.89
  },
  {
    "TimeStamp": "2025-09-28T01:38:00Z",
    "DiskUsageUtilization": 61.89
  }
]
```
