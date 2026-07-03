# 卡牌目录

内部 ID 永不使用显示语言。中文名是当前开发译名，可在本地化文件中修改。

| ID | 日文名 | 中文开发名 | MP | 数量 | 优先级 | 胜利条件 |
|---|---|---|---:|---:|---:|---|
| `alien` | 宇宙人 | 宇宙人 | -1 | 1 | 1 | 自己被监禁 |
| `infected` | 感染者 | 感染者 | 0 | 1 | 2 | 调合失败 |
| `criminal` | 犯人 | 犯人 | 0 | 1 | 3 | 自己未被监禁 |
| `accomplice` | 共犯者 | 共犯者 | 0 | 3 | 3 | 犯人获胜 |
| `student_council_president` | 生徒会長 | 学生会长 | 3 | 1 | 4 | 调合成功 |
| `class_representative` | 学級委員 | 学级委员 | 2 | 2 | 4 | 调合成功 |
| `prodigy` | 秀才 | 秀才 | 2 | 1 | 4 | 调合成功 |
| `disciplinary_committee` | 風紀委員 | 风纪委员 | 1 | 1 | 4 | 调合成功 |
| `health_committee` | 保健委員 | 保健委员 | 1 | 2 | 4 | 调合成功 |
| `lady` | お嬢様 | 大小姐 | 1 | 1 | 4 | 自己未被监禁 |
| `library_committee` | 図書委員 | 图书委员 | 1 | 5 | 4 | 调合成功 |
| `newspaper_club` | 新聞部 | 新闻部 | 1 | 3 | 4 | 调合成功 |
| `go_home_club` | 帰宅部 | 归宅部 | 0 | 3 | 5 | 更高优先级无人获胜 |

总数：25。

## 能力定义

| ID | 能力 |
|---|---|
| `alien` | 持有期间，面对秀才能力时可假装犯人回应；主动使用无效果 |
| `infected` | 自己下个回合开始时，若该牌仍在自己的 `USED`，从调合区取回一张牌 |
| `criminal` | 不能主动打出，只能被其他能力移动 |
| `accomplice` | 将某玩家的一张疑惑牌转移至另一名玩家 |
| `student_council_president` | 持有者成为首位玩家；主动使用无效果 |
| `class_representative` | 选择另一玩家，双方各暗选一张手牌并交换 |
| `prodigy` | 私密识别犯人；宇宙人可以制造假信号 |
| `disciplinary_committee` | 私密查看另一名玩家全部手牌 |
| `health_committee` | 将另一玩家 `USED` 中一张非保健委员牌加入自己手牌 |
| `lady` | 从另一玩家手牌随机抽一张，再暗置返还一张；可返还刚抽到的牌 |
| `library_committee` | 私密查看调合区全部牌，保持原顺序 |
| `newspaper_club` | 所有合格玩家各暗选一张手牌，同时传给左侧下一名合格玩家 |
| `go_home_club` | 自己一张剩余手牌与调合区一张牌交换 |

## 建议数据结构

卡牌定义放在版本化数据文件中，实例 ID 由开局创建：

```json
{
  "schema_version": 1,
  "id": "class_representative",
  "mp": 2,
  "copies": 2,
  "victory_priority": 4,
  "ability": "exchange_one_card",
  "victory": "embalming_succeeded",
  "art_key": "card.class_representative"
}
```

能力和胜利条件只允许引用引擎注册表中的稳定键，禁止从字符串执行任意 Python。
