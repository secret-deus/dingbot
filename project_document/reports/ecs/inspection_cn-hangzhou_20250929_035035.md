# ECS巡检报告

- 开始: 2025-09-29 03:50:35 UTC
- 结束: 2025-09-29 03:50:35 UTC
- 地域: ['cn-hangzhou']
- 实例数: 200
- 窗口: 1h
- 并发: 5
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 1
- 低风险: 199

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-bp1fva2t19bzbcabko7g | 生产-微爱-app-01 | medium | 80.383 | - | - | cn-hangzhou-k | Running |
| i-bp13onik0hd4uniz751o | 测试-通用-acknode-004 | low | - | 71.869 | - | cn-hangzhou-b | Running |
| i-bp10zf1gy4t2exf5vlyl | 生产-大数据-大语言模型训练-空碗-gpu-003 | low | 8.986 | 50.917 | - | cn-hangzhou-j | Running |
| i-bp1izvhfvbrel4k1piw6 | 生产-crm-驰云中心服务器-05 | low | 22.18 | - | 37.0 | cn-hangzhou-h | Running |
| i-bp15aa8vfgb6ik00g1ds | 生产-crm-莫莫目标追踪-001 | low | - | 53.14 | - | cn-hangzhou-k | Running |
| i-bp1djud42juqjc2perbi | 生产-通用-ack-node-035 | low | - | 50.377 | - | cn-hangzhou-b | Running |
| i-bp1b7lg8l7hk8b9peor6 | 预生产-大数据-k8s-node | low | - | 49.042 | - | cn-hangzhou-b | Running |
| i-bp1fcql6prdzzzhpfq6s | 生产-通用-ack-node-054 | low | 5.064 | 42.352 | - | cn-hangzhou-b | Running |
| i-bp1ik7t5d5f2n4hvc1m8 | 生产-通用-ack-node-024 | low | - | 48.38 | - | cn-hangzhou-g | Running |
| i-bp10na7saw1vy2we9ri9 | 生产-通用-ack-node-037 | low | 2.156 | 43.462 | - | cn-hangzhou-g | Running |

## 明细（采样）
### i-bp1ezxzd5ptskbk7kjac (生产-CRM-星语平台-010)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.469, p95=1.999, max=2.218
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 1.421,
    "IntranetOutRate": 1195.331
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 1904.247
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 1938.784
  }
]
```

### i-bp1ezxzd5ptskbk7kjab (生产-CRM-星语平台-009)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "IntranetOutRate": 268257.416
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 23403.997
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 27922.022
  }
]
```

### i-bp1ezxzd5ptskbk7kjaa (生产-CRM-星语平台-008)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.005083333333333333, p95=0.005, max=0.006
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 0.005
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 0.005
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 0.005
  }
]
```

### i-bp1ezxzd5ptskbk7kja9 (生产-CRM-星语平台-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.005316666666666667, p95=0.007, max=0.008
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 0.004
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "CPU": 0.006
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 0.005
  }
]
```

### i-bp1ezxzd5ptskbk7kja8 (生产-CRM-星语平台-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "IntranetInRate": 34.438,
    "DiskUsageUtilization": 20.93
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetInRate": 48.445,
    "DiskUsageUtilization": 20.93
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 34.471,
    "DiskUsageUtilization": 20.93
  }
]
```

### i-bp1hq844oy11b3u9jnwj (生产-CRM-星语平台-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1j4jvdujrtenkmndyt (生产-crm-驰云中心服务器-安卓)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.0104833333333334, p95=1.121, max=1.178
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 0.912
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "CPU": 1.078
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 0.921
  }
]
```

### i-bp13yabzr5882mivlycf (生产-微爱-区块链-单点临时使用-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.9660166666666666, p95=1.905, max=2.606
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 1.365
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "CPU": 1.27
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 1.283
  }
]
```

### i-bp1hh4jmc5lq815psq6v (生产-微爱-区块链-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "InternetTX": null,
    "IntranetInRate": 31841.757
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null,
    "IntranetInRate": 31647.88
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "IntranetInRate": 31917.26
  }
]
```

### i-bp1hh4jmc5lq815psq6x (生产-微爱-区块链-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hh4jmc5lq815psq6w (生产-微爱-区块链-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.16783333333333336, p95=0.172, max=0.177
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 0.163
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 0.165
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 0.163
  }
]
```

### i-bp1i4ilhgbgmh0ad7tkr (测试-前端-coze-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "InternetTX": null,
    "IntranetInRate": 240.844
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null,
    "IntranetInRate": 204.117
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "IntranetInRate": 204.936
  }
]
```

### i-bp14hd0h696itgph7q01 (生产-通用-ack-node-072)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetRX": null
  }
]
```

### i-bp1g5sg40chcucujygtm (测试-大数据-大语言模型训练-gpu-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null
  }
]
```

### i-bp1f901c0xvcrh03yhnv (测试-通用-acknode-016)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "InternetRX": null,
    "IntranetOutRate": 10911.01
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetRX": null,
    "IntranetOutRate": 11116.122
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetRX": null,
    "IntranetOutRate": 11089.546
  }
]
```

### i-bp148a784artf4abq4ri (测试-运维-ling-测试)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.05111666666666667, p95=0.066, max=0.208
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 0.033
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "CPU": 0.05
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 0.048
  }
]
```

### i-bp13gg740rm1l6zo1mzb (测试-微爱-区块链-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null
  }
]
```

### i-bp1b99get09sbi96bt7h (生产-通用-ack-node-071)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null
  }
]
```

### i-bp12e97wltuwwvjfo75w (测试-平台支撑-容器镜像)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "DiskUsageUtilization": 2.9
  }
]
```

### i-bp17z7z7r9qjhdm5lww4 (测试-通用-acknode-015)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "IntranetOutRate": 3647.202
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 3590.108
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 3590.411
  }
]
```

