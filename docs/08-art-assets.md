# 美术资源契约

## 1. 使用策略

`Embalming_Girl_(Rules-English).pdf` 中的卡图只用于本地开发、规则验证和布局占位。它们不得被视为项目自有美术，也不应进入公开发行包。

正式素材由画师交付后，通过资源清单切换。规则代码、卡牌 ID 和网络协议不引用具体文件名。

## 2. 目录约定

```text
assets/
├── temporary/
│   └── source-pdf/             # 本地临时提取；默认不进入发行物
├── production/
│   ├── cards/
│   ├── board/
│   ├── ui/
│   └── audio/
├── manifest.development.json
└── manifest.production.json
```

是否将临时提取文件提交 Git，在 M0 根据仓库公开范围决定；默认建议忽略，只保留提取脚本和来源说明。

## 3. 稳定资源键

每种角色至少提供：

```text
card.alien.front
card.alien.thumbnail
```

公共资源：

```text
card.common.back
board.corpse
board.background
ui.suspicion_marker
ui.embalming_marker
```

前端从 manifest 解析资源键：

```json
{
  "manifest_version": 1,
  "asset_set": "temporary-pdf",
  "assets": {
    "card.alien.front": {
      "src": "/assets/temporary/cards/alien.webp",
      "width": 445,
      "height": 622,
      "status": "temporary",
      "source": "Embalming_Girl_(Rules-English).pdf"
    }
  }
}
```

## 4. 卡牌交付规格

- 推荐画布比例：沿用原卡约 `445:622`，组件使用 `aspect-ratio`，不依赖固定像素。
- 主文件：分层源文件由美术团队保存。
- Web 交付：WebP 或 PNG，sRGB。
- 建议尺寸：正面至少 890×1244；缩略图可由构建流程生成。
- 安全区：关键文字和人物不得紧贴裁切边。
- 卡面文字建议由 Web UI 叠加，而不是烘焙进图片，以支持中文修订、无障碍和未来多语言。
- 美术只负责底图、角色与装饰；MP、名称、能力、优先级和胜利条件来自卡牌数据。

## 5. 替换验收

正式资源切换必须满足：

- `manifest.production.json` 不引用 `temporary/`。
- 每个 `art_key` 都存在文件、尺寸正确且可加载。
- 缺失资源显示统一占位图，不导致游戏无法进行。
- 替换 manifest 后，后端测试结果和对局回放哈希不变。
- 发行构建自动检查并拒绝包含 `status: temporary` 的资源。

## 6. 来源记录

每套资源记录：

- 作者或来源
- 许可范围
- 获取或交付日期
- 是否允许修改、公开发布和商业使用
- 对应版本与文件校验和

该记录是工程追踪要求，不代替法律判断。
