# ECS巡检报告

- 开始: 2025-09-17 08:59:12 UTC
- 结束: 2025-09-17 08:59:12 UTC
- 地域: ['cn-hangzhou']
- 实例数: 594
- 窗口: 1h
- 并发: 20
- 阈值: CPU p95>=80.0%, 内存>=85.0%, 磁盘>=80.0%

## 汇总
- 高风险: 0
- 中风险: 1
- 低风险: 593

## Top 风险实例
| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |
|---|---|---|---:|---:|---:|---|---|
| i-bp1i1jaztjfl3gsa22s6 | 测试-平台支撑-安全IAST测试 | medium | 99.912 | - | - | cn-hangzhou-b | Running |
| i-bp1gac7y9jr1qfm1lydw | 预生产-通用-k8s-new-node-005 | low | 19.945 | - | - | cn-hangzhou-b | Running |
| i-bp13rpulwhqklvgrmnhq | 测试-保险-aj-001 | low | 17.087 | - | - | cn-hangzhou-e | Running |
| i-bp19qee7e1l6z0932a7n | 生产-火箭-提供http服务-002 | low | 15.122 | - | - | cn-hangzhou-b | Running |
| i-bp1cfj11xpdtffyeytbu | 测试-保险-pressur_measurement-002 | low | 14.549 | - | - | cn-hangzhou-b | Running |
| i-bp16589vyznk7kfx7lw0 | 生产-平台支撑-openvas-001 | low | 11.458 | - | - | cn-hangzhou-b | Running |
| i-bp1akooukwvp5op96ie2 | 测试-技术中心-费控系统-后台服务器-001 | low | 9.82 | - | - | cn-hangzhou-g | Running |
| i-bp1cx13y2y278hhs8awz | 测试-crm-莫莫目标追踪-001 | low | 9.314 | - | - | cn-hangzhou-k | Running |
| i-bp1gyurl0fqb3dusuu47 | 测试-技术中心-用户增长01 | low | 9.171 | - | - | cn-hangzhou-b | Running |
| i-bp18mr52zr78odr6b0o2 | 生产-健康-大病社区系统-002 | low | 8.457 | - | - | cn-hangzhou-g | Running |

## 明细（采样）
### i-bp1j4jvdujrtenkmndyt (生产-crm-驰云中心服务器-安卓)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.9216666666666666, p95=1.012, max=1.034
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 0.968,
    "IntranetOutRate": 3289.634
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 0.865,
    "IntranetOutRate": 4486.758
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 1.034,
    "IntranetOutRate": 8018.466
  }
]
```

### i-bp13yabzr5882mivlycf (生产-微爱-区块链-单点临时使用-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hh4jmc5lq815psq6v (生产-微爱-区块链-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 326.739
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 333.694
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 329.371
  }
]
```

### i-bp1hh4jmc5lq815psq6x (生产-微爱-区块链-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hh4jmc5lq815psq6w (生产-微爱-区块链-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.08786666666666668, p95=0.093, max=0.096
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 0.092
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 0.081
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 0.085
  }
]
```

### i-bp1i4ilhgbgmh0ad7tkr (测试-前端-coze-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14hd0h696itgph7q01 (生产-通用-ack-node-072)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1g5sg40chcucujygtm (测试-大数据-大语言模型训练-gpu-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f901c0xvcrh03yhnv (测试-通用-acknode-016)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp148a784artf4abq4rk (生产-微爱-区块链-调试-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp148a784artf4abq4ri (生产-微爱-区块链-调试-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp148a784artf4abq4rj (生产-微爱-区块链-调试-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13gg740rm1l6zo1mzb (测试-微爱-区块链-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b99get09sbi96bt7h (生产-通用-ack-node-071)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12e97wltuwwvjfo75w (测试-平台支撑-容器镜像)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17z7z7r9qjhdm5lww4 (测试-通用-acknode-015)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16bk59nfr78kelqpcd (生产-通用-ack-node-070)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1egki2k7iulh3w0sa8 (生产-通用-ack-node-069)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f5rx2dmkfquo3n7fz (生产-通用-skywalking-banyandb-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 6190727.85
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 7517920.051
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 2709641.762
  }
]
```

### i-bp1f5rx2dmkfquo3n7fy (生产-通用-skywalking-banyandb-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f5rx2dmkfquo3n7fx (生产-通用-skywalking-banyandb-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14yffwp9oi1pcwr7uo (生产-通用-skywalking-oap-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15aa8vfgb6ik00g1ds (生产-crm-莫莫目标追踪-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 28424.465
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 27845.563
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 27883.11
  }
]
```

### i-bp1flrwaw8ocd6swyf6d (测试-大数据-智能记忆体-neo4j图数据库)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11mw62lucculpmx75o (生产-大数据-智能记忆体-neo4j图数据库)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 10340.352
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 10925.533
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 10452.309
  }
]
```

### i-bp1cx13y2y278hhs8awz (测试-crm-莫莫目标追踪-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.544066666666668, p95=9.314, max=9.457
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 9.457
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 8.987
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 9.091
  }
]
```

### i-bp1azlu246g6s2je0kdr (生产-通用-ack-node-068)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ccl6gkupuuk8z5pfr (生产-通用-ack-node-067)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b35itfkfk8w3337jo (生产-CRM-OCR-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 6174.72
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 4651.281
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 4821.128
  }
]
```

### i-bp1fdju07s1hgeojnnms (生产-CRM-OCR-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17q4dvhdsw23r7dwuf (生产-大数据-莫莫猫脸识别-gpu-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hhoi63e4fa64hpujv (生产-通用-ack-node-68)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17vnk03hf08ownu5x9 (生产-crm-实时字幕烧录-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17vnk03hf08ownu5x7 (生产-crm-实时字幕烧录-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 6206576.776
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 23669655.551
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 25004089.207
  }
]
```

### i-bp17vnk03hf08ownu5x8 (生产-crm-实时字幕烧录-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp176liqfunsfoaogvol (生产-通用-ack-node-67)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp177xyvox3vsfpuieys (生产-大数据-日志拉取)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h1gu3djkpocvjlu57 (生产-医疗-文件上传-temp)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dnu601niybx0adgc9 (测试-莫莫-freeswitch-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11vwnue2zdyizyo8lu (生产-CRM-星语平台-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1jdb6m212e4z5kuxy9 (预生产-通用-k8s-new-node-014)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10zrbl0kd6wm2p0m9o (生产-CRM-星语平台-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cg7vw5j4bz3jr4jt7 (测试-通用-acknode-014)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16r9cxhil8iz0zt1kb (生产-通用-ack-node-065)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16r9cxhil8iz0zt1ka (生产-通用-ack-node-064)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp193mwb7ny9ljqpsfmp (生产-通用-ack-node-066)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19k0qor1uls8csx3vz (生产-通用-ack-node-063)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15bby7o91rhgk2rbe6 (生产-通用-ack-node-062)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gx2gg0t4i869ac6ie (生产-通用-ack-node-061)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 11369.643
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 6597.714
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 10951.395
  }
]
```

### i-bp1d9ctjyrk5obldp6vb (测试-莫莫-freeswitch-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp159h0vv1vwvpsljji5 (生产-大数据-langfuse-平台)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1bdcc19wenz2p0dnaf (生产-通用-ack-node-060)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=4.723933333333333, p95=4.776, max=4.855
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 4.716
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 4.656
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 4.855
  }
]
```

### i-bp1ivu3yaedtzh73s9pc (生产-CRM-星语平台-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 47381.708
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 14346822.587
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 12952797.047
  }
]
```