### i-bp16bk59nfr78kelqpcd (生产-通用-ack-node-070)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1egki2k7iulh3w0sa8 (生产-通用-ack-node-069)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.85775, p95=2.961, max=2.995
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 2.758,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetRX": null
  }
]
```

### i-bp1f5rx2dmkfquo3n7fz (生产-通用-skywalking-banyandb-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=9.546750000000001, p95=13.431, max=19.202
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "CPU": 8.454,
    "InternetRX": null,
    "IntranetOutRate": 2070.391
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetRX": null,
    "IntranetOutRate": 2281.959
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetRX": null,
    "IntranetOutRate": 65740.391
  }
]
```

### i-bp1f5rx2dmkfquo3n7fy (生产-通用-skywalking-banyandb-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:45:00Z",
    "InternetTX": null,
    "IntranetInRate": 6194174.634
  },
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null,
    "IntranetInRate": 7862832.059
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "IntranetInRate": 7178445.482
  }
]
```

### i-bp1f5rx2dmkfquo3n7fx (生产-通用-skywalking-banyandb-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14yffwp9oi1pcwr7uo (生产-通用-skywalking-oap-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null
  }
]
```

### i-bp15aa8vfgb6ik00g1ds (生产-crm-莫莫目标追踪-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 28293.666,
    "MemoryUtilization": 53.13
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 28131.191,
    "MemoryUtilization": 53.13
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 28636.501,
    "MemoryUtilization": 53.13
  }
]
```

### i-bp1flrwaw8ocd6swyf6d (测试-大数据-智能记忆体-neo4j图数据库)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.306, p95=2.455, max=2.481
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 2.121
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 2.416
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 2.397
  }
]
```

### i-bp11mw62lucculpmx75o (生产-大数据-智能记忆体-neo4j图数据库)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null,
    "IntranetInRate": 1107.831
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "IntranetInRate": 1208.046
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null,
    "IntranetInRate": 2686.976
  }
]
```

### i-bp1cx13y2y278hhs8awz (测试-crm-莫莫目标追踪-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.45208333333333334, p95=0.462, max=0.466
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "DiskUsageUtilization": 3.22
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "DiskUsageUtilization": 3.22
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "DiskUsageUtilization": 3.22
  }
]
```

### i-bp1azlu246g6s2je0kdr (生产-通用-ack-node-068)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.9160833333333334, p95=3.969, max=3.97
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null,
    "IntranetOutRate": 631721.983
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "IntranetOutRate": 666804.497
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null,
    "IntranetOutRate": 656109.431
  }
]
```

### i-bp1ccl6gkupuuk8z5pfr (生产-通用-ack-node-067)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null,
    "IntranetInRate": 6284905.403
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "IntranetInRate": 7890215.731
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null,
    "IntranetInRate": 7374170.112
  }
]
```

### i-bp1b35itfkfk8w3337jo (生产-CRM-OCR-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 316.35,
    "DiskUsageUtilization": 3.22
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 304.289,
    "DiskUsageUtilization": 3.22
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 296.187,
    "DiskUsageUtilization": 3.22
  }
]
```

### i-bp1fdju07s1hgeojnnms (生产-CRM-OCR-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=5.840916666666667, p95=11.607, max=14.67
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "CPU": 6.575,
    "IntranetOutRate": 324.441,
    "DiskUsageUtilization": 5.4
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 6.196,
    "IntranetOutRate": 358.466,
    "DiskUsageUtilization": 5.4
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 3.904,
    "IntranetOutRate": 249.83,
    "DiskUsageUtilization": 5.4
  }
]
```

### i-bp17q4dvhdsw23r7dwuf (生产-大数据-莫莫猫脸识别-gpu-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetInRate": 4612901.683
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 4908015.752
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 4531619.703
  }
]
```

### i-bp1hhoi63e4fa64hpujv (生产-通用-ack-node-68)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetInRate": 3215649.45
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 14024268.322
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 2676046.37
  }
]
```

### i-bp17vnk03hf08ownu5x9 (生产-crm-实时字幕烧录-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 543379.046
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 703591.901
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 263692.424
  }
]
```

### i-bp17vnk03hf08ownu5x7 (生产-crm-实时字幕烧录-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.07108333333333333, p95=0.072, max=0.072
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 26780.057
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 26238.839
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 27197.713
  }
]
```

### i-bp17vnk03hf08ownu5x8 (生产-crm-实时字幕烧录-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.14391666666666666, p95=0.15, max=0.153
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetInRate": 177.496
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 69.338
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 139.201
  }
]
```

### i-bp176liqfunsfoaogvol (生产-通用-ack-node-67)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetInRate": 1807451.067,
    "DiskUsageUtilization": 19.51
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 1544963.003,
    "DiskUsageUtilization": 19.51
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 1660593.493,
    "DiskUsageUtilization": 19.51
  }
]
```

### i-bp177xyvox3vsfpuieys (生产-大数据-日志拉取)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.939333333333334, p95=7.357, max=7.479
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "CPU": 6.761
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 6.614
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 7.099
  }
]
```

### i-bp1h1gu3djkpocvjlu57 (生产-医疗-文件上传-temp)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "InternetTX": null,
    "MemoryUtilization": 5.02
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "MemoryUtilization": 5.02
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null,
    "MemoryUtilization": 5.02
  }
]
```

### i-bp1dnu601niybx0adgc9 (测试-莫莫-freeswitch-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.7613220338983051, p95=0.824, max=0.877
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "CPU": 0.788,
    "IntranetOutRate": 8570.47
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 0.737,
    "IntranetOutRate": 14144.17
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 0.795,
    "IntranetOutRate": 8513.945
  }
]
```

### i-bp11vwnue2zdyizyo8lu (生产-CRM-星语平台-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.0065, p95=0.007, max=0.007
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "DiskUsageUtilization": 20.76
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "DiskUsageUtilization": 20.76
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "DiskUsageUtilization": 20.76
  }
]
```

