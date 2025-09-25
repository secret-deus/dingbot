# ECS巡检报告

- 时间: 2025-09-17 06:41:05 UTC
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
| i-2zehftd4ce4iyiz8y6zt | 生产-平台支撑-Jira_Confluence_Crowd-001 | low | 29.741 | - | - | cn-beijing-d | Running |
| i-2zebcdgh4e5mzy7db1oo | 生产-大数据-data-trans-001 | low | 14.645 | - | - | cn-beijing-h | Running |
| i-2ze2i4qu555mj5vgvwa6 | 生产-大数据-Deepseek | low | 0.254 | - | - | cn-beijing-i | Running |
| i-2zeegsqhwtcdhku7dno1 | 生产-通用-轻松集团官网www.qingsonghealth.com | low | - | - | - | cn-beijing-h | Running |
| i-2zecc9f3sh2gux9giscv | 生产-crm-驰云代理服务器-01 | low | - | - | - | cn-beijing-a | Running |
| i-2zeharxemrb62feh6hse | 生产-健康-qingsonghealthcare网站 | low | - | - | - | cn-beijing-b | Running |
| i-2ze6m4f72i5kybo0q47n | 测试-平台支撑-freeipa-安全测试-临时 | low | - | - | - | cn-beijing-d | Running |
| i-2zehvvnevpjol5vkh6jv | 生产-平台支撑-freeipa-002 | low | - | - | - | cn-beijing-d | Running |
| i-2ze3f4w50nxduu4m7bl1 | 生产-平台支撑-freeipa-001 | low | - | - | - | cn-beijing-d | Running |
| i-2zed7senuu0ctl35xxqr | 生产-平台支撑-数据-01 | low | - | - | - | cn-beijing-c | Running |

## 明细（采样）
### i-2ze2i4qu555mj5vgvwa6 (生产-大数据-Deepseek)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.24326666666666666, p95=0.254, max=0.305
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T22:27:00Z",
    "CPU": 0.228
  },
  {
    "TimeStamp": "2025-09-16T22:28:00Z",
    "CPU": 0.252
  },
  {
    "TimeStamp": "2025-09-16T22:29:00Z",
    "CPU": 0.225
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
    "TimeStamp": "2025-09-16T22:27:00Z",
    "IntranetInRate": 19.24,
    "IntranetOutRate": 83.134
  },
  {
    "TimeStamp": "2025-09-16T22:28:00Z",
    "IntranetInRate": 85.099,
    "IntranetOutRate": 2419.933
  },
  {
    "TimeStamp": "2025-09-16T22:29:00Z",
    "IntranetInRate": 5.248,
    "IntranetOutRate": 64.296
  }
]
```

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
    "TimeStamp": "2025-09-16T22:27:00Z",
    "IntranetInRate": 9502.583
  },
  {
    "TimeStamp": "2025-09-16T22:28:00Z",
    "IntranetInRate": 2190.813
  },
  {
    "TimeStamp": "2025-09-16T22:29:00Z",
    "IntranetInRate": 2405.853
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
    "TimeStamp": "2025-09-16T22:27:00Z",
    "IntranetInRate": 18.758
  },
  {
    "TimeStamp": "2025-09-16T22:28:00Z",
    "IntranetInRate": 6.674
  },
  {
    "TimeStamp": "2025-09-16T22:29:00Z",
    "IntranetInRate": 6.085
  }
]
```

### i-2zebcdgh4e5mzy7db1oo (生产-大数据-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.5568, p95=14.645, max=14.88
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T22:27:00Z",
    "CPU": 14.622
  },
  {
    "TimeStamp": "2025-09-16T22:28:00Z",
    "CPU": 14.422
  },
  {
    "TimeStamp": "2025-09-16T22:29:00Z",
    "CPU": 14.572
  }
]
```

### i-2zehvvnevpjol5vkh6jv (生产-平台支撑-freeipa-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2ze3f4w50nxduu4m7bl1 (生产-平台支撑-freeipa-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zed7senuu0ctl35xxqr (生产-平台支撑-数据-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T22:28:00Z",
    "IntranetInRate": 1619.421,
    "IntranetOutRate": 138.812
  },
  {
    "TimeStamp": "2025-09-16T22:29:00Z",
    "IntranetInRate": 1770.837,
    "IntranetOutRate": 142.948
  },
  {
    "TimeStamp": "2025-09-16T22:30:00Z",
    "IntranetInRate": 1487.394,
    "IntranetOutRate": 125.769
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
    "TimeStamp": "2025-09-16T22:28:00Z",
    "IntranetInRate": 156.715
  },
  {
    "TimeStamp": "2025-09-16T22:29:00Z",
    "IntranetInRate": 6.924
  },
  {
    "TimeStamp": "2025-09-16T22:30:00Z",
    "IntranetInRate": 17.905
  }
]
```

### i-2zef1jdvkslc2zj3f6zn (生产-极速筹-李丹-jisuchou.net备案用)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2zehftd4ce4iyiz8y6zt (生产-平台支撑-Jira_Confluence_Crowd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=29.383066666666664, p95=29.741, max=29.932
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-16T22:28:00Z",
    "CPU": 29.053
  },
  {
    "TimeStamp": "2025-09-16T22:29:00Z",
    "CPU": 29.094
  },
  {
    "TimeStamp": "2025-09-16T22:30:00Z",
    "CPU": 29.467
  }
]
```