### i-bp1fqfje3gwdtbcikjzd (生产-大数据-外采)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16ocsr2n0jh5fv3gza (生产-医疗-文件上传-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h6tv5kezs83ofzyb7 (生产-crm-zy-企微会话存档-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b53i1ykx67i4ugy7e (生产-crm-zy-企微会话存档-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16i1531i6nlqj15h2x (生产-crm-驰云中心服务器-07)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16i1531i6nlqj15h2y (生产-crm-驰云中心服务器-06)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18ri3uy5ulu0ivx9o2 (生产-微爱-go_mp_client-vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 33890.304
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 34405.171
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 33403.426
  }
]
```

### i-bp18ri3uy5ulu0ivx9o1 (生产-微爱-go_mp_client-vpc-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17ycfcea3ibii4kq48 (生产-微爱-go_project_index-vpc-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17ycfcea3ibii4kq47 (生产-微爱-go_project_index-vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10wfdq4eqtbgw1jksc (生产-微爱-go_partner_ygl-vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10wfdq4eqtbgw1jksa (生产-微爱-go_partner-vpc-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10wfdq4eqtbgw1jksb (生产-微爱-go_partner-vpc-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10wfdq4eqtbgw1jks9 (生产-微爱-go_partner-vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1bnyi3nd6yxl32eoxx (生产-通用-ack-node-059)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19wzhktmfgn1586a4d (生产-通用-ack-node-058)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19wzhktmfgn1586a4f (生产-通用-ack-node-057)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19wzhktmfgn1586a4e (生产-通用-ack-node-056)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19wzhktmfgn1586a4c (生产-通用-ack-node-055)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fcql6prdzzzhpfq6s (生产-通用-ack-node-054)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fcql6prdzzzhpfq6p (生产-通用-ack-node-053)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fcql6prdzzzhpfq6q (生产-通用-ack-node-052)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.311, p95=1.357, max=1.375
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 1.32
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 1.315
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 1.357
  }
]
```

### i-bp1fcql6prdzzzhpfq6r (生产-通用-ack-node-051)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 7362440.26
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 7447210.53
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 7153257.403
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
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 11217.891
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 7493.512
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 7474.943
  }
]
```

### i-bp108xg7jezya6tjm7ih (生产-通用-ack-node-049)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp108xg7jezya6tjm7if (生产-通用-ack-node-048)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 1929136.264
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 1766172.262
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 1784766.327
  }
]
```

### i-bp108xg7jezya6tjm7ii (生产-通用-ack-node-047)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 4856224.153
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 4786527.436
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 5588782.011
  }
]
```

### i-bp108xg7jezya6tjm7ig (生产-通用-ack-node-046)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14b7jx33vieqjcs6x4 (生产-微爱-go_api_gateway_vpc-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14b7jx33vieqjcs6x5 (生产-微爱-go_api_gateway_vpc-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14b7jx33vieqjcs6x2 (生产-微爱-go_api_gateway_vpc-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14b7jx33vieqjcs6x6 (生产-微爱-go_api_gateway_vpc-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14b7jx33vieqjcs6x3 (生产-微爱-go_api_gateway_vpc-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 703931.596
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 812843.69
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 547010.969
  }
]
```

### i-bp19cvw9lyh82l7t5kwv (生产-微爱-go_partner-vpc-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19cvw9lyh82l7t5kwx (生产-微爱-go_partner-vpc-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19cvw9lyh82l7t5kww (生产-微爱-go_partner-vpc-008)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19cvw9lyh82l7t5kwu (生产-微爱-go_partner-vpc-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19cvw9lyh82l7t5kwt (生产-微爱-go_partner-vpc-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16q0s3g4c9cjihw9jr (生产-通用-ack-大数据文章查重-node-045)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 83556.078
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 106475.929
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 90417.425
  }
]
```

### i-bp16q0s3g4c9cjihw9jq (生产-通用-ack-大数据文章查重-node-044)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f08qxsdf6uee8oz59 (生产-通用-ack-大数据文章查重-node-043)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 140605.849
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 88325.87
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 161736.43
  }
]
```

### i-bp1f08qxsdf6uee8oz5a (生产-通用-ack-大数据文章查重-node-042)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f08qxsdf6uee8oz58 (生产-通用-ack-大数据文章生成-node-041)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f08qxsdf6uee8oz57 (生产-通用-ack-大数据文章生成-node-040)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f08qxsdf6uee8oz56 (生产-通用-ack-node-039)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10na7saw1vy2we9rib (生产-通用-ack-node-038)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 13205129.898
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 13068643.532
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 9904359.424
  }
]
```

### i-bp10na7saw1vy2we9ri9 (生产-通用-ack-node-037)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10na7saw1vy2we9ria (生产-通用-ack-node-036)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1djud42juqjc2perbi (生产-通用-ack-node-035)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1djud42juqjc2perbh (生产-通用-ack-node-034)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1djud42juqjc2perbg (生产-通用-ack-node-033)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14y1mtx36q1twgu20c (生产-通用-ack-node-032)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14y1mtx36q1twgu20d (生产-通用-ack-node-031)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp176ar7xqoj0ckd7f9r (生产-shangyitech-nginx-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1iomyvtcf7wsgffeet (生产-momo-nginx-out-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1iomyvtcf7wsgffees (生产-momo-nginx-out-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14efp0nz1vcue5tq1k (生产-momo-etcd-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14efp0nz1vcue5tq1m (生产-momo-etcd-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14efp0nz1vcue5tq1l (生产-momo-etcd-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 52283.392
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 52431.394
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 52459.929
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
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 130.931
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 173.479
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 126.423
  }
]
```

### i-bp102e6660kwur07m9lj (生产-微爱-php服务-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp102e6660kwur07m9li (生产-微爱-php服务-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 974.438
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 812.509
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 2540.339
  }
]
```

### i-bp1fva2t19bzbcabko7h (生产-微爱-app-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fva2t19bzbcabko7g (生产-微爱-app-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fva2t19bzbcabko7f (生产-微爱-单节点服务)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1izvhfvbrel4k1piw6 (生产-crm-驰云中心服务器-05)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1jfuozuwikduledeox (生产-医疗-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13gqyopa94bry7qb2c (生产-大数据-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13bkus3cb8x37ftr4b (生产-CRM-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp131uzubb7um0ovvm51 (生产-健康-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1jfuozuwikd8w24stu (生产-技术中心-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 2330718.89
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 4030272.443
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 2608795.511
  }
]
```

### i-bp15bfsmrvg3yfcdjznb (生产-保险-ACK-Ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp113mhyqqqcrxeiftbt (测试-通用-acknode-013)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ctodkpmhajry2s4n1 (测试-通用-ack测试dns-nginx)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cc9mdf236r375vm81 (生产-通用-ack-node-030)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18mz3peh1jzjmh9gaa (生产-通用-ack-node-029)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1me (生产-通用-ack-node-028)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.7169333333333334, p95=2.256, max=2.487
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 1.74,
    "IntranetOutRate": 8285.361
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 1.709,
    "IntranetOutRate": 7745.054
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 2.487,
    "IntranetOutRate": 10122.351
  }
]
```

### i-bp1ik7t5d5f2n4hvc1md (生产-通用-ack-node-027)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1ma (生产-通用-ack-node-026)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1m9 (生产-通用-ack-node-025)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1m8 (生产-通用-ack-node-024)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1m7 (生产-通用-ack-node-023)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1m6 (生产-通用-ack-node-022)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1m5 (生产-通用-ack-node-021)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1mc (生产-通用-ack-node-020)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ik7t5d5f2n4hvc1mb (生产-通用-ack-node-019)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 1096306.688
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 1796547.515
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 1158467.857
  }
]
```