### i-bp1jdb6m212e4z5kuxy9 (预生产-通用-k8s-new-node-014)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.29924999999999996, p95=0.304, max=0.31
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 0.297
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 0.301
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 0.293
  }
]
```

### i-bp10zrbl0kd6wm2p0m9o (生产-CRM-星语平台-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "DiskUsageUtilization": 23.38
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "DiskUsageUtilization": 23.38
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "DiskUsageUtilization": 23.38
  }
]
```

### i-bp1cg7vw5j4bz3jr4jt7 (测试-通用-acknode-014)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetInRate": 56249.342,
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 57407.325,
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 57642.066,
    "DiskUsageUtilization": 2.9
  }
]
```

### i-bp16r9cxhil8iz0zt1kb (生产-通用-ack-node-065)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.3545, p95=2.553, max=2.657
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 5649.376
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 5929.182
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 5363.146
  }
]
```

### i-bp16r9cxhil8iz0zt1ka (生产-通用-ack-node-064)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.640133333333333, p95=10.689, max=14.227
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "CPU": 8.055,
    "IntranetOutRate": 59696.9
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 8.832,
    "IntranetOutRate": 72514.564
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 7.932,
    "IntranetOutRate": 56926.117
  }
]
```

### i-bp193mwb7ny9ljqpsfmp (生产-通用-ack-node-066)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 541862.161
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 638618.146
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 945417.966
  }
]
```

### i-bp19k0qor1uls8csx3vz (生产-通用-ack-node-063)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "DiskUsageUtilization": 2.9
  }
]
```

### i-bp15bby7o91rhgk2rbe6 (生产-通用-ack-node-062)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:46:00Z",
    "IntranetOutRate": 637421.065
  },
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 700185.623
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 479751.171
  }
]
```

### i-bp1gx2gg0t4i869ac6ie (生产-通用-ack-node-061)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1d9ctjyrk5obldp6vb (测试-莫莫-freeswitch-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.232083333333334, p95=9.224, max=10.309
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 7.797
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 9.224
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 8.963
  }
]
```

### i-bp159h0vv1vwvpsljji5 (生产-大数据-langfuse-平台)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.0230166666666665, p95=3.255, max=3.312
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 3.119
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 3.14
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 3.163
  }
]
```

### i-bp1bdcc19wenz2p0dnaf (生产-通用-ack-node-060)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=4.727616666666666, p95=4.839, max=5.044
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 4.715,
    "IntranetInRate": 12679.641
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 4.698,
    "IntranetInRate": 11800.48
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 4.708,
    "IntranetInRate": 12112.364
  }
]
```

### i-bp1ivu3yaedtzh73s9pc (生产-CRM-星语平台-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.03891666666666667, p95=0.041, max=0.042
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 0.038,
    "IntranetInRate": 36.573
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 0.041,
    "IntranetInRate": 35.592
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 0.039,
    "IntranetInRate": 46.361
  }
]
```

### i-bp1fqfje3gwdtbcikjzd (生产-大数据-外采)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.4673333333333334, p95=1.488, max=1.491
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "MemoryUtilization": 12.175
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "MemoryUtilization": 12.175
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "MemoryUtilization": 12.18
  }
]
```

### i-bp16ocsr2n0jh5fv3gza (生产-医疗-文件上传-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.299499999999999, p95=6.346, max=6.435
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 6.346
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 6.268
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 6.256
  }
]
```

### i-bp1h6tv5kezs83ofzyb7 (生产-crm-zy-企微会话存档-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null
  }
]
```

### i-bp1b53i1ykx67i4ugy7e (生产-crm-zy-企微会话存档-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.0464166666666666, p95=2.066, max=2.074
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 12840.686,
    "DiskUsageUtilization": 1.05
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 15156.155,
    "DiskUsageUtilization": 1.05
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetInRate": 13634.491,
    "DiskUsageUtilization": 1.05
  }
]
```

### i-bp16i1531i6nlqj15h2x (生产-crm-驰云中心服务器-07)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "IntranetOutRate": 160097.484
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null,
    "IntranetOutRate": 162601.233
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null,
    "IntranetOutRate": 163960.695
  }
]
```

### i-bp16i1531i6nlqj15h2y (生产-crm-驰云中心服务器-06)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 111.466
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 7.38
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetInRate": 7.808
  }
]
```

### i-bp18ri3uy5ulu0ivx9o2 (生产-微爱-go_mp_client-vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "MemoryUtilization": 17.582
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "MemoryUtilization": 17.56
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "MemoryUtilization": 17.535
  }
]
```

### i-bp18ri3uy5ulu0ivx9o1 (生产-微爱-go_mp_client-vpc-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.9085, p95=1.943, max=1.951
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.864
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 1.855
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 1.886
  }
]
```

### i-bp17ycfcea3ibii4kq48 (生产-微爱-go_project_index-vpc-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 1678.031,
    "DiskUsageUtilization": 9.97
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 1582.247,
    "DiskUsageUtilization": 9.97
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetInRate": 2491.154,
    "DiskUsageUtilization": 9.97
  }
]
```

### i-bp17ycfcea3ibii4kq47 (生产-微爱-go_project_index-vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=4.301166666666666, p95=4.404, max=4.571
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 4.324
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 4.404
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 4.109
  }
]
```

### i-bp10wfdq4eqtbgw1jksc (生产-微爱-go_partner_ygl-vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetTX": null,
    "IntranetInRate": 25875.251,
    "DiskUsageUtilization": 9.57
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null,
    "IntranetInRate": 25456.366,
    "DiskUsageUtilization": 9.57
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null,
    "IntranetInRate": 27375.752,
    "DiskUsageUtilization": 9.57
  }
]
```

### i-bp10wfdq4eqtbgw1jksa (生产-微爱-go_partner-vpc-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10wfdq4eqtbgw1jksb (生产-微爱-go_partner-vpc-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetRX": null,
    "MemoryUtilization": 23.755
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetRX": null,
    "MemoryUtilization": 22.727
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null,
    "MemoryUtilization": 22.507
  }
]
```

