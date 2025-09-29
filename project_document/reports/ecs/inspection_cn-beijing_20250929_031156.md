# ECS巡检报告

- 开始: 2025-09-29 03:11:56 UTC
- 结束: 2025-09-29 03:11:56 UTC
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
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | - | - | 61.91 | cn-beijing-d | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | - | 36.817 | - | cn-beijing-h | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | - | - | 36.47 | cn-beijing-d | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | 18.773 | - | - | cn-beijing-a | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | 14.431 | - | - | cn-beijing-h | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | 12.16 | - | - | cn-beijing-b | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | 8.531 | - | - | cn-beijing-d | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | 6.949 | - | - | cn-beijing-d | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | 6.72 | cn-beijing-h | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | 0.242 | - | - | cn-beijing-i | Running |

## 明细（采样）
### i-2ze6mjqj6m1bjp3uuhsi (生产-运维-公益基金会推广)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:13:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "InternetTX": null
  }
]
```

### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.23916666666666667, p95=0.242, max=0.246
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "CPU": 0.241
  },
  {
    "TimeStamp": "2025-09-28T18:20:00Z",
    "CPU": 0.238
  },
  {
    "TimeStamp": "2025-09-28T18:25:00Z",
    "CPU": 0.236
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
    "TimeStamp": "2025-09-28T18:13:00Z",
    "InternetTX": null,
    "DiskUsageUtilization": 6.72
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "InternetTX": null,
    "DiskUsageUtilization": 6.72
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "InternetTX": null,
    "DiskUsageUtilization": 6.72
  }
]
```

### i-2zecc9f3sh2gux9giscv (生产-crm-驰云代理服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=12.13725, p95=18.773, max=29.849
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "CPU": 9.303
  },
  {
    "TimeStamp": "2025-09-28T18:20:00Z",
    "CPU": 9.447
  },
  {
    "TimeStamp": "2025-09-28T18:25:00Z",
    "CPU": 9.106
  }
]
```

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=11.442266666666665, p95=12.16, max=12.763
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:13:00Z",
    "CPU": 12.763
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "CPU": 11.611
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "CPU": 11.186
  }
]
```

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.7731, p95=8.531, max=9.354
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:13:00Z",
    "CPU": 8.375,
    "IntranetOutRate": 56.746
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "CPU": 8.531,
    "IntranetOutRate": 71.551
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "CPU": 8.243,
    "IntranetOutRate": 60.848
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.11315, p95=14.431, max=16.222
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:13:00Z",
    "CPU": 13.956
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "CPU": 14.186
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "CPU": 14.081
  }
]
```

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.668716666666667, p95=6.949, max=7.195
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:13:00Z",
    "CPU": 6.716,
    "IntranetOutRate": 83.811
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "CPU": 6.31,
    "IntranetOutRate": 78.141
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "CPU": 6.409,
    "IntranetOutRate": 77.98
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
    "TimeStamp": "2025-09-28T18:13:00Z",
    "IntranetInRate": 34.225,
    "IntranetOutRate": 172.773,
    "DiskUsageUtilization": 36.47
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "IntranetInRate": 23.639,
    "IntranetOutRate": 123.226,
    "DiskUsageUtilization": 36.47
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "IntranetInRate": 45.101,
    "IntranetOutRate": 149.208,
    "DiskUsageUtilization": 36.47
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
    "TimeStamp": "2025-09-28T18:13:00Z",
    "IntranetInRate": 11.71
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "IntranetInRate": 12.076
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "IntranetInRate": 21.629
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
    "TimeStamp": "2025-09-28T18:13:00Z",
    "InternetRX": null,
    "IntranetInRate": 2985.028
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "InternetRX": null,
    "IntranetInRate": 1005.431
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "InternetRX": null,
    "IntranetInRate": 6224.964
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
    "TimeStamp": "2025-09-28T18:13:00Z",
    "InternetTX": null,
    "MemoryUtilization": 36.655
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "InternetTX": null,
    "MemoryUtilization": 36.65
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "InternetTX": null,
    "MemoryUtilization": 36.627
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
    "TimeStamp": "2025-09-28T18:13:00Z",
    "IntranetInRate": 24.435,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T18:14:00Z",
    "IntranetInRate": 35.561,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T18:15:00Z",
    "IntranetInRate": 40.81,
    "DiskUsageUtilization": 61.91
  }
]
```