### i-bp12mfr8nud3quprwayo (生产-通用-ack-node-018)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 8412.139
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 7145.479
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 8142.561
  }
]
```

### i-bp12mfr8nud3quprwaym (生产-通用-ack-node-017)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mfr8nud3quprwayl (生产-通用-ack-node-016)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mfr8nud3quprwayn (生产-通用-ack-node-015)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mfr8nud3quprwayh (生产-通用-ack-node-014)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mfr8nud3quprwayg (生产-通用-ack-node-013)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 6478.931
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 7046.178
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 7433.183
  }
]
```

### i-bp12mfr8nud3quprwayi (生产-通用-ack-node-012)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mfr8nud3quprwayk (生产-通用-ack-node-011)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mfr8nud3quprwayj (生产-通用-ack-node-009)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15t3qdt708wnxfqrs8 (生产-通用-ack-node-008)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15t3qdt708wnxfqrs6 (生产-通用-ack-node-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=5.602333333333333, p95=5.755, max=5.783
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 5.49
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 5.755
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 5.607
  }
]
```

### i-bp15t3qdt708wnxfqrs5 (生产-通用-ack-node-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15t3qdt708wnxfqrs4 (生产-通用-ack-node-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 4086853.631
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 2559475.029
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 3279733.282
  }
]
```

### i-bp15t3qdt708wnxfqrs1 (生产-通用-ack-node-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15t3qdt708wnxfqrs3 (生产-通用-ack-node-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 8698893.243
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 7806310.673
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 9163514.811
  }
]
```

### i-bp15t3qdt708wnxfqrs2 (生产-通用-ack-node-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15t3qdt708wnxfqrs7 (生产-通用-ack-node-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19wgapp5a8lhdwacwt (生产-通用-ack-node-010)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1aegk8l8fgje6qnio3 (生产-微爱-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15t3qdt708w856ubs7 (生产-健康-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1aegk8l8fgiugfiyva (生产-大数据-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 2716.245
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 2589.956
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 2282.608
  }
]
```

### i-bp19p4ib4b5uumbfgiad (生产-医疗-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1aegk8l8fgikl9yoyw (生产-CRM-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h35mcqj4d7o2l9cu0 (生产-保险-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 1664631.33
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 1287069.559
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 2454041.258
  }
]
```

### i-bp12un2oqsr3g432umuu (生产-技术中心-ACK-Ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1enj5sdg8gecgjap8i (生产-通用-ack-master)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1abupkgyneaqe56ejq (生产-医疗-银河互联网电视ftp)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13zput9obyr6cyevk3 (测试-通用-ackingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1937jgqpsprj240ovz (生产-大数据-大语言模型训练-gpu-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19jklbsxkuzxs45qwf (测试-技术中心-测试)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dsu59mjheqpn206tg (测试-通用-acknode-012)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13onik0hd4uniz751o (测试-通用-acknode-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13onik0hd4uniz751p (测试-通用-acknode-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15i7kfg5ufoyfqg6o4 (测试-通用-acknode-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15i7kfg5ufoyfqg6o5 (测试-通用-acknode-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp166brjk6veg3s7ucqj (测试-通用-acknode-008)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 3173918.037
  },
  {
    "TimeStamp": "2025-09-17T00:49:00Z",
    "IntranetInRate": 5806224.588
  },
  {
    "TimeStamp": "2025-09-17T00:50:00Z",
    "IntranetInRate": 6070802.158
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
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 4607.806
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 4754.046
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 4635.788
  }
]
```

### i-bp10f7ki9z95snz3mwda (测试-通用-acknode-010)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

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
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 11743.756
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 28898.879
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 31899.425
  }
]
```

### i-bp1aqi8px10bmc1a88y9 (测试-通用-acknode-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1aqi8px10bmc1a88y8 (测试-通用-acknode-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 2036.33
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 1819.773
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 2530.322
  }
]
```

### i-bp1bmtqus4wgdv6ex0v5 (测试-通用-etcd-new)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gascwri3v0mh5x8ck (生产-保险-惠民保自营单回溯)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h8smwi4n4sw26yz1w (生产-大数据-大语言模型训练-满碗-gpu-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b7lg8l7hk8b9peor6 (预生产-大数据-k8s-node)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp100gxsgywj6c7speff (生产-医疗-直播机器人-windows-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dzyyuu16ojfwbfw2z (生产-运维-合同校验)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1egahcnltsdf1yu5xx (生产-crm-驰云中心服务器-04)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15o1gwawi1afu80q6u (生产-医疗-直播机器人-windows-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14pl40ckwe7vjvhqqt (生产-大数据-stable-video-diffusion-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16vhmca6h16zn2683c (生产-医疗-直播机器人-windows-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10zf1gy4t2exf5vlyl (生产-大数据-大语言模型训练-空碗-gpu-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15rwnojzp40sox0he1 (测试-大数据-ocr-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fym2bpuaqy1wq1gis (生产-通用-备案服务器-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fym2bpuaqy1wq1git (生产-通用-备案服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp110dn8uarqtxwtx82d (测试-通用-etcd-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp110dn8uarqtxwtx82c (测试-通用-etcd-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 345.173
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 334.561
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 335.053
  }
]
```

### i-bp1fijqsvr0nitmgx28t (生产-通用-etcdbackup-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b4gfja0gzlsozrfww (生产-通用-etcdbackup-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1el4aqr0z8w6zzw5y7 (生产-通用-etcdbackup-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 184.097
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 183.662
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 185.537
  }
]
```

### i-bp16rkx0pygpg0sgbpwj (测试-通用-etcd-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10zzsxofvfhqpawd0p (生产-通用-etcd-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10zzsxofvfhqpawd0o (生产-通用-etcd-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=0.9036000000000001, p95=1.104, max=1.108
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 1.103
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 0.672
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 1.102
  }
]
```

### i-bp10zzsxofvfhqpawd0l (生产-通用-etcd-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 233797.495
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 241592.593
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 233709.158
  }
]
```

### i-bp10zzsxofvfhqpawd0n (生产-通用-etcd-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10zzsxofvfhqpawd0m (生产-通用-etcd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gzf0ud0750yli1qhk (生产-凯森-数据中台)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dh1nra86nh61lt53p (生产-大数据-大语言模型训练-chatglm-gpu-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10fw6e3knjj3dxmjzz (生产-微爱-go_star_rank-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10fw6e3knjj3dxmk00 (生产-微爱-go_star_rank-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1a486f2b85t7v67wih (生产-crm-灵犀-FreeSwitch外呼-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 74.273
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 72.744
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 115.69
  }
]
```

### i-bp1a486f2b85t7v67wii (生产-crm-灵犀-FreeSwitch外呼-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15upeobtygxflf93ux (生产-健康-ocr-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15upeobtygxflf93uy (生产-健康-ocr-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19vaqycpstsfl0zhkc (测试-运维-zhaoyingzhao-测试)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14pghwoim62592piy8 (生产-大数据-qdrant-new-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14pghwoim62592piy9 (生产-大数据-qdrant-new-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14pghwoim62592piy7 (生产-大数据-qdrant-new-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15k8me9xxz66c4ar05 (生产-大数据-大语言模型训练-微爱文章生成-gpu-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19jjtn3ug31wejoqfq (生产-微爱-pdf2image)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16k5b0w9u0z58ql785 (测试-平台支撑-jenkins-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ds7tlphnpt0jjufvr (生产-crm-驰云中心服务器-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1iv71u7ecjcmecwprs (生产-运维-openvpn-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12b9kkb0ctifr7g6ha (生产-通用-银河系统-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17pgjo9trkh9wdov4r (生产-大数据-qdrant-备机)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=5.1532, p95=5.242, max=5.329
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 5.15
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 5.083
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 5.112
  }
]
```