### i-bp10wfdq4eqtbgw1jks9 (生产-微爱-go_partner-vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null
  }
]
```

### i-bp1bnyi3nd6yxl32eoxx (生产-通用-ack-node-059)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetOutRate": 3814712.661,
    "MemoryUtilization": 36.027
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 3643824.81,
    "MemoryUtilization": 36.015
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 3731525.768,
    "MemoryUtilization": 36.017
  }
]
```

### i-bp19wzhktmfgn1586a4d (生产-通用-ack-node-058)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.12, p95=7.156, max=7.162
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 7.12
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 7.156
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 7.087
  }
]
```

### i-bp19wzhktmfgn1586a4f (生产-通用-ack-node-057)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.9267, p95=3.093, max=3.108
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 2.796,
    "IntranetInRate": 395747.464,
    "DiskUsageUtilization": 20.41
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 3.093,
    "IntranetInRate": 463900.945,
    "DiskUsageUtilization": 20.41
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 2.83,
    "IntranetInRate": 425741.653,
    "DiskUsageUtilization": 20.41
  }
]
```

### i-bp19wzhktmfgn1586a4e (生产-通用-ack-node-056)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "IntranetInRate": 837498.88,
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 873186.235,
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetInRate": 911724.544,
    "DiskUsageUtilization": 2.9
  }
]
```

### i-bp19wzhktmfgn1586a4c (生产-通用-ack-node-055)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "MemoryUtilization": 40.265
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "MemoryUtilization": 40.23
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "MemoryUtilization": 40.227
  }
]
```

### i-bp1fcql6prdzzzhpfq6s (生产-通用-ack-node-054)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.7083333333333335, p95=5.064, max=6.855
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 1.856,
    "MemoryUtilization": 38.89
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 1.65,
    "MemoryUtilization": 38.89
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 2.058,
    "MemoryUtilization": 38.882
  }
]
```

### i-bp1fcql6prdzzzhpfq6p (生产-通用-ack-node-053)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fcql6prdzzzhpfq6q (生产-通用-ack-node-052)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.6576333333333333, p95=1.767, max=1.864
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:47:00Z",
    "CPU": 1.591,
    "IntranetInRate": 1454961.322
  },
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 1.564,
    "IntranetInRate": 1556784.605
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 1.589,
    "IntranetInRate": 1555801.565
  }
]
```

### i-bp1fcql6prdzzzhpfq6r (生产-通用-ack-node-051)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.3499166666666667, p95=2.411, max=2.428
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 2.397
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 2.404
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 2.231
  }
]
```

### i-bp108xg7jezya6tjm7ij (生产-通用-ack-node-050)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null
  }
]
```

### i-bp108xg7jezya6tjm7ih (生产-通用-ack-node-049)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp108xg7jezya6tjm7if (生产-通用-ack-node-048)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp108xg7jezya6tjm7ii (生产-通用-ack-node-047)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.639283333333333, p95=4.027, max=5.028
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 2.268,
    "DiskUsageUtilization": 25.85
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 2.386,
    "DiskUsageUtilization": 25.85
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 2.147,
    "DiskUsageUtilization": 25.85
  }
]
```

### i-bp108xg7jezya6tjm7ig (生产-通用-ack-node-046)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14b7jx33vieqjcs6x4 (生产-微爱-go_api_gateway_vpc-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 151255.449
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 177998.37
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetOutRate": 168814.182
  }
]
```

### i-bp14b7jx33vieqjcs6x5 (生产-微爱-go_api_gateway_vpc-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.14335, p95=1.222, max=1.251
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 1.079
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 1.127
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.055
  }
]
```

### i-bp14b7jx33vieqjcs6x2 (生产-微爱-go_api_gateway_vpc-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null
  }
]
```

### i-bp14b7jx33vieqjcs6x6 (生产-微爱-go_api_gateway_vpc-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.984, p95=2.225, max=2.252
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 136155.682
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 307085.721
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.876,
    "IntranetOutRate": 356260.795
  }
]
```

### i-bp14b7jx33vieqjcs6x3 (生产-微爱-go_api_gateway_vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.4190166666666668, p95=1.739, max=1.979
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 1.183
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 1.37
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.692
  }
]
```

### i-bp19cvw9lyh82l7t5kwv (生产-微爱-go_partner-vpc-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=5.405833333333334, p95=5.718, max=5.763
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 643786.205
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 63707.545
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 5.631,
    "IntranetOutRate": 57863.099
  }
]
```

### i-bp19cvw9lyh82l7t5kwx (生产-微爱-go_partner-vpc-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.733999999999999, p95=7.124, max=7.273
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 51131.187,
    "DiskUsageUtilization": 11.53
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 667746.85,
    "DiskUsageUtilization": 11.54
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 6.464,
    "IntranetOutRate": 56693.828,
    "DiskUsageUtilization": 11.547
  }
]
```

### i-bp19cvw9lyh82l7t5kww (生产-微爱-go_partner-vpc-008)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.186000000000001, p95=7.916, max=8.703
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 5.594,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 6.366,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 6.358,
    "InternetRX": null
  }
]
```

### i-bp19cvw9lyh82l7t5kwu (生产-微爱-go_partner-vpc-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null
  }
]
```

### i-bp19cvw9lyh82l7t5kwt (生产-微爱-go_partner-vpc-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetRX": null,
    "MemoryUtilization": 24.18
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null,
    "MemoryUtilization": 24.117
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null,
    "MemoryUtilization": 24.175
  }
]
```

### i-bp16q0s3g4c9cjihw9jr (生产-通用-ack-大数据文章查重-node-045)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.931, p95=0.967, max=1.218
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 0.967,
    "InternetRX": null
  }
]
```

### i-bp16q0s3g4c9cjihw9jq (生产-通用-ack-大数据文章查重-node-044)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetInRate": 107020.97
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetInRate": 101138.978
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetInRate": 99835.767
  }
]
```

### i-bp1f08qxsdf6uee8oz59 (生产-通用-ack-大数据文章查重-node-043)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 82891.844
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 80534.459
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetOutRate": 81241.565
  }
]
```

