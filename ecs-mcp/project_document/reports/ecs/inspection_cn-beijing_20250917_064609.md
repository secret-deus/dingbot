# ECS巡检报告

- 时间: 2025-09-17 06:46:09 UTC
- 地域: cn-beijing
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
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | 29.641 | 41.352 | 61.62 | cn-beijing-d | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | 9.355 | 61.677 | - | cn-beijing-d | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | - | 63.19 | - | cn-beijing-b | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | 10.033 | - | - | cn-beijing-h | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | 0.254 | - | - | cn-beijing-i | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | - | cn-beijing-h | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | - | - | - | cn-beijing-h | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | - | - | - | cn-beijing-d | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | - | - | - | cn-beijing-d | Running |

## 明细（采样）
### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.2397166666666667, p95=0.254, max=0.321
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T21:46:00Z",
    "CPU": 0.254,
    "InternetTX": null,
    "IntranetInRate": 2276.42,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:47:00Z",
    "CPU": 0.226,
    "InternetTX": null,
    "IntranetInRate": 2547.985,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "CPU": 0.254,
    "InternetTX": null,
    "IntranetInRate": 1214.19,
    "IOPSRead": null
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
    "TimeStamp": "2025-09-16T21:46:00Z",
    "InternetRX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:47:00Z",
    "InternetRX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "InternetRX": null,
    "IOPSRead": null
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
    "TimeStamp": "2025-09-16T21:46:00Z",
    "InternetRX": null,
    "IOPSWrite": 1.75
  },
  {
    "TimeStamp": "2025-09-16T21:47:00Z",
    "InternetRX": null,
    "IOPSWrite": 2.083
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "InternetRX": null,
    "IOPSWrite": 3.3
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
    "TimeStamp": "2025-09-16T21:47:00Z",
    "IOPSRead": null,
    "MemoryUtilization": 62.867
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "IOPSRead": null,
    "MemoryUtilization": 62.932
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "IOPSRead": 0.05,
    "MemoryUtilization": 62.967
  }
]
```

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.682033898305084, p95=9.355, max=9.618
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T21:47:00Z",
    "CPU": 9.355,
    "IntranetInRate": 4.731,
    "IntranetOutRate": 55.634,
    "IOPSWrite": 2.25,
    "MemoryUtilization": 61.565
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "CPU": 8.872,
    "IntranetInRate": 18.204,
    "IntranetOutRate": 67.067,
    "IOPSWrite": 1.883,
    "MemoryUtilization": 61.56
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "CPU": 8.982,
    "IntranetInRate": 7.111,
    "IntranetOutRate": 70.256,
    "IOPSWrite": 2.216,
    "MemoryUtilization": 61.56
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
    "TimeStamp": "2025-09-16T21:47:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 13151.709
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 8529.237
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 8644.061
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
    "TimeStamp": "2025-09-16T21:47:00Z",
    "InternetRX": null,
    "IntranetInRate": 3902.259,
    "IntranetOutRate": 76.39,
    "IOPSWrite": 8.75
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "InternetRX": null,
    "IntranetInRate": 5500.518,
    "IntranetOutRate": 81.89,
    "IOPSWrite": 5.683
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetRX": null,
    "IntranetInRate": 4012.032,
    "IntranetOutRate": 80.378,
    "IOPSWrite": 8.85
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
    "TimeStamp": "2025-09-16T21:47:00Z",
    "IntranetOutRate": 17773.226,
    "IOPSWrite": 10.416
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "IntranetOutRate": 16742.126,
    "IOPSWrite": 9.783
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "IntranetOutRate": 17302.596,
    "IOPSWrite": 10.233
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
    "TimeStamp": "2025-09-16T21:47:00Z",
    "InternetTX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "InternetTX": null,
    "IOPSRead": 0.016
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetTX": null,
    "IOPSRead": 0.033
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
    "TimeStamp": "2025-09-16T21:47:00Z",
    "InternetRX": null,
    "IntranetInRate": 1176.644,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "InternetRX": null,
    "IntranetInRate": 55770.18,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetRX": null,
    "IntranetInRate": 37034.393,
    "IOPSRead": null
  }
]
```

### i-2zef1jdvkslc2zj3f6zn (生产-极速筹-李丹-jisuchou.net备案用)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=9.639933333333333, p95=10.033, max=10.673
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T21:47:00Z",
    "CPU": 9.464,
    "IntranetOutRate": 8972.97
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "CPU": 9.544,
    "IntranetOutRate": 19006.259
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "CPU": 9.901,
    "IntranetOutRate": 37847.176
  }
]
```

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=29.226283333333335, p95=29.641, max=29.932
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T21:47:00Z",
    "CPU": 29.049,
    "IntranetInRate": 21.462,
    "IntranetOutRate": 67128.524,
    "MemoryUtilization": 41.352,
    "DiskUsageUtilization": 61.62
  },
  {
    "TimeStamp": "2025-09-16T21:48:00Z",
    "CPU": 29.104,
    "IntranetInRate": 32.404,
    "IntranetOutRate": 69541.478,
    "MemoryUtilization": 41.35,
    "DiskUsageUtilization": 61.62
  },
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "CPU": 29.038,
    "IntranetInRate": 28.111,
    "IntranetOutRate": 68223.931,
    "MemoryUtilization": 41.347,
    "DiskUsageUtilization": 61.62
  }
]
```