### i-bp18jmci3lktccl7edd0 (预生产-通用-k8s-new-node-011)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ct2tli830d2p5plot (预生产-通用-k8s-new-node-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13alik0sur3u6joola (预生产-通用-k8s-new-node-010)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.917, p95=4.0, max=4.05
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 4.05
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 3.854
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 3.913
  }
]
```

### i-bp13alik0sur3u6joolc (预生产-通用-k8s-new-node-009)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13alik0sur3u6joolb (预生产-通用-k8s-new-node-008)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1bp07fvq98758kpoi8 (预生产-通用-k8s-new-node-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cchat3h7a8we9uxhk (预生产-通用-k8s-new-node-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gv5zqy3838powbq5r (测试-大数据-大语言模型训练-gpu-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gy6erv790djpihdsg (预生产-通用-k8s-new-ingress-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp193pyn62ke9ba6or7n (测试-大数据-qdrant-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gac7y9jr1qfm1lydw (预生产-通用-k8s-new-node-005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=10.848866666666668, p95=19.945, max=42.783
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 3.844,
    "IntranetOutRate": 1450.691
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 3.761,
    "IntranetOutRate": 1483.017
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 42.783,
    "IntranetOutRate": 1432.481
  }
]
```

### i-bp1do45w3vv00gwjb6z1 (预生产-通用-k8s-new-node-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1d0ol2age3gw1ylet7 (预生产-通用-k8s-new-node-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 176615.287
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 165160.277
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 186224.64
  }
]
```

### i-bp1d0ol2age3gw1ylet8 (预生产-通用-k8s-new-master-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1d0ol2age3gw1ylet6 (预生产-通用-k8s-new-node-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1252k8g9rz0k227vit (生产-平台支撑-ceph-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1252k8g9rz0k227vis (生产-平台支撑-ceph-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1252k8g9rz0k227vir (生产-平台支撑-ceph-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18qu99751x91uir9eu (测试-平台支撑-dongpengfeitest)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.5050666666666666, p95=3.606, max=3.632
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 3.632
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 3.466
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 3.458
  }
]
```

### i-bp1ez9c8uqbq6zs7luaz (生产-财务-见证宝sftp)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1bo0aclgmhojf1v9qj (生产-平台支撑-openvpn-ldap-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15m9wf21ndfqy20fij (生产-平台支撑-DBA-influxdb1)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 2442.302
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 1336.937
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 265.115
  }
]
```

### i-bp1jfpj9agehtgyzbetx (生产-大数据-asr-语音识别-gpu-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1jfpj9agehtgyzbety (生产-大数据-asr-语音识别-gpu-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 100676.932
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 95059.925
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 46669.055
  }
]
```

### i-bp1jfpj9agehtgyzbetz (生产-大数据-asr-话者分离)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp111kxlfo9hx8lin42a (生产-大数据-asr-语音识别-cpu-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=4.968933333333333, p95=5.124, max=5.217
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "CPU": 4.967
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 5.124
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 5.089
  }
]
```

### i-bp111kxlfo9hx8lin429 (生产-大数据-asr-语音识别-cpu-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp194ytlctx82okj8fs1 (生产-大数据-asr-链路服务)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19qti7th4vdsy0skxu (生产-运维-node-091)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1desdbbfvez7pbhbp5 (测试-微爱-qa_test-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1be50e2kdjiyh002gq (生产-微爱-qsc3_php_轻松筹web_go_sms-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 23012.283
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 24378.709
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 23070.31
  }
]
```

### i-bp10vrrkqcniqh26nepg (生产-大数据-gitlab-runner)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12k79b8x807xxrqh7i (生产-运维-xxl-job-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13k03iocj2rmss9rbl (生产-运维-xxl-job-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gz8ckhhzwkirhu4g6 (生产-运维-xxl-job-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1d5ab6obya20d9ml5s (生产-运维-k8s-ingress-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19b1h56x8330y910sh (测试-平台支撑-devops-elk-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18aaoq4jqbirvays76 (测试-平台支撑-devops-elk-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ap0tc2oyiygw5xwwk (测试-平台支撑-devops-elk-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 2163.732
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 2114.333
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 2150.83
  }
]
```

### i-bp1f1qmettu9hs1ivh7q (生产-crm-驰云中心服务器-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18m9bpfejwpi9jau6q (生产-运维-k8s-master-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18m9bpfejwpi9jau6o (生产-运维-k8s-node-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18m9bpfejwpi9jau6s (生产-运维-k8s-node-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 135876.334
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 134306.201
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 136373.998
  }
]
```

### i-bp18m9bpfejwpi9jau6p (生产-运维-k8s-node-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 779098.794
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 924465.834
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 1104746.359
  }
]
```

### i-bp19nvnorew1q3mjjehs (生产-crm-驰云中心服务器-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12v58sgw5gu8weieom (生产-crm-驰云私有云)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16hgwrbfh6zty2b0vt (生产-大数据-神策-data-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16hgwrbfh6zty2b0vu (生产-大数据-神策-data-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16hgwrbfh6zty2b0vv (生产-大数据-神策-data-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetOutRate": 6701126.041
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 7290939.528
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 6941480.55
  }
]
```

### i-bp1593ot6c26wgnd3q6p (生产-大数据-神策-mdata-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1593ot6c26wgnd3q6o (生产-大数据-神策-mdata-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:44:00Z",
    "IntranetInRate": 14009.362
  },
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 13994.328
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 13509.042
  }
]
```

### i-bp1593ot6c26wgnd3q6q (生产-大数据-神策-mdata-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1iqbggnsm7btxjvmpm (生产-大数据-nginx-002-new)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12lib8f785zpyzg0rt (生产-大数据-nginx-001-new)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14n6kbu6xlakbr361l (生产-保险-openapi-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1goeqot4h4d37p4sek (测试-平台支撑-grafa-test)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 15.711
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 15.787
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 26.846
  }
]
```

### i-bp18amzo1pw5dcs1zlhz (生产-运维-DBA归档-1)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11xckqzo1qc8006zgl (测试-运维-ak8s-ops)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10xc1pcwgd96wikwcj (测试-运维-k8s-ops)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19hhlk4yefea5tk9vw (生产-大数据-tableau003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12wzdmw1wwaf2tfn7q (生产-大数据-tableau002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ioowc3g7gs16a5h14 (生产-大数据-tableau001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hf37dflnnsk32d4k2 (生产-平台支撑-k8s-harbor-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15q9uiddth09z73v9p (生产-平台支撑-devops-qscoms-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gb8l3tk590iwhbi25 (开发-大数据-Linkis服务)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp144slsoje6we6dn916 (测试-平台支撑-devops-common-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b5qxtoduchxu0cup6 (生产-前端-npm私有仓库)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 139.73
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 33.337
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 16.662
  }
]
```

### i-bp1c2dtlxw1j3n5gk1t7 (生产-保险-ebao-api-ms-task-manage-001-new)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18c46ib9ng2i2csyy0 (压测-通用-k8s-node-06)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18c46ib9ng2i2csyxz (压测-通用-k8s-node-05)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16jtdc34fu69kij85r (生产-保险-api-ms-v3-prod006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16jtdc34fu69kij85p (生产-保险-api-ms-v3-prod005)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16jtdc34fu69kij85q (生产-保险-api-ms-v3-prod004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp152prtht93h77089gp (测试-通用-k8s-node-009)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hvmf79f6ekv2qqc8z (测试-通用-k8s-ingress)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.4632666666666667, p95=3.55, max=3.628
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 3.441
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 3.628
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 3.358
  }
]
```