### i-bp1f08qxsdf6uee8oz5a (生产-通用-ack-大数据文章查重-node-042)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 83107.976,
    "DiskUsageUtilization": 12.73
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 72917.811,
    "DiskUsageUtilization": 12.73
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetOutRate": 82997.794,
    "DiskUsageUtilization": 12.73
  }
]
```

### i-bp1f08qxsdf6uee8oz58 (生产-通用-ack-大数据文章生成-node-041)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null
  }
]
```

### i-bp1f08qxsdf6uee8oz57 (生产-通用-ack-大数据文章生成-node-040)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 567.828
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 556.987
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetOutRate": 579.335
  }
]
```

### i-bp1f08qxsdf6uee8oz56 (生产-通用-ack-node-039)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10na7saw1vy2we9rib (生产-通用-ack-node-038)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.789283333333334, p95=7.201, max=7.247
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 6.979
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 6.553
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 6.909
  }
]
```

### i-bp10na7saw1vy2we9ri9 (生产-通用-ack-node-037)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.7614166666666666, p95=2.156, max=2.535
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "MemoryUtilization": 43.375
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "MemoryUtilization": 43.39
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.658,
    "MemoryUtilization": 43.382
  }
]
```

### i-bp10na7saw1vy2we9ria (生产-通用-ack-node-036)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.5376440677966103, p95=2.592, max=2.594
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "CPU": 2.497,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 2.531,
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 2.523,
    "InternetRX": null
  }
]
```

### i-bp1djud42juqjc2perbi (生产-通用-ack-node-035)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "MemoryUtilization": 50.319
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "MemoryUtilization": 50.325
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "MemoryUtilization": 50.349
  }
]
```

### i-bp1djud42juqjc2perbh (生产-通用-ack-node-034)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:48:00Z",
    "IntranetOutRate": 435591.577,
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 466942.498,
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetOutRate": 459664.042,
    "DiskUsageUtilization": 2.9
  }
]
```

### i-bp1djud42juqjc2perbg (生产-通用-ack-node-033)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.3798333333333332, p95=1.389, max=1.4
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.375,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null
  }
]
```

### i-bp14y1mtx36q1twgu20c (生产-通用-ack-node-032)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetRX": null
  }
]
```

### i-bp14y1mtx36q1twgu20d (生产-通用-ack-node-031)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 361358.404
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetOutRate": 339183.616
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetOutRate": 819458.73
  }
]
```

### i-bp176ar7xqoj0ckd7f9r (生产-shangyitech-nginx-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 9296.964
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 7390.003
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetRX": null,
    "InternetTX": null,
    "IntranetInRate": 7587.157
  }
]
```

### i-bp1iomyvtcf7wsgffeet (生产-momo-nginx-out-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.9459333333333333, p95=2.012, max=2.182
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 1.929
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.92
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 1.95
  }
]
```

### i-bp1iomyvtcf7wsgffees (生产-momo-nginx-out-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 22459.187
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetOutRate": 83351.278
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetOutRate": 22622.208
  }
]
```

### i-bp14efp0nz1vcue5tq1k (生产-momo-etcd-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.0134999999999998, p95=1.028, max=1.042
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetInRate": 93573.802,
    "DiskUsageUtilization": 0.73
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.014,
    "IntranetInRate": 91306.666,
    "DiskUsageUtilization": 0.73
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetInRate": 91618.918,
    "DiskUsageUtilization": 0.73
  }
]
```

### i-bp14efp0nz1vcue5tq1m (生产-momo-etcd-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14efp0nz1vcue5tq1l (生产-momo-etcd-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.736542372881356, p95=1.841, max=17.209
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 1.769,
    "MemoryUtilization": 15.997
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.648,
    "MemoryUtilization": 15.99
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 1.602,
    "MemoryUtilization": 15.996
  }
]
```

### i-bp1en8fg3gh26uyuxo7x (生产-微爱-公益基金会个筹-app-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null
  }
]
```

### i-bp102e6660kwur07m9lj (生产-微爱-php服务-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.0055, p95=1.108, max=1.145
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 0.941,
    "IntranetInRate": 2662.4
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 0.978,
    "IntranetInRate": 1111.927
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 1.135,
    "IntranetInRate": 23357.576
  }
]
```

### i-bp102e6660kwur07m9li (生产-微爱-php服务-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.71605, p95=0.776, max=0.828
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 0.756,
    "IntranetOutRate": 8017.783
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 0.668,
    "IntranetOutRate": 8388.198
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 0.749,
    "IntranetOutRate": 8002.628
  }
]
```

### i-bp1fva2t19bzbcabko7h (生产-微爱-app-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 2191126.254
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetOutRate": 3576441.924
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetOutRate": 2734274.423
  }
]
```

### i-bp1fva2t19bzbcabko7g (生产-微爱-app-01)
- 风险: medium | 标记: {'cpu_p95_high': True, 'memory_high': False, 'disk_high': False}
- CPU: avg=79.54375, p95=80.383, max=80.765
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 80.037,
    "IntranetInRate": 11259.188
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 79.117,
    "IntranetInRate": 25880.88
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 78.906,
    "IntranetInRate": 22294.018
  }
]
```

### i-bp1fva2t19bzbcabko7f (生产-微爱-单节点服务)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null
  }
]
```

### i-bp1izvhfvbrel4k1piw6 (生产-crm-驰云中心服务器-05)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=18.941916666666668, p95=22.18, max=24.839
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "DiskUsageUtilization": 37.0
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 17.247,
    "DiskUsageUtilization": 37.0
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "DiskUsageUtilization": 37.0
  }
]
```

### i-bp1jfuozuwikduledeox (生产-医疗-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null,
    "IntranetInRate": 3275.707
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null,
    "IntranetInRate": 3122.835
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null,
    "IntranetInRate": 3041.29
  }
]
```

