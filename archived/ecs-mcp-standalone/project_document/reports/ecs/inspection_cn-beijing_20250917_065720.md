# ECS巡检报告

- 开始: 1970-01-01 00:00:00 UTC
- 结束: 2025-09-17 06:57:20 UTC
- 地域: ['cn-beijing']
- 实例数: 12
- 窗口: 1h
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 2
- 低风险: 10

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-2zed7senuu0ctl35xxqr | 生产-平台支撑-数据-01 | medium | - | 68.77 | 89.0 | cn-beijing-c | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | medium | - | - | 87.43 | cn-beijing-d | Running |
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | - | 41.28 | - | cn-beijing-d | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | - | 41.262 | - | cn-beijing-h | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | 14.88 | - | - | cn-beijing-h | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | 2.036 | - | 6.68 | cn-beijing-h | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | 8.0 | cn-beijing-a | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | - | - | - | cn-beijing-b | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | - | - | - | cn-beijing-d | Running |

## 明细（采样）
### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T21:58:00Z",
    "InternetTX": null,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "InternetTX": null,
    "IOPSRead": null
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.8857666666666666, p95=2.036, max=2.242
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T21:58:00Z",
    "CPU": 1.867,
    "InternetTX": null,
    "IOPSWrite": 0.516,
    "DiskUsageUtilization": 6.68
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "CPU": 1.84,
    "InternetTX": null,
    "IOPSWrite": 0.583,
    "DiskUsageUtilization": 6.68
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "CPU": 1.941,
    "InternetTX": null,
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
    "TimeStamp": "2025-09-16T21:58:00Z",
    "InternetRX": null,
    "IntranetOutRate": 81.444,
    "DiskUsageUtilization": 8.0
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "InternetRX": null,
    "IntranetOutRate": 82.966,
    "DiskUsageUtilization": 8.0
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "InternetRX": null,
    "IntranetOutRate": 86.286,
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
    "TimeStamp": "2025-09-16T21:58:00Z",
    "InternetTX": null,
    "IntranetOutRate": 57226.308
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "InternetTX": null,
    "IntranetOutRate": 65441.655
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "InternetTX": null,
    "IntranetOutRate": 54853.768
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
    "TimeStamp": "2025-09-16T21:58:00Z",
    "InternetRX": null,
    "IntranetOutRate": 66.247,
    "IOPSRead": null,
    "DiskUsageUtilization": 87.43
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "InternetRX": null,
    "IntranetOutRate": 58.447,
    "IOPSRead": null,
    "DiskUsageUtilization": 87.43
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "InternetRX": null,
    "IntranetOutRate": 68.151,
    "IOPSRead": null,
    "DiskUsageUtilization": 87.43
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.642983333333332, p95=14.88, max=15.142
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T21:58:00Z",
    "CPU": 14.624,
    "IntranetOutRate": 8462.882
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "CPU": 14.582,
    "IntranetOutRate": 8509.03
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "CPU": 14.584,
    "IntranetOutRate": 8498.517
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
    "TimeStamp": "2025-09-16T21:58:00Z",
    "IntranetInRate": 27.765,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "IntranetInRate": 28.618,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "IntranetInRate": 40.63,
    "IOPSRead": null
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
    "TimeStamp": "2025-09-16T21:58:00Z",
    "InternetTX": null,
    "IntranetOutRate": 101.98
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "InternetTX": null,
    "IntranetOutRate": 131.673
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "InternetTX": null,
    "IntranetOutRate": 112.411
  }
]
```

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: medium | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': True}
- CPU: avg=None, p95=None, max=None
- 样例点:
```json
[
  {
    "TimeStamp": "2025-09-16T21:58:00Z",
    "IntranetInRate": 12.284,
    "MemoryUtilization": 68.77,
    "DiskUsageUtilization": 89.0
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "IntranetInRate": 10.393,
    "MemoryUtilization": 68.712,
    "DiskUsageUtilization": 89.0
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "IntranetInRate": 25.05,
    "MemoryUtilization": 68.682,
    "DiskUsageUtilization": 89.0
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
    "TimeStamp": "2025-09-16T21:58:00Z",
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T21:59:00Z",
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "IOPSRead": null
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
    "TimeStamp": "2025-09-16T21:59:00Z",
    "InternetTX": null,
    "IntranetInRate": 215.111,
    "MemoryUtilization": 41.167
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "InternetTX": null,
    "IntranetInRate": 58.928,
    "MemoryUtilization": 41.194
  },
  {
    "TimeStamp": "2025-09-16T22:01:00Z",
    "InternetTX": null,
    "IntranetInRate": 57.56,
    "MemoryUtilization": 41.192
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
    "TimeStamp": "2025-09-16T21:59:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IOPSRead": 1.3,
    "IOPSWrite": 18.183,
    "MemoryUtilization": 41.28
  },
  {
    "TimeStamp": "2025-09-16T22:00:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IOPSRead": 2.483,
    "IOPSWrite": 17.166,
    "MemoryUtilization": 41.269
  },
  {
    "TimeStamp": "2025-09-16T22:01:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IOPSRead": 4.65,
    "IOPSWrite": 20.216,
    "MemoryUtilization": 41.254
  }
]
```