### i-bp1egbr8o5u4apdw07b5 (开发-健康-nginx-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1i1jaztjfl3gsa22s6 (测试-平台支撑-安全IAST测试)
- 风险: medium | 标记: {'cpu_p95_high': True, 'memory_high': False, 'disk_high': False}
- CPU: avg=99.88333333333334, p95=99.912, max=99.931
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 99.887
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 99.836
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 99.859
  }
]
```

### i-bp1eijm8to1xfgmpok98 (压测-通用-k8s-ingress-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1eijm8to1xfgmpok99 (压测-通用-k8s-ingress-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h6spvddwiacwjwc3d (测试-平台支撑-skywalking-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18no7hkaueuqdlmti8 (生产-平台支撑-堡垒机-new-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hpjwbw5ra06igkjqc (生产-平台支撑-堡垒机-new-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17piwbrpx0r2c2ncyi (生产-平台支撑-ES-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 206504.769
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 202474.8
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 230166.896
  }
]
```

### i-bp17piwbrpx0r2c2ncyj (生产-平台支撑-ES-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17piwbrpx0r2c2ncyk (生产-平台支撑-ES-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 327574.567
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 308860.724
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 286117.97
  }
]
```

### i-bp19bspzms79p4murgc7 (生产-平台支撑-devops-qscoms-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp121mhndh5gl3d2t4g5 (生产-平台支撑-自定义监控脚本机器)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15lasta90xy7lneqz3 (生产-平台支撑-skywalking-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15lasta90xy7lneqz2 (生产-平台支撑-skywalking-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15lasta90xy7lneqz4 (生产-平台支撑-skywalking-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 869.385
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 770.985
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 902.353
  }
]
```

### i-bp111y5fbfu06139aapc (生产-微爱-nginx-inner-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 381.606
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 386.687
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 390.834
  }
]
```

### i-bp111y5fbfu06139aapd (生产-微爱-nginx-inner-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp153pwyvblguxr3eikn (测试-运维-etcd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1bobyt8kibvwvzgamd (生产-前端-vue构建机器)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1780n6r6rtmrgr0s2d (生产-技术中心-费控系统-filesys-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h3bdea4pbb63n19yv (生产-技术中心-费控系统-admin-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h3bdea4pbb63n19yu (生产-技术中心-费控系统-admin-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10m862v342xyqq6dyh (生产-技术中心-费控系统-job-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 15957.879
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 19610.555
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 17496.883
  }
]
```

### i-bp10uo1c6bfd52yz9uyu (生产-技术中心-费控系统-api_nginx-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10uo1c6bfd52yz9uyt (生产-技术中心-费控系统-api_nginx-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1eho37e5nw2gzmav36 (生产-平台支撑-漏扫)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f7eqaprlpqwzzz0ec (生产-大数据-split-clue)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ff214qpa0zzgbml81 (压测-通用-nginx-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ekymn8og7kdmh0wao (压测-通用-nacos)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ivitz6d5hxonkfeo9 (生产-保险-ebao-backtrack-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1er8ll8is9sd2xim17 (生产-保险-ebao-backtrack-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1263iphg0piclnrn9d (生产-保险-ebao-backtrack-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12mpdj5b72wem6kyws (生产-健康-health-admin-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 17535.931
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 17830.57
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 17410.73
  }
]
```

### i-bp1aza1q41525ns775cl (生产-平台支撑-nacos-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp125ym0e8yx61zanwyr (生产-平台支撑-nacos-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17epc8vfl26bfif6q9 (生产-平台支撑-nacos-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dqh9q8l3fuwv1dhux (预生产-技术中心-nacos-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14rxfga5iv4bcbos7z (生产-保险-backtracking-admin-以防监管查询可回溯)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hfcfw07luwzf8dnrq (开发-健康-公共服务nacos-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12tyu20diudzgs38bo (生产-平台支撑-堡垒机-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 2566.69
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 1040.52
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 1797.87
  }
]
```

### i-bp1akooukwvp5op96ie2 (测试-技术中心-费控系统-后台服务器-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.85, p95=9.82, max=12.441
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 6.364
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 6.266
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 9.82
  }
]
```

### i-bp1f9dh7rtuhpn5qo42x (测试-技术中心-费控系统-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp196t897o8qxrmvoe5d (预生产-通用-nginx-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h58plc0ufe8judimf (生产-平台支撑-nexus-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 147.529
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 150.386
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 147.499
  }
]
```

### i-bp18up6yqp25mqczwyzk (生产-凯森-phone-convert-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp179uw4fsjp0fzdyza1 (生产-平台支撑-devops_alarm-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 63.169
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 63.027
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 78.041
  }
]
```

### i-bp1bretxzvgy5og7jgg3 (生产-平台支撑-devops_alarm-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13rpulwhqklvgrmnhq (测试-保险-aj-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=11.312266666666666, p95=17.087, max=17.278
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 9.979
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 16.429
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 9.915
  }
]
```

### i-bp1hklmb7naxus8taljc (开发-平台支撑-.-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1j6g2ax5j0fxxcm429 (生产-财务-go-cert-service-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1498k1otx846oo8keo (生产-健康-nginx-out-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1498k1otx846oo8ken (生产-健康-nginx-in-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17axzvpyuexstfjaez (生产-健康-nginx-in-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17axzvpyuexstfjaey (生产-健康-nginx-out-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dv4sp3ktf3ek4gg3d (压测-通用-k8s-node-04)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dv4sp3ktf3ek4gg3c (压测-通用-k8s-node-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13h95mcoht3kb5ucg1 (压测-通用-k8s-node-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13h95mcoht3kb5ucg2 (压测-通用-k8s-node-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dn3njwpmdfq31odtc (压测-通用-k8s-master-03)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1imvno00dnju0yokbh (压测-通用-k8s-master-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1iwq64qj83akqczngs (压测-通用-k8s-master-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17a6fpu9ruhkxveq32 (生产-财务-go-cert-service-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1bw6bg3nsrehzc5weh (生产-财务-go-cert-service-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17is7vbu4nt11a5pjs (生产-保险-activities-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19uyyqp88cpxgmqnby (生产-保险-activities-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13l2tka3mcbch9xbvp (生产-外包-轻松筹-人力系统轻松小学)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cfj11xpdtffyeytbu (测试-保险-pressur_measurement-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=13.807133333333333, p95=14.549, max=16.277
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 12.611
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 12.611
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 12.506
  }
]
```

### i-bp1dyfzp857m0jobbiwx (测试-保险-pressur_measurement-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14oie16kr630osmbec (生产-大数据-nginx-inner-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1c3ke2vqa05r7qo87v (生产-大数据-nginx-inner-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp167mdyatjvcidj68fu (测试-保险-migration_project-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1htmw3s4pq251updny (预生产-技术中心-敏感服务)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18znguopl6krg1nc0y (生产-技术中心-后端-data-trans-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=1.5345333333333333, p95=1.558, max=1.814
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 1.516
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 1.522
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 1.515
  }
]
```