### i-bp13gqyopa94bry7qb2c (生产-大数据-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=10.1001, p95=10.562, max=10.811
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 10.003
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 10.365
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 10.101
  }
]
```

### i-bp13bkus3cb8x37ftr4b (生产-CRM-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null,
    "IntranetInRate": 4241342.873
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null,
    "IntranetInRate": 4542506.734
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null,
    "IntranetInRate": 4298283.144
  }
]
```

### i-bp131uzubb7um0ovvm51 (生产-健康-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=10.482999999999999, p95=10.801, max=10.805
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetOutRate": 170445.482
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 10.2,
    "IntranetOutRate": 129440.836
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetOutRate": 239981.636
  }
]
```

### i-bp1jfuozuwikd8w24stu (生产-技术中心-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15bfsmrvg3yfcdjznb (生产-保险-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=28.656416666666665, p95=29.242, max=30.139
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 28.214
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 28.568
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 29.242
  }
]
```

### i-bp113mhyqqqcrxeiftbt (测试-通用-acknode-013)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetRX": null,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetRX": null,
    "InternetTX": null
  }
]
```

### i-bp1ctodkpmhajry2s4n1 (测试-通用-ack测试dns-nginx)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.7831666666666667, p95=0.849, max=1.075
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 0.851,
    "IntranetOutRate": 9854.839,
    "DiskUsageUtilization": 8.61
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 0.735,
    "IntranetOutRate": 8445.815,
    "DiskUsageUtilization": 8.61
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 0.879,
    "IntranetOutRate": 8822.784,
    "DiskUsageUtilization": 8.61
  }
]
```

### i-bp1cc9mdf236r375vm81 (生产-通用-ack-node-030)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.2461166666666665, p95=3.678, max=3.979
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "CPU": 2.939,
    "IntranetInRate": 2728445.542
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 2.994,
    "IntranetInRate": 2939844.608
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 3.182,
    "IntranetInRate": 5338485.009
  }
]
```

### i-bp18mz3peh1jzjmh9gaa (生产-通用-ack-node-029)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null
  }
]
```

### i-bp1ik7t5d5f2n4hvc1me (生产-通用-ack-node-028)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1md (生产-通用-ack-node-027)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:49:00Z",
    "IntranetInRate": 11138.12
  },
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetInRate": 8868.081
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetInRate": 8988.584
  }
]
```

### i-bp1ik7t5d5f2n4hvc1ma (生产-通用-ack-node-026)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1m9 (生产-通用-ack-node-025)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.4756666666666667, p95=3.325, max=3.363
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 2.503,
    "IntranetOutRate": 1503860.462
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetOutRate": 1527297.774
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetOutRate": 1942319.377
  }
]
```

### i-bp1ik7t5d5f2n4hvc1m8 (生产-通用-ack-node-024)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "MemoryUtilization": 48.315
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "MemoryUtilization": 48.312
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "MemoryUtilization": 48.304
  }
]
```

### i-bp1ik7t5d5f2n4hvc1m7 (生产-通用-ack-node-023)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1m6 (生产-通用-ack-node-022)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=4.910464285714285, p95=5.679, max=6.604
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 4.774,
    "IntranetOutRate": 498209.314,
    "DiskUsageUtilization": 30.96
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 4.826,
    "IntranetOutRate": 650945.467,
    "DiskUsageUtilization": 30.96
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 4.772,
    "IntranetOutRate": 452326.331,
    "DiskUsageUtilization": 30.96
  }
]
```

### i-bp1ik7t5d5f2n4hvc1m5 (生产-通用-ack-node-021)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetInRate": 523347.968
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetInRate": 461671.219
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetInRate": 495721.13
  }
]
```

### i-bp1ik7t5d5f2n4hvc1mc (生产-通用-ack-node-020)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.6366181818181817, p95=2.931, max=3.336
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 1.348,
    "IntranetOutRate": 871019.997
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 1.378,
    "IntranetOutRate": 926776.524
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 1.363,
    "IntranetOutRate": 928395.81
  }
]
```

### i-bp1ik7t5d5f2n4hvc1mb (生产-通用-ack-node-019)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "MemoryUtilization": 44.922
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "MemoryUtilization": 44.912
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "MemoryUtilization": 44.927
  }
]
```

### i-bp12mfr8nud3quprwayo (生产-通用-ack-node-018)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mfr8nud3quprwaym (生产-通用-ack-node-017)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null,
    "IntranetOutRate": 1949052.108
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null,
    "IntranetOutRate": 1964825.395
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetOutRate": 1990158.062
  }
]
```

### i-bp12mfr8nud3quprwayl (生产-通用-ack-node-016)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.734, p95=3.808, max=3.834
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 3.622
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 3.798
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 3.808
  }
]
```

### i-bp12mfr8nud3quprwayn (生产-通用-ack-node-015)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetTX": null
  }
]
```

### i-bp12mfr8nud3quprwayh (生产-通用-ack-node-014)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mfr8nud3quprwayg (生产-通用-ack-node-013)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.3908333333333336, p95=2.422, max=2.424
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 2.414
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 2.399
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 2.375
  }
]
```

### i-bp12mfr8nud3quprwayi (生产-通用-ack-node-012)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetInRate": 461535.368,
    "DiskUsageUtilization": 27.02
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetInRate": 607996.45,
    "DiskUsageUtilization": 27.02
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetInRate": 661594.248,
    "DiskUsageUtilization": 27.02
  }
]
```

### i-bp12mfr8nud3quprwayk (生产-通用-ack-node-011)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.8781166666666667, p95=2.988, max=3.085
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 2.848,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 2.848,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 2.959,
    "InternetTX": null
  }
]
```

### i-bp12mfr8nud3quprwayj (生产-通用-ack-node-009)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=4.3603, p95=5.071, max=5.33
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 4.999,
    "InternetRX": null,
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 4.128,
    "InternetRX": null,
    "DiskUsageUtilization": 2.9
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 3.942,
    "InternetRX": null,
    "DiskUsageUtilization": 2.9
  }
]
```

