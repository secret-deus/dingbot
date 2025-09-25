# ECS巡检报告

- 开始: 2025-09-17 08:53:41 UTC
- 结束: 2025-09-17 08:53:41 UTC
- 地域: ['cn-beijing']
- 实例数: 12
- 窗口: 1h
- 并发: 20
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 0
- 低风险: 12

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-2zed7senuu0ctl35xxqr | 生产-平台支撑-数据-01 | low | - | 68.447 | - | cn-beijing-c | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | 7.523 | - | 36.17 | cn-beijing-d | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | 14.912 | - | - | cn-beijing-h | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | - | cn-beijing-h | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | - | - | - | cn-beijing-b | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | - | - | - | cn-beijing-d | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | - | - | - | cn-beijing-d | Running |
| i-2zeevtwyz9h2ls5aka25 | 生产-阳光链-后端-live节点-002 | low | - | - | - | cn-beijing-a | Running |

## 明细（采样）
### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:55:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-16T23:56:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-16T23:57:00Z",
    "InternetRX": null
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zecc9f3sh2gux9giscv (生产-crm-驰云代理服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:55:00Z",
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:56:00Z",
    "IOPSRead": 0.433
  },
  {
    "TimeStamp": "2025-09-16T23:57:00Z",
    "IOPSRead": null
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
    "TimeStamp": "2025-09-16T23:55:00Z",
    "IntranetOutRate": 13613.192
  },
  {
    "TimeStamp": "2025-09-16T23:56:00Z",
    "IntranetOutRate": 9172.309
  },
  {
    "TimeStamp": "2025-09-16T23:57:00Z",
    "IntranetOutRate": 7477.384
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.673833333333333, p95=14.912, max=15.935
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:55:00Z",
    "CPU": 14.506,
    "InternetRX": null,
    "IntranetOutRate": 8554.769,
    "IOPSWrite": 0.466
  },
  {
    "TimeStamp": "2025-09-16T23:56:00Z",
    "CPU": 14.478,
    "InternetRX": null,
    "IntranetOutRate": 9463.534,
    "IOPSWrite": 0.516
  },
  {
    "TimeStamp": "2025-09-16T23:57:00Z",
    "CPU": 14.642,
    "InternetRX": null,
    "IntranetOutRate": 12189.696,
    "IOPSWrite": 0.716
  }
]
```

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.816883333333333, p95=7.523, max=7.849
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:55:00Z",
    "CPU": 7.492,
    "IntranetOutRate": 204.124,
    "DiskUsageUtilization": 36.16
  },
  {
    "TimeStamp": "2025-09-16T23:56:00Z",
    "CPU": 7.285,
    "IntranetOutRate": 102.203,
    "DiskUsageUtilization": 36.16
  },
  {
    "TimeStamp": "2025-09-16T23:57:00Z",
    "CPU": 7.09,
    "IntranetOutRate": 143.884,
    "DiskUsageUtilization": 36.16
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
    "TimeStamp": "2025-09-16T23:55:00Z",
    "InternetTX": null,
    "MemoryUtilization": 68.442
  },
  {
    "TimeStamp": "2025-09-16T23:56:00Z",
    "InternetTX": null,
    "MemoryUtilization": 68.382
  },
  {
    "TimeStamp": "2025-09-16T23:57:00Z",
    "InternetTX": null,
    "MemoryUtilization": 68.425
  }
]
```

### i-2zeevtwyz9h2ls5aka25 (生产-阳光链-后端-live节点-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zef1jdvkslc2zj3f6zn (生产-极速筹-李丹-jisuchou.net备案用)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:55:00Z",
    "IOPSWrite": 17.1
  },
  {
    "TimeStamp": "2025-09-16T23:56:00Z",
    "IOPSWrite": 18.483
  },
  {
    "TimeStamp": "2025-09-16T23:57:00Z",
    "IOPSWrite": 16.783
  }
]
```