### i-bp1igenmrfpojti7g96p (生产-平台支撑-k8s-ingress-002-待定)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.655466666666666, p95=7.939, max=8.095
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 7.45
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 7.512
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 7.765
  }
]
```

### i-bp1igenmrfpojti7g96o (生产-微爱-k8s-ingress-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11ez8lmp5jpd4vogrm (生产-会员-nginx-in-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11ez8lmp5jpd4vogro (生产-保险-nginx-out-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11ez8lmp5jpd4vogrk (生产-保险-nginx-in-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 1553892.966
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 950766.114
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 935108.198
  }
]
```

### i-bp179lofu2s9ksxbc0pu (生产-会员-nginx-out-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=4.991866666666667, p95=5.34, max=5.82
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 5.075
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 5.007
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 5.066
  }
]
```

### i-bp179lofu2s9ksxbc0px (生产-会员-nginx-out-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp179lofu2s9ksxbc0pv (生产-会员-nginx-in-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 22487.176
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 22173.696
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 25399.022
  }
]
```

### i-bp179lofu2s9ksxbc0ps (生产-保险-nginx-out-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 1893080.405
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 1668531.268
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 1817804.39
  }
]
```

### i-bp179lofu2s9ksxbc0pw (生产-保险-nginx-in-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=3.3714, p95=3.616, max=4.378
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 3.279
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 3.341
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 3.403
  }
]
```

### i-bp1bvomq1xq18xqhqlkq (测试-技术中心-nginx)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp120pf8pffsg7jefudd (生产-平台支撑-jenkins)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ggjr0d8ktms2scjx6 (生产-技术中心-nginx-out-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17z7ks8yvbx3qe74vq (生产-平台支撑-alertmanager-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17z7ks8yvbx3qe74vp (生产-平台支撑-alertmanager-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17z7ks8yvbx3qe74vo (压测-通用-etcd)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 36912.059
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 35262.054
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 35374.557
  }
]
```

### i-bp13j70qg685ozgzn0bg (生产-平台支撑-Prometheus-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f4zu0mvk20upk3qec (生产-平台支撑-Prometheus-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 3724.871
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 3726.732
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 3808.479
  }
]
```

### i-bp13dj8i3kf6g61kbgqh (生产-技术中心-go_center_schedule_cron-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13dj8i3kf6g61kbgqi (生产-技术中心-go_center_schedule_cron-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13dj8i3kf6g61kbgqg (生产-技术中心-go_center_schedule_cron-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11u6rj79bxp73gztuw (生产-技术中心-nginx-inner-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1546opi6um349tigs7 (开发-技术中心-qa_tools-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1adg00c6qoeujjoqyn (生产-技术中心-nginx-inner-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 7081618.5
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 5136411.579
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 4055325.218
  }
]
```

### i-bp18usa82hd1vdtzrfrj (生产-技术中心-nginx-out-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1a3ntfw0zgs6vvy6i6 (生产-健康-go_healthplatform_task-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10m18xa3fxhnj3dqtj (测试-大数据-data_bus-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ekt9drfuh0832i1s3 (生产-大数据-nlp_node-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11o0n0b4302t7s73id (生产-大数据-算法)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10c9y124p2rfcb5ktz (生产-健康-go_healthapp_task-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15emvfk4ai3xsx8v3y (预生产-健康-go_healthcare_pre-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gh7gke2goyrbqiwj4 (生产-平台支撑-openvpn-ldap-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1e8z3uz7pktljoq123 (开发-保险-redash业务监控-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp150hce9r0nbo0g4w04 (生产-保险-new_spock-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10fezk86gmjakky6vo (测试-Q保-qbao-app-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 34952.533
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 35216.725
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 36662.886
  }
]
```

### i-bp1d3dvbh9byliapn1jy (测试-Q保-qbao-app-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 230.978
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 133.248
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 126.795
  }
]
```

### i-bp1iemoke3l051idu2t2 (测试-技术中心-go_center_refund-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15uvy8by0tlwafkgf2 (生产-凯森-网关001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1d5ddx5mie09re4zcu (测试-大数据-services_test-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1baqvusvn5wu5ew7qv (测试-大数据-services_test-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13gkk2sac5mweawiav (测试-大数据-services_test-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fna3fievsg84debc7 (生产-保险-java-claims_sync_app-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13lgnve382ciope4cm (生产-保险-java-claims_sync_app-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 220.047
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 104.447
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 81.028
  }
]
```

### i-bp1bfwcbqjtagigi9yk2 (生产-保险-api-ms-v3-prod001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1bfwcbqjtagigi9yk3 (生产-保险-api-ms-v3-prod002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1bfwcbqjtagigi9yk1 (生产-保险-api-ms-v3-prod003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19t4224ytq5tbtfswm (生产-技术中心-技术中心静态资源-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1brrrx37m2nz8ese5v (生产-凯森-数据同步)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1963q1kvl24sp6x8zo (测试-大数据-测试机-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13tfdbinchr91nfnft (测试-大数据-测试机-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cub1nwgqpvpk7blmb (生产-凯森-轻松筹泰康项目-web)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13al3gx35bec80jts5 (生产-保险-ebao-spock-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14a0v1sz0eauokx0jv (生产-技术中心-go_center_qydk-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=6.1903999999999995, p95=6.535, max=6.742
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 5.919
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 6.217
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 6.535
  }
]
```

### i-bp1j1alu0701o2zdm7bi (生产-技术中心-go_center_qydk-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ce2qjqwk15x47u6a0 (测试-保险-ebao-test-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16ctwpabqnso8m7y3o (生产-技术中心-go_center_dk-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fv3o6y2wra4m2vq4b (生产-健康-go_healthservice_task-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 31794.38
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 31243.332
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 31447.586
  }
]
```

### i-bp13q6hd8z3wf9ouvo40 (生产-会员-FE-nginx-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b7tj5u2oesexa4epm (生产-会员-FE-nginx-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10v9gd79mq37hromon (生产-凯森-跳板机-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 16867.601
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 3512.046
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 3528.977
  }
]
```

### i-bp1c2lnnishmulwj4ycz (生产-凯森-数据管理-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gixvf6p71fn7juebg (生产-会员-go_mutual_task-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 731.073
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 734.935
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 722.541
  }
]
```

### i-bp1go9891vednf0l9bgi (生产-技术中心-zk-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 28.459
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 17.97
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 28.644
  }
]
```

### i-bp11hv61p238cgvil9u1 (生产-技术中心-zk-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10w6mxav9zeiw7ra00 (生产-技术中心-zk-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18wbngpzva0nbypfix (生产-大数据-ner-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b12nih6lgcq4v8pm6 (生产-大数据-ner-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1e68obldg3uz6w38rx (生产-保险-fe-access-node-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 50642.67
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 53798.775
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 55305.42
  }
]
```