### i-bp15t3qdt708wnxfqrs8 (生产-通用-ack-node-008)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetTX": null
  }
]
```

### i-bp15t3qdt708wnxfqrs6 (生产-通用-ack-node-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetRX": null
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetRX": null
  }
]
```

### i-bp15t3qdt708wnxfqrs5 (生产-通用-ack-node-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.723116666666667, p95=10.541, max=11.912
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 6.446,
    "IntranetOutRate": 3964121.497
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 5.377,
    "IntranetOutRate": 4362237.952
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 7.499,
    "IntranetOutRate": 5592356.454
  }
]
```

### i-bp15t3qdt708wnxfqrs4 (生产-通用-ack-node-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15t3qdt708wnxfqrs1 (生产-通用-ack-node-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "IntranetInRate": 8797872.81
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetInRate": 667365.922
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetInRate": 554311.816
  }
]
```

### i-bp15t3qdt708wnxfqrs3 (生产-通用-ack-node-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=5.94125, p95=6.176, max=6.468
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 5.571
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 5.656
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 6.11
  }
]
```

### i-bp15t3qdt708wnxfqrs2 (生产-通用-ack-node-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "InternetRX": null,
    "MemoryUtilization": 46.025
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetRX": null,
    "MemoryUtilization": 46.045
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetRX": null,
    "MemoryUtilization": 46.045
  }
]
```

### i-bp15t3qdt708wnxfqrs7 (生产-通用-ack-node-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19wgapp5a8lhdwacwt (生产-通用-ack-node-010)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.9988, p95=4.159, max=4.311
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 4.069
  },
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 3.911
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 4.045
  }
]
```

### i-bp1aegk8l8fgje6qnio3 (生产-微爱-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.73575, p95=0.745, max=0.806
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:50:00Z",
    "CPU": 0.738
  },
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 0.739
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 0.708
  }
]
```

### i-bp15t3qdt708w856ubs7 (生产-健康-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetRX": null,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetRX": null,
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "InternetRX": null,
    "InternetTX": null
  }
]
```

### i-bp1aegk8l8fgiugfiyva (生产-大数据-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetOutRate": 758024.192
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetOutRate": 282787.703
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetOutRate": 177540.846
  }
]
```

### i-bp19p4ib4b5uumbfgiad (生产-医疗-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "MemoryUtilization": 25.467
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "MemoryUtilization": 25.417
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "MemoryUtilization": 25.435
  }
]
```

### i-bp1aegk8l8fgikl9yoyw (生产-CRM-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.4291, p95=8.746, max=9.179
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 8.475
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 8.186
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 8.588
  }
]
```

### i-bp1h35mcqj4d7o2l9cu0 (生产-保险-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.2246999999999995, p95=7.437, max=7.583
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 7.443,
    "IntranetInRate": 505817.361
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 7.082,
    "IntranetInRate": 481817.804
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 7.471,
    "IntranetInRate": 472738.884
  }
]
```

### i-bp12un2oqsr3g432umuu (生产-技术中心-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1enj5sdg8gecgjap8i (生产-通用-ack-master)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.4253333333333333, p95=1.444, max=1.446
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "DiskUsageUtilization": 2.89
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "DiskUsageUtilization": 2.89
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "DiskUsageUtilization": 2.89
  }
]
```

### i-bp1abupkgyneaqe56ejq (生产-医疗-银河互联网电视ftp)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13zput9obyr6cyevk3 (测试-通用-ackingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1937jgqpsprj240ovz (生产-大数据-大语言模型训练-gpu-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=16.31235, p95=16.457, max=16.503
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 16.361,
    "IntranetInRate": 69.196
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 16.382,
    "IntranetInRate": 47.39
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 16.231,
    "IntranetInRate": 46.682
  }
]
```

### i-bp19jklbsxkuzxs45qwf (测试-技术中心-测试)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.8238333333333334, p95=2.248, max=2.385
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 1.694,
    "IntranetOutRate": 9023.897
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 1.69,
    "IntranetOutRate": 10722.508
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 1.706,
    "IntranetOutRate": 10041.07
  }
]
```

### i-bp1dsu59mjheqpn206tg (测试-通用-acknode-012)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetInRate": 9980.754
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetInRate": 10651.857
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetInRate": 10526.647
  }
]
```

### i-bp13onik0hd4uniz751o (测试-通用-acknode-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "MemoryUtilization": 68.362
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "MemoryUtilization": 68.89
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "MemoryUtilization": 68.722
  }
]
```

### i-bp13onik0hd4uniz751p (测试-通用-acknode-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.264183333333333, p95=8.388, max=8.406
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 8.167,
    "IntranetInRate": 328779.229
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 8.388,
    "IntranetInRate": 343261.047
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 8.342,
    "IntranetInRate": 348769.484
  }
]
```

### i-bp15i7kfg5ufoyfqg6o4 (测试-通用-acknode-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=9.153583333333334, p95=9.275, max=9.379
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 9.236
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 9.138
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 9.075
  }
]
```

### i-bp15i7kfg5ufoyfqg6o5 (测试-通用-acknode-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetRX": null,
    "IntranetInRate": 3824.424
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetRX": null,
    "IntranetInRate": 3326.086
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "InternetRX": null,
    "IntranetInRate": 3699.158
  }
]
```

### i-bp166brjk6veg3s7ucqj (测试-通用-acknode-008)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=9.609716666666666, p95=9.707, max=9.932
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 9.66
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 9.611
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 9.646
  }
]
```

### i-bp166brjk6veg3s7ucqi (测试-通用-acknode-009)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetTX": null
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "InternetTX": null
  }
]
```

### i-bp10f7ki9z95snz3mwda (测试-通用-acknode-010)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetOutRate": 4259.088
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetOutRate": 4184.894
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetOutRate": 4225.122
  }
]
```

