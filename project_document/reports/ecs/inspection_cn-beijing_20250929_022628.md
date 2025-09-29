# ECS巡检报告

- 开始: 2025-09-29 02:26:28 UTC
- 结束: 2025-09-29 02:26:28 UTC
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
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | 11.581 | 65.035 | - | cn-beijing-b | Running |
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | - | - | 61.91 | cn-beijing-d | Running |
| i-2zed7senuu0ctl35xxqr | 生产-平台支撑-数据-01 | low | 33.401 | - | - | cn-beijing-c | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | 9.96 | - | - | cn-beijing-a | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | 7.723 | - | - | cn-beijing-d | Running |
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | - | - | 7.61 | cn-beijing-h | Running |
| i-2ze6mjqj6m1bjp3uuhsi | 生产-运维-公益基金会推广 | low | - | - | - | cn-beijing-a | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | - | cn-beijing-h | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | - | - | - | cn-beijing-d | Running |

## 明细（采样）
### i-2ze6mjqj6m1bjp3uuhsi (生产-运维-公益基金会推广)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:27:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "InternetRX": null
  }
]
```

### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:27:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
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
    "TimeStamp": "2025-09-28T17:27:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "InternetTX": null
  }
]
```

### i-2zecc9f3sh2gux9giscv (生产-crm-驰云代理服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=9.331, p95=9.96, max=10.151
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:27:00Z",
    "CPU": 9.424
  },
  {
    "TimeStamp": "2025-09-28T17:28:00Z",
    "CPU": 10.044
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "CPU": 9.109
  }
]
```

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=11.423, p95=11.581, max=12.418
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:27:00Z",
    "InternetTX": null,
    "IntranetInRate": 709.973,
    "MemoryUtilization": 64.235
  },
  {
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetTX": null,
    "IntranetInRate": 1444.932,
    "MemoryUtilization": 64.224
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "InternetTX": null,
    "IntranetInRate": 2222.626,
    "MemoryUtilization": 64.275
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
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetTX": null,
    "IntranetOutRate": 11768.49
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "InternetTX": null,
    "IntranetOutRate": 9373.559
  },
  {
    "TimeStamp": "2025-09-28T17:30:00Z",
    "InternetTX": null,
    "IntranetOutRate": 11581.986
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.27475, p95=7.723, max=7.882
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T17:30:00Z",
    "CPU": 7.502,
    "InternetRX": null
  }
]
```

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=33.26675, p95=33.401, max=33.621
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetRX": null,
    "IntranetInRate": 97.527
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "InternetRX": null,
    "IntranetInRate": 11.498
  },
  {
    "TimeStamp": "2025-09-28T17:30:00Z",
    "CPU": 33.621,
    "InternetRX": null,
    "IntranetInRate": 21.962
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
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetRX": null,
    "IntranetInRate": 3275.707,
    "IntranetOutRate": 94.667
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "InternetRX": null,
    "IntranetInRate": 907.4,
    "IntranetOutRate": 67.798
  },
  {
    "TimeStamp": "2025-09-28T17:30:00Z",
    "InternetRX": null,
    "IntranetInRate": 925.832,
    "IntranetOutRate": 69.043
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
    "TimeStamp": "2025-09-28T17:28:00Z",
    "InternetTX": null,
    "IntranetInRate": 2450.09,
    "DiskUsageUtilization": 7.61
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "InternetTX": null,
    "IntranetInRate": 1010.346,
    "DiskUsageUtilization": 7.61
  },
  {
    "TimeStamp": "2025-09-28T17:30:00Z",
    "InternetTX": null,
    "IntranetInRate": 889.924,
    "DiskUsageUtilization": 7.61
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
    "TimeStamp": "2025-09-28T17:28:00Z",
    "IntranetInRate": 5045.179,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T17:29:00Z",
    "IntranetInRate": 4540.962,
    "DiskUsageUtilization": 61.91
  },
  {
    "TimeStamp": "2025-09-28T17:30:00Z",
    "IntranetInRate": 6685.354,
    "DiskUsageUtilization": 61.91
  }
]
```
