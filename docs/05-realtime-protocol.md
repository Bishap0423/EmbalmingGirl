# 实时通信协议

## 1. 传输

- HTTP：创建房间、加入房间、获取静态配置和健康检查。
- WebSocket：房间状态、游戏命令、定向事件和重连。
- 所有消息使用 UTF-8 JSON，并携带协议版本。

首版不使用 GraphQL。

当前实现端点：

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/rooms` | 创建房间并取得房主席位令牌 |
| `POST` | `/api/rooms/{id}/players` | 加入房间 |
| `PUT` | `/api/rooms/{id}/ready` | 设置准备状态 |
| `POST` | `/api/rooms/{id}/start` | 房主开始对局 |
| `GET` | `/api/rooms/{id}` | 获取按席位裁剪的重连快照 |
| `POST` | `/api/rooms/{id}/commands` | 提交游戏命令 |
| `WS` | `/ws/rooms/{id}?token=...` | 实时快照、命令和重连 |

HTTP 席位认证使用 `X-Player-Token`。令牌不得写入日志或玩家视图。

## 2. 消息信封

客户端到服务器：

```json
{
  "protocol_version": 1,
  "type": "command",
  "request_id": "01J...",
  "game_id": "01J...",
  "player_token": "secret",
  "expected_revision": 42,
  "payload": {
    "command": "play_suspicion",
    "card_instance_id": "card_17",
    "target_player_id": "player_2"
  }
}
```

服务器到客户端：

```json
{
  "protocol_version": 1,
  "type": "state_patch",
  "request_id": "01J...",
  "game_id": "01J...",
  "revision": 43,
  "visibility": "player",
  "payload": {}
}
```

## 3. 服务器消息类型

| 类型 | 用途 |
|---|---|
| `snapshot` | 首次连接或重连的完整玩家视图 |
| `state_patch` | 已投影的增量变化 |
| `decision_required` | 当前连接需要完成一个能力步骤 |
| `private_reveal` | 风纪委员、图书委员、秀才等私密结果 |
| `command_accepted` | 命令已持久化 |
| `command_rejected` | 非法命令、旧 revision 或权限错误 |
| `presence` | 玩家连接、离线、准备状态 |
| `game_finished` | 终局公开结果 |

## 4. 待决策结构

所有多步骤能力统一表示为：

```json
{
  "decision_id": "decision_9",
  "kind": "select_card",
  "actor_player_id": "player_1",
  "prompt_key": "ability.go_home.select_hand_card",
  "min": 1,
  "max": 1,
  "options": [
    {"value": "card_4", "label_key": "card.class_representative"}
  ],
  "private": true
}
```

- 服务端只下发该玩家有权知道的 options。
- 客户端返回 value，不返回显示文本。
- 同时选择能力为每名玩家创建独立私密 decision；全部完成后一次结算。
- 重连后未完成 decision 必须重新出现在 snapshot 中。

## 5. 错误码

| 错误码 | 含义 |
|---|---|
| `STALE_REVISION` | 客户端基于旧状态行动，应刷新 |
| `NOT_YOUR_TURN` | 非当前玩家提交回合动作 |
| `CARD_NOT_IN_HAND` | 牌不在该玩家手中 |
| `ACTION_NOT_ALLOWED` | 此牌或当前阶段不允许该动作 |
| `INVALID_TARGET` | 目标不合法 |
| `DECISION_NOT_FOUND` | 决策已完成、过期或不属于该玩家 |
| `GAME_ALREADY_FINISHED` | 对局已经结束 |

错误响应不得包含可推断隐藏牌的信息。例如犯人不能调合时，只返回通用的 `ACTION_NOT_ALLOWED`；客户端本来已知道自己的手牌，因此无需额外解释其他玩家信息。

## 6. 重连

玩家凭房间 ID 与不可猜测的 player token 重连：

1. 服务端关闭同一席位旧连接。
2. 返回当前 revision 的完整 `PlayerView`。
3. 恢复该席位有权查看的私密结果和未完成 decision。
4. 客户端丢弃本地旧状态。

## 7. 与未来模型的兼容

HTTP 可另外暴露与 WebSocket 同构的轮询端点：

- `GET /games/{id}/observation`
- `GET /games/{id}/legal-actions`
- `POST /games/{id}/commands`

这些端点仍要求席位 token，并复用相同的命令校验与玩家视图投影。