### i-bp10f7ki9z95snz3mwd9 (测试-通用-acknode-011)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1aqi8px10bmc1a88y7 (测试-通用-acknode-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "InternetTX": null,
    "IntranetInRate": 1162002.432,
    "DiskUsageUtilization": 2.88
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetTX": null,
    "IntranetInRate": 2110135.637,
    "DiskUsageUtilization": 2.88
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "InternetTX": null,
    "IntranetInRate": 1097978.538,
    "DiskUsageUtilization": 2.88
  }
]
```

### i-bp1aqi8px10bmc1a88y9 (测试-通用-acknode-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "IntranetOutRate": 41220.505,
    "DiskUsageUtilization": 44.15
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetOutRate": 40615.385,
    "DiskUsageUtilization": 44.15
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetOutRate": 41013.622,
    "DiskUsageUtilization": 44.152
  }
]
```

### i-bp1aqi8px10bmc1a88y8 (测试-通用-acknode-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=2.8203333333333336, p95=2.916, max=2.939
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 2.576
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 2.786
  },
  {
    "TimeStamp": "2025-09-28T19:05:00Z",
    "CPU": 2.939
  }
]
```

### i-bp1bmtqus4wgdv6ex0v5 (测试-通用-etcd-new)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=26.877366666666667, p95=27.147, max=27.242
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 26.805
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 26.957
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 26.979
  }
]
```

### i-bp1gascwri3v0mh5x8ck (生产-保险-惠民保自营单回溯)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.0068, p95=3.21, max=16.82
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:51:00Z",
    "CPU": 2.766
  },
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 2.861
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 2.703
  }
]
```

### i-bp1h8smwi4n4sw26yz1w (生产-大数据-大语言模型训练-满碗-gpu-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetTX": null,
    "IntranetInRate": 39394.34
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "InternetTX": null,
    "IntranetInRate": 41182.251
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "InternetTX": null,
    "IntranetInRate": 41158.333
  }
]
```

### i-bp1b7lg8l7hk8b9peor6 (预生产-大数据-k8s-node)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetTX": null,
    "IntranetOutRate": 1878.525,
    "MemoryUtilization": 48.352
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "InternetTX": null,
    "IntranetOutRate": 1827.528,
    "MemoryUtilization": 48.975
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "InternetTX": null,
    "IntranetOutRate": 1828.295,
    "MemoryUtilization": 49.004
  }
]
```

### i-bp100gxsgywj6c7speff (生产-医疗-直播机器人-windows-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.21458333333333332, p95=0.229, max=0.236
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetOutRate": 7364.334
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetOutRate": 7499.229
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "IntranetOutRate": 7943.099
  }
]
```

### i-bp1dzyyuu16ojfwbfw2z (生产-运维-合同校验)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetRX": null,
    "DiskUsageUtilization": 11.38
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "InternetRX": null,
    "DiskUsageUtilization": 11.38
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "InternetRX": null,
    "DiskUsageUtilization": 11.38
  }
]
```

### i-bp1egahcnltsdf1yu5xx (生产-crm-驰云中心服务器-04)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetOutRate": 7872.468
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetOutRate": 8792.134
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "IntranetOutRate": 7943.684
  }
]
```

### i-bp15o1gwawi1afu80q6u (生产-医疗-直播机器人-windows-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetInRate": 9636.113
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetInRate": 8289.348
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "IntranetInRate": 8670.822
  }
]
```

### i-bp14pl40ckwe7vjvhqqt (生产-大数据-stable-video-diffusion-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetInRate": 82.386
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetInRate": 89.166
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "IntranetInRate": 82.297
  }
]
```

### i-bp16vhmca6h16zn2683c (生产-医疗-直播机器人-windows-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.3433333333333334, p95=0.392, max=0.642
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 0.31,
    "IntranetInRate": 10853.717
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 0.314,
    "IntranetInRate": 7884.117
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "CPU": 0.325,
    "IntranetInRate": 7976.14
  }
]
```

### i-bp10zf1gy4t2exf5vlyl (生产-大数据-大语言模型训练-空碗-gpu-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.5778, p95=8.986, max=10.216
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "CPU": 4.312,
    "MemoryUtilization": 50.912
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "CPU": 4.728,
    "MemoryUtilization": 50.91
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "CPU": 4.334,
    "MemoryUtilization": 50.902
  }
]
```

### i-bp15rwnojzp40sox0he1 (测试-大数据-ocr-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "DiskUsageUtilization": 19.73
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "DiskUsageUtilization": 19.73
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "DiskUsageUtilization": 19.73
  }
]
```

### i-bp1fym2bpuaqy1wq1gis (生产-通用-备案服务器-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "InternetTX": null,
    "IntranetInRate": 806.912
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "InternetTX": null,
    "IntranetInRate": 1203.541
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "InternetTX": null,
    "IntranetInRate": 2548.804
  }
]
```

### i-bp1fym2bpuaqy1wq1git (生产-通用-备案服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.80975, p95=7.435, max=7.811
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:55:00Z",
    "CPU": 6.819
  },
  {
    "TimeStamp": "2025-09-28T19:00:00Z",
    "CPU": 6.266
  },
  {
    "TimeStamp": "2025-09-28T19:05:00Z",
    "CPU": 6.357
  }
]
```

### i-bp110dn8uarqtxwtx82d (测试-通用-etcd-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.41, p95=1.438, max=1.463
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-28T18:52:00Z",
    "IntranetInRate": 1142.734,
    "IntranetOutRate": 136198.69,
    "DiskUsageUtilization": 7.98
  },
  {
    "TimeStamp": "2025-09-28T18:53:00Z",
    "IntranetInRate": 2869.79,
    "IntranetOutRate": 403507.473,
    "DiskUsageUtilization": 7.98
  },
  {
    "TimeStamp": "2025-09-28T18:54:00Z",
    "IntranetInRate": 1715.38,
    "IntranetOutRate": 233125.068,
    "DiskUsageUtilization": 7.98
  }
]
```