### i-bp1e68obldg3ux7uz6sp (生产-保险-fe-access-node-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11i3ig6f4548t1h1tu (生产-技术中心-ding_callback-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 252.0
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 188.892
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 199.318
  }
]
```

### i-bp1iaj62cegwryevf09t (生产-保险-openapi-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16rm1auwaddfb6me3z (测试-会员-go_mutual_task-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12slqenpvboczbq47x (生产-技术中心-urp_admin-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp171nliad1je1eptx30 (生产-技术中心-urp-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17c2vrtqpxarad3fv6 (生产-技术中心-urp-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1izpokikof3lpx8ye0 (预生产-技术中心-grows-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16fyb0guks0xnl5rcc (测试-保险-ebao-v1-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10n9722bkr0u9tb9l4 (生产-财务-settlement-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 705.727
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 725.864
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 707.377
  }
]
```

### i-bp163v1l5cfugq2lxtt1 (生产-财务-settlement-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16ik43u2n21j7js9zv (生产-保险-goldfish-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10lniqggy64p6ojvqg (生产-平台支撑-dnsmasq)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1eumzz9ehjeurvye04 (测试-保险-fe-test-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ba4p55m5lpsxwtlzm (预生产-保险-fe-pre-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1a72zikj28hs24l2n9 (生产-保险-apigateway-statsd-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp163b1t0urze53y34zn (生产-保险-apigateway-statsd-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12fba8yswl5gtqcdm1 (生产-保险-apigateway-statsd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 13609.506
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 12302.745
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetOutRate": 12608.443
  }
]
```

### i-bp1d232pzwmov2mz5pjf (生产-保险-apigateway-manage-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16oiztlz8lu9ssilz6 (生产-保险-apigateway-influxdb-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 101.253
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 92.767
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 94.591
  }
]
```

### i-bp13pr318zrjgmtu1nws (生产-平台支撑-k8s-etcd-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cz9kz76weo6ib8zan (生产-保险-apigateway-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h8m2chopj0ef0133r (生产-保险-apigateway-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17g7m5das0u92mawxx (生产-保险-apigateway-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17720r8yhsq64dcwfo (测试-微爱-skywaliking-test)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1j5zwxo6poap5gz5a9 (预生产-CRM-crm_pre-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14x0g864bpzx8izrdv (开发-技术中心-phabricator-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10hna2lsnwq7ogn5on (测试-大数据-标签测试-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 165.107
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 170.314
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 170.482
  }
]
```

### i-bp11zao4uxbrlob1eozz (生产-crm-elasticsearch001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 9520.899
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 9499.22
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 9042.467
  }
]
```

### i-bp11zao4uxbrlob1ep00 (生产-crm-elasticsearch002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11zao4uxbrlob1ep01 (生产-crm-elasticsearch003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1b7f1mm2t6mxoqqg32 (生产-技术中心-jaeger-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 544651.673
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 523934.105
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetInRate": 593317.068
  }
]
```

### i-bp10zgmfu7nvfe8w5t3d (生产-技术中心-jaeger-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1g66sbsdxp1q5t4oaq (生产-平台支撑-dns-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1g66sbsdxp1q5t4oas (生产-平台支撑-dns-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 4355.959
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 3329.911
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 1942.186
  }
]
```

### i-bp1g66sbsdxp1q5t4oar (生产-平台支撑-dns-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 17095.065
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 21317.631
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 16093.457
  }
]
```

### i-bp17rbxjqz4qn0e60o7w (生产-技术中心-go_center_receipt-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 284.33
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 263.563
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 261.884
  }
]
```

### i-bp1ivhkgilwhu0rkonj9 (生产-技术中心-go_center_receipt-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 247.783
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 243.762
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 249.279
  }
]
```

### i-bp1c88sbllf42gdfuxyf (预生产-平台支撑-dns-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17jei1pul0y1a393xt (生产-通用-ebao-yapi-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11dyfw79gx0e3ilrcp (生产-CRM-Go-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12g33obkw3a0vz0d6d (预生产-会员-go_vip_pre-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17aowbj7d9gy4vtjgq (生产-保险-ebao-task_spock-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 11867.34
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 12291.686
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 13452.492
  }
]
```

### i-bp14fk5yd8eh3rmke6f0 (生产-保险-ebao-notify-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19nphq1ilzr2bogu3q (生产-保险-ebao-notify-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fck6rch7w43kz99g1 (生产-保险-ebao-api-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15mimsmv0j8z3bcao8 (生产-保险-ebao-api-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19r762s7xsjehv0jnd (生产-保险-ebao-api-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15mimsmv0j8x4a88oo (生产-保险-ebao-admin-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dyqve8yyc6m30nln1 (生产-Q保-qbao_data_prod-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 33670.894
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 37350.331
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 35162.658
  }
]
```

### i-bp1dtvjt554w9k5ym4ka (生产-Q保-qbao_data_prod-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1erqefu8ehl7cs6zzf (生产-Q保-qbao_app_prod-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12dcog2gppbip2feww (生产-Q保-qbao_app_prod-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1636g8ewdn8icyupoz (预生产-Q保-qbao_pre-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1dtvjt554vxc62hrh4 (生产-Q保-qbao_data_prod-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10lb7tmlxt8081p5c7 (生产-Q保-qbao_data_prod-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 68.223
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 57.366
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 57.416
  }
]
```

### i-bp1636g8ewdn8eewmlq7 (生产-Q保-qbao-paycenter-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16cdvzk4rhpkn7e3fl (生产-Q保-qbao-paycenter-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14afmchbfo4cinshbb (生产-技术中心-优惠券-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14afmchbfo4cinshb9 (生产-技术中心-优惠券-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 164.923
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 167.541
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 166.875
  }
]
```

### i-bp14afmchbfo4cinshbc (生产-技术中心-优惠券-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16xttbby2da5rguosz (生产-平台支撑-tenginx_for_elk_and_钉钉微应用-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetInRate": 1132.953
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 2642.875
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 1776.571
  }
]
```

### i-bp12dpr9gpgafjxx7iy2 (生产-技术中心-推送平台001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12dpr9gpgafjxx7iy4 (生产-技术中心-推送平台002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12dpr9gpgafjxx7iy3 (生产-技术中心-推送平台003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11q05lzhgf1cv3e41y (测试-CRM-CRM)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 137.351
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 133.944
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 136.494
  }
]
```

### i-bp13xgu7xnkpy69loxis (生产-技术中心-profile-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1f2y4ij2clnunkzffq (生产-平台支撑-DBA-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1en2bkrf1ez6moogo4 (生产-保险-任务调度中心-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ebznxpym75pt6ypg8 (生产-平台支撑-日志收集-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1arj8dptvi6zfhtgfi (生产-平台支撑-conf_manage-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13tmf4a9vebqy3721d (开发-保险-openresty-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hudtjguhbujzbnags (生产-技术中心-性能测试-salve-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gomezxwu9ez7u5zm2 (生产-健康-模块化管理后台-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngp2 (生产-技术中心-猎户投放API系统-v2-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngp6 (生产-技术中心-猎户投放API系统-v2-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngp5 (生产-技术中心-投放管理后台-v2)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngoy (生产-技术中心-猎户埋点系统-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngp3 (生产-技术中心-猎户投放API系统-v2-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngp4 (生产-技术中心-广告模块化后台-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngp0 (生产-技术中心-猎户投放API系统-v2-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngoz (生产-技术中心-猎户埋点系统-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cjyzb15c1h868ngov (生产-技术中心-增长平台统计服务-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=5.819866666666667, p95=5.998, max=6.162
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 5.706
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 5.508
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 5.712
  }
]
```

