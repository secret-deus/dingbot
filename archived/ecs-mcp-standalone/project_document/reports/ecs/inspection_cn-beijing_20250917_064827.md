# ECS巡检报告

- 时间: 2025-09-17 06:48:27 UTC
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
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | - | 59.727 | - | cn-beijing-h | Running |
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | 29.641 | - | - | cn-beijing-d | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | - | - | 24.47 | cn-beijing-b | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | 2.036 | - | 6.68 | cn-beijing-h | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | 3.17 | - | cn-beijing-i | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | - | - | - | cn-beijing-d | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | - | - | - | cn-beijing-d | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | - | - | - | cn-beijing-d | Running |
| i-2zed7senuu0ctl35xxqr | 生产-平台支撑-数据-01 | low | - | - | - | cn-beijing-c | Running |

## 明细（采样）
### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "IntranetOutRate": 117.86,
    "IOPSWrite": 1.95,
    "MemoryUtilization": 3.15
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "IntranetOutRate": 121.094,
    "IOPSWrite": 1.716,
    "MemoryUtilization": 3.15
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "IntranetOutRate": 119.045,
    "IOPSWrite": 2.066,
    "MemoryUtilization": 3.15
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.88475, p95=2.036, max=2.242
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T21:49:00Z",
    "CPU": 1.997,
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 432.977,
    "IOPSWrite": 0.466,
    "DiskUsageUtilization": 6.68
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "CPU": 1.943,
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 444.049,
    "IOPSWrite": 0.6,
    "DiskUsageUtilization": 6.68
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "CPU": 1.898,
    "InternetRX": null,
    "InternetTX": null,
    "IntranetOutRate": 433.549,
    "IOPSWrite": 1.833,
    "DiskUsageUtilization": 6.68
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
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 856.2,
    "IOPSWrite": 2.016
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 926.788,
    "IOPSWrite": 1.666
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 3248.264,
    "IOPSWrite": 2.15
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
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetRX": null,
    "IntranetInRate": 243.297,
    "IOPSWrite": 1.216,
    "DiskUsageUtilization": 24.47
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "InternetRX": null,
    "IntranetInRate": 250.683,
    "IOPSWrite": 0.65,
    "DiskUsageUtilization": 24.47
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "InternetRX": null,
    "IntranetInRate": 294.679,
    "IOPSWrite": 2.216,
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
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetTX": null,
    "IntranetInRate": 970.888
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "InternetTX": null,
    "IntranetInRate": 956.006
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "InternetTX": null,
    "IntranetInRate": 2174.293
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
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetRX": null,
    "IntranetOutRate": 8644.061,
    "IOPSWrite": 0.483,
    "MemoryUtilization": 59.527
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "InternetRX": null,
    "IntranetOutRate": 8249.89,
    "IOPSWrite": 0.383,
    "MemoryUtilization": 59.58
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "InternetRX": null,
    "IntranetOutRate": 8731.306,
    "IOPSWrite": 2.0,
    "MemoryUtilization": 59.722
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
    "TimeStamp": "2025-09-16T21:49:00Z",
    "IntranetInRate": 29.385
  },
  {
    "TimeStamp": "2025-09-16T21:52:00Z",
    "IntranetInRate": 28.696
  },
  {
    "TimeStamp": "2025-09-16T21:53:00Z",
    "IntranetInRate": 55.444
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
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetRX": null,
    "IntranetInRate": 3795.217,
    "IOPSWrite": 10.233
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "InternetRX": null,
    "IntranetInRate": 2892.731,
    "IOPSWrite": 7.933
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "InternetRX": null,
    "IntranetInRate": 4615.782,
    "IOPSWrite": 11.383
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
    "TimeStamp": "2025-09-16T21:49:00Z",
    "InternetTX": null,
    "IOPSRead": 0.033
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "InternetTX": null,
    "IOPSRead": 0.283
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "InternetTX": null,
    "IOPSRead": 0.583
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
    "TimeStamp": "2025-09-16T21:49:00Z",
    "IOPSWrite": 0.783
  },
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "IOPSWrite": 0.633
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "IOPSWrite": 0.533
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
    "TimeStamp": "2025-09-16T21:50:00Z",
    "InternetTX": null,
    "IntranetOutRate": 24600.576,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "InternetTX": null,
    "IntranetOutRate": 27459.31,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:52:00Z",
    "InternetTX": null,
    "IntranetOutRate": 22560.221,
    "IOPSRead": null
  }
]
```

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=29.23323333333333, p95=29.641, max=29.932
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T21:50:00Z",
    "CPU": 29.217,
    "IntranetInRate": 4790.818
  },
  {
    "TimeStamp": "2025-09-16T21:51:00Z",
    "CPU": 29.161,
    "IntranetInRate": 4576.46
  },
  {
    "TimeStamp": "2025-09-16T21:52:00Z",
    "CPU": 28.987,
    "IntranetInRate": 2700.492
  }
]
```
