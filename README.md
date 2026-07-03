# Embalming Girl

《冰冷的她醒来之前》（Embalming Girl）的本地数字化开发项目。

项目目标是建立一个以 Python 为权威规则引擎、Web 为显示与交互界面的游戏平台，并为后续接入大语言模型保留稳定的“观察—合法行动—事件”接口。本阶段不实现任何模型调用。

## 当前状态

- 阶段：M3 终局、回放与属性测试完成，下一阶段为 M4 本地房间与实时服务
- 规则来源：
  - `Embalming_Girl_(Rules_-_JP).jpg`：日文官方规则书，规则裁定的主要依据
  - `Embalming_Girl_(Rules-English).pdf`：英文规则与卡图，角色数据和开发期临时素材来源
- 代码：已实现核心回合、13 种角色能力、终局优先级、事件回放、状态哈希与不变量检查
- 美术：PDF 卡图仅作为开发期临时资源，正式资源将独立替换

## 文档导航

- [范围与原则](docs/01-product-scope.md)
- [规则规格](docs/02-rules-spec.md)
- [卡牌目录](docs/03-card-catalog.md)
- [技术架构](docs/04-architecture.md)
- [通信协议](docs/05-realtime-protocol.md)
- [开发里程碑](docs/06-milestones.md)
- [测试策略](docs/07-testing-strategy.md)
- [美术资源契约](docs/08-art-assets.md)

## 计划技术栈

- Python 3.12、FastAPI、Pydantic、pytest
- React、TypeScript、Vite
- WebSocket 实时通信
- JSON/JSONL 对局快照与事件回放

具体版本在 M0 建库时锁定。