### i-bp1cjyzb15c1h868ngp1 (生产-技术中心-猎户埋点系统-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1347ba9krweikkcy76 (生产-保险-hzb前端-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 407.369
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 415.002
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 403.884
  }
]
```

### i-bp1a6vx1xwu7w3h4ckng (生产-保险-大保健接口-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp147of4lcxkuehklrv5 (生产-保险-大保健接口-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11l1b68410ptcegaf1 (生产-保险-大保健接口-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1gnel1od4hjlqqs6io (生产-平台支撑-审计-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1chhmo70ir913j3nnt (生产-健康-大病社区系统-004)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1518pfyn1hmowwuak7 (生产-技术中心-redis代理-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ic9ggky8lvys5fp11 (生产-技术中心-技术中心静态资源-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=5.507733333333333, p95=5.694, max=5.813
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 5.274
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 5.694
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 5.575
  }
]
```

### i-bp14u1jmuziltq5rujph (预发布-健康-diagnose-007)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ad1jbc6fv9jik70ho (预生产-保险-pre-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp133l0ge76s5rsd4jwy (生产-保险-xhb-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp121qc3k5s4jttaghej (生产-健康-diagnose-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "IntranetOutRate": 881.744
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 886.838
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 886.063
  }
]
```

### i-bp1gyurl0fqb3dusuu47 (测试-技术中心-用户增长01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=8.626933333333334, p95=9.171, max=9.254
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 8.533
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 9.097
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 8.77
  }
]
```

### i-bp14q2ifhxqa7zzn7pfa (生产-健康-diagnose-000)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1144kizck7ocn5e53h (生产-健康-reportanalysis-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp179fiyxxjf8roipd0m (生产-技术中心-安卓打包-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1i7pizgcnsahzubsgl (测试-技术中心-代码审计工具测试-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1e222edw5m1acmd5qq (测试-技术中心-性能测试-salve-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp115g8xflx2nnceemdz (生产-大数据-数据服务-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp177w0ffs0e9atako4t (生产-大数据-数据服务-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18mr52zr78odr6b0o2 (生产-健康-大病社区系统-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=7.797266666666667, p95=8.457, max=9.006
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:45:00Z",
    "CPU": 7.447
  },
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 7.561
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 6.996
  }
]
```

### i-bp158njg5gof4ynp1heb (生产-健康-大病社区系统-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1cy8o56jfgp1e4bpra (生产-大数据-收集各个业务目标指标-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1c8l3lmbvt4traq45w (生产-会员-nginx-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp11fj7q5onlgepn8znk (生产-会员-nginx-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp18o21sxum8elrf3jp5 (生产-保险-zk-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1ddn3qllt2s2vn5luz (生产-保险-zk-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15nyxaowfshuzv4j6y (生产-保险-zk-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp16589vyznk7kfx7lw0 (生产-平台支撑-openvas-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=11.205, p95=11.458, max=11.519
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 11.324
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 11.178
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "CPU": 11.161
  }
]
```

### i-bp1fwaqhukrqfv2y5y28 (预生产-保险-ebao-pre-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fs05owv1989akem2z (生产-健康-前端-管理后台-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 981.437
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 938.852
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetOutRate": 987.87
  }
]
```

### i-bp1beg1ta2kgg1rqe9ow (生产-健康-前端-管理后台-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hcjozmtbnu0zfy3hg (测试-平台支撑-dns-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp17odtp89dq79k9vv0r (生产-平台支撑-logstash及监控脚本-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19qee7e1l6z0932a7n (生产-火箭-提供http服务-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=14.424000000000001, p95=15.122, max=15.603
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "CPU": 13.956
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "CPU": 14.009
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "CPU": 13.674
  }
]
```

### i-bp1czr4eg9vz4ftdbrbz (生产-火箭-提供http服务-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp158puzt0ehz62x95ml (生产-通用-scripts)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15pjtwp4uldoh9vfco (生产-保险-nexus-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 11057.425
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 11177.984
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetOutRate": 10850.304
  }
]
```

### i-bp1e0ge3ve4rbvmyy4kq (预生产-微爱-审核后台-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp168brirm09c65i9uai (生产-技术中心-nginx-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1hl07s537rvk1tb6vk (生产-技术中心-nginx-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 58852.42
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 58536.345
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetOutRate": 51673.224
  }
]
```

### i-bp10e7wqn5qnxznm84py (生产-微爱-及时推送-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 18136.541
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 19283.831
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetOutRate": 22477.755
  }
]
```

### i-bp194ugtc493hhwqyn17 (生产-技术中心-火箭管理后台)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1h77gicvef96s68pja (生产-平台支撑-vpc-zabbix监控)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp13kv4jghysw50f0yw8 (生产-平台支撑-堡垒机-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp149dsj767oo3lwavcp (生产-微爱-阳光链-前端-01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp149dsj767oo3lwavco (生产-微爱-阳光链-前端-02)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1i4relv9vc2p03cjzq (生产-大数据-存放医疗数据-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19n4qr1yt5a8x3l3d8 (测试-微爱-console_greencat-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1iqrlsldyut6j8qe7f (生产-会员-wechat-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12bxxhtwowtj90p0ui (测试-火箭-提供http服务编译)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1g85iprsk5f5wopksv (生产-微爱-vpc_go_beacon-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1g85iprsk5f5wopksw (生产-微爱-vpc_go_beacon-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 247.3
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 243.98
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetOutRate": 237.523
  }
]
```

### i-bp1g85iprsk5f5wopksx (生产-微爱-vpc_go_beacon-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 18899.353
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 20795.801
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetInRate": 18987.007
  }
]
```

### i-bp10lxdukyobcacz1zyn (生产-微爱-vpc_etcd-003)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetOutRate": 294.854
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetOutRate": 339.255
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetOutRate": 311.285
  }
]
```

### i-bp10lxdukyobcacz1zyp (生产-微爱-vpc_etcd-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp10lxdukyobcacz1zyo (生产-微爱-vpc_etcd-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp19cwe60vswkviczyzm (生产-微爱-console_greencat-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp14q0z29an7gpckmwvt (预生产-通用-pre_live-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1fbdvymohd9nu0fbwy (生产-微爱-前端公众号业务服务-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp12n6ep53tcdqp3v0d3 (生产-技术中心-代码审计服务器中心01)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1e3eitq8z3dv4c2nxu (生产-微爱-前端公众号业务服务-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp1iqd0bpfmnmbm20zyz (生产-平台支撑-git仓库-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-bp15nzoz9lk87b7fiq34 (生产-微爱-php_base-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-2341vxqio (生产-微爱-project-006)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-23ssjz0jo (生产-微爱-php_app_api-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-23udi3faq (生产-微爱-project-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 1019237.99,
    "IntranetOutRate": 226482.039
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 1012036.266,
    "IntranetOutRate": 224919.005
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetInRate": 1030924.561,
    "IntranetOutRate": 226449.954
  }
]
```

### i-23yp6itps (生产-微爱-www_qschou_com-001)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None

### i-23kboi171 (生产-微爱-www_qschou_com-002)
- 风险: low | 标记: {'cpu_p95_high': False, 'memory_high': False, 'disk_high': False}
- CPU: avg=None, p95=None, max=None
- 样例点: 
```json
[
  {
    "TimeStamp": "2025-09-17T00:46:00Z",
    "IntranetInRate": 192.843
  },
  {
    "TimeStamp": "2025-09-17T00:47:00Z",
    "IntranetInRate": 240.081
  },
  {
    "TimeStamp": "2025-09-17T00:48:00Z",
    "IntranetInRate": 306.314
  }
]
```
