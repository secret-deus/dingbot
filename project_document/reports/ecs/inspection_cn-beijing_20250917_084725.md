# ECS巡检报告

- 开始: 2025-09-17 08:47:25 UTC
- 结束: 2025-09-17 08:47:25 UTC
- 地域: ['cn-beijing']
- 实例数: 12
- 窗口: 1h
- 并发: 10
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 0
- 低风险: 12

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-2zef1jdvkslc2zj3f6zn | 生产-极速筹-李丹-jisuchou.net备案用 | low | - | 41.293 | - | cn-beijing-h | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | 2.0 | - | - | cn-beijing-h | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | - | - | - | cn-beijing-i | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | - | - | - | cn-beijing-b | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | - | - | - | cn-beijing-d | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | - | - | - | cn-beijing-h | Running |
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
    "TimeStamp": "2025-09-16T23:48:00Z",
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:49:00Z",
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:50:00Z",
    "IOPSRead": null
  }
]
```

### i-2zeegsqhwtcdhku7dno1 (生产-通用-轻松集团官网www.qingsonghealth.com)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.81185, p95=2.0, max=2.184
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:48:00Z",
    "CPU": 1.717,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-16T23:49:00Z",
    "CPU": 1.68,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-16T23:50:00Z",
    "CPU": 1.79,
    "InternetRX": null
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
    "TimeStamp": "2025-09-16T23:48:00Z",
    "InternetTX": null,
    "IntranetOutRate": 11355.34
  },
  {
    "TimeStamp": "2025-09-16T23:49:00Z",
    "InternetTX": null,
    "IntranetOutRate": 11360.938
  },
  {
    "TimeStamp": "2025-09-16T23:50:00Z",
    "InternetTX": null,
    "IntranetOutRate": 10704.213
  }
]
```

### i-2zeharxemrb62feh6hse (生产-健康-qingsonghealthcare网站)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2ze6m4f72i5kybo0q47n (测试-平台支撑-freeipa-安全测试-临时)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:48:00Z",
    "InternetRX": null,
    "IntranetInRate": 41.348,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:49:00Z",
    "InternetRX": null,
    "IntranetInRate": 28.768,
    "IOPSRead": null
  },
  {
    "TimeStamp": "2025-09-16T23:50:00Z",
    "InternetRX": null,
    "IntranetInRate": 28.026,
    "IOPSRead": null
  }
]
```

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zeevtwyz9h2ls5aka25 (生产-阳光链-后端-live节点-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T23:48:00Z",
    "InternetRX": null,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-16T23:49:00Z",
    "InternetRX": null,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-16T23:50:00Z",
    "InternetRX": null,
    "InternetTX": null
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
    "TimeStamp": "2025-09-16T23:49:00Z",
    "InternetRX": null,
    "IntranetInRate": 157.55,
    "IntranetOutRate": 13789.866,
    "IOPSWrite": 0.466,
    "MemoryUtilization": 41.157
  },
  {
    "TimeStamp": "2025-09-16T23:50:00Z",
    "InternetRX": null,
    "IntranetInRate": 19.033,
    "IntranetOutRate": 9998.882,
    "IOPSWrite": 0.433,
    "MemoryUtilization": 41.105
  },
  {
    "TimeStamp": "2025-09-16T23:51:00Z",
    "InternetRX": null,
    "IntranetInRate": 7.192,
    "IntranetOutRate": 8560.913,
    "IOPSWrite": 0.516,
    "MemoryUtilization": 41.112
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
    "TimeStamp": "2025-09-16T23:49:00Z",
    "IntranetOutRate": 66223.991,
    "IOPSWrite": 17.816
  },
  {
    "TimeStamp": "2025-09-16T23:50:00Z",
    "IntranetOutRate": 69760.614,
    "IOPSWrite": 17.383
  },
  {
    "TimeStamp": "2025-09-16T23:51:00Z",
    "IntranetOutRate": 66006.766,
    "IOPSWrite": 17.4
  }
]
```
