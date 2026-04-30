# 原型方向与竞品参考

生成时间：2026-04-29

## 产品定位

当前项目不应该做成“普通 Kubernetes Dashboard + 聊天窗口”。更适合的定位是：

> 面向 SRE / 平台工程师的 AI 运维指挥台：用自然语言触发诊断，用工具执行取证，用拓扑和时间线解释原因，用审计和确认流约束风险。

## 参考产品

### Komodor

官网定位为 Autonomous AI SRE Platform，强调云原生基础设施的上下文可视化、快速故障排查和自动化运营。对本项目最有参考价值的是“问题上下文 + RCA + 操作建议”组合，而不是单纯罗列资源。

参考：

- https://komodor.com/
- https://komodor.com/blog/introducing-klaudiaai-redefining-kubernetes-troubleshooting/

### Grafana Kubernetes Monitoring

Grafana 的 Kubernetes Monitoring 强调指标、日志、troubleshooting tools 和 metrics status。对本项目的启发是：诊断界面要能显示“数据是否采集到了、缺的是哪一类信号”，否则 AI 结论没有可信度。

参考：

- https://grafana.com/docs/grafana-cloud/monitor-infrastructure/kubernetes-monitoring/configuration/troubleshooting/

### Datadog Kubernetes Monitoring

Datadog 强调开箱即用的 Kubernetes dashboard、集成云厂商/应用/安全信号。对本项目的启发是：K8s 和 ECS 不应该分成两个孤岛，应该在同一风险视图里关联 workload、node、instance、告警和调用链。

参考：

- https://www.datadoghq.com/solutions/kubernetes/

### Lens

Lens 是 Kubernetes IDE，核心价值是快速浏览多集群状态、进入资源详情、查看日志和执行常用操作。对本项目的启发是：运维工作台需要很强的“可导航性”，AI 对话不能替代资源浏览。

参考：

- https://lenshq.io/
- https://docs.k8slens.dev/k8slens/

### Portainer

Portainer 的 Kubernetes dashboard 以环境摘要、资源计数和多集群管理为主。对本项目的启发是：首页应先给出环境全局态势，包括 namespace、workload、service、ingress、secret、volume 等关键对象计数。

参考：

- https://docs.portainer.io/user/kubernetes/dashboard
- https://www.portainer.io/

### Kubernetes Dashboard

官方 Dashboard 能部署、排障、管理资源，提供应用和集群状态概览。对本项目的启发是：基础资源操作仍是底盘，但本项目应在其上增加 AI 取证、DingTalk 协同和审计。

参考：

- https://kubernetes.io/docs/tasks/web-ui-dashboard/

### Rootly / PagerDuty

Rootly 和 PagerDuty 更偏事故响应。它们的启发是：运维机器人不只回答问题，还应沉淀 incident timeline、action items、责任人、通知和复盘内容。

参考：

- https://rootly.com/
- https://docs.rootly.com/incidents
- https://docs.rootly.com/ai/ai
- https://www.pagerduty.com/platform/aiops/

## 原型设计原则

1. 第一屏是工作台，不是营销页。
2. 左侧导航固定承载高频模块：指挥台、拓扑、事故、自动化、审计、配置。
3. 中央区域以聊天/命令为入口，但每次回答都要暴露工具轨迹和证据。
4. 右侧是当前上下文：环境、风险、拓扑、下一步操作。
5. 下方保留事件时间线和自动化队列，让 DingTalk、巡检、告警和手动操作连起来。
6. 高危操作必须有清晰状态：只读、需确认、已审计、已回滚。
7. 视觉上采用深色专业工具风格，少用装饰，多用密度、层次、状态色和微交互感。

## 生成物

- `project_document/prototypes/ops-copilot-prototype.html`
