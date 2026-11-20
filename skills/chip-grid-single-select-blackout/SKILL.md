---
name: chip-grid-single-select-blackout
description: "Remotion motion shot card 'chip grid single select blackout' (). 五个选项 chip 以 3+2 居中排布逐个淡入；选中帧先插一帧灰色按压块，紧接数帧内底色变墨黑、文字变白并做 1→1.04→1 极轻回弹，其余 chip 淡到 18% 但位置锁死；随后余项归零，黑 chip 上移收窄，下方升起结算价格。适用: 单选/套餐/档位选择的交互演示；\"选了它之后会怎样\"的因果镜头；价格/参数结算类链路. Use when the user asks for the chip-grid-single-select-blackout effect/shot, or a video/reel/promo moment that fits it (حركة موشن جاهزة: chip grid single select blackout)."
---

# chip-grid-single-select-blackout

Motion recipe card + tuned Remotion reference implementation, packaged as a
standalone skill. Original card text is Chinese (kept verbatim below so frame
counts and parameters stay exact).

| Field | Value |
|---|---|
| One-liner (一句话) | 五个选项 chip 以 3+2 居中排布逐个淡入；选中帧先插一帧灰色按压块，紧接数帧内底色变墨黑、文字变白并做 1→1.04→1 极轻回弹，其余 chip 淡到 18% 但位置锁死；随后余项归零，黑 chip 上移收窄，下方升起结算价格 |
| Best for (适用) | 单选/套餐/档位选择的交互演示；"选了它之后会怎样"的因果镜头；价格/参数结算类链路 |
| Duration (时长) | 约5.5s（165f@30fps） |
| Energy (能量) | 中低（唯一的爆点是那一帧灰闪，其余都在收） |
| Category (标签) |  |

## How to use

1. Read the whole card below before writing code (intent → motion core → parameter table).
2. Needs **Remotion 4 + React 19** (FFmpeg for checks). Copy the `demos/` folder from this
   skill into your Remotion project's `src/` so relative imports (`../../_fixtures/...`) resolve.
3. Register the component in `Root.tsx` as a `<Composition>` (1920×1080 @ 30fps unless the
   card says otherwise) and render with `npx remotion render <id> out.mp4`.
4. Swap placeholder copy, colors (`_fixtures/Brand.tsx`) and screenshots for the user's own.
5. Live preview gallery: https://vincentwei1021.github.io/video-shotcraft/

### Files
- `demos/interaction/chip-grid-single-select-blackout/ChipGridSingleSelectBlackout.tsx`

---

## Card (original)

## 意图
一帧灰闪 + 三帧反黑，是把真实 UI 的 `:active → :selected` 两级状态
拆开演。观众看到的是"手指按下"再"系统确认"，而不是一次渐变。其余
chip 降到 18% 而**位置绝不移动**：一旦重排，观众会以为页面刷新了，
"单选"的语义就丢了。

## 动效核心
- 5 个 chip 分 3+2 两行居中（1080p 原生：高 96、圆角 48、gap 22、36px 字，固定宽 346/364/476/236/330），
  8f 起按 3f 间隔 snappy 升起；上方眉题 + 84px 问句先到
- 光标 26–54f 从右下走 swift 弧线移到目标 chip（因果预告），56f 按下
- **1 帧按压灰闪**：仅 FS=56 这一帧，`rgba(120,128,146,.5)` 覆盖层
- **反黑**：57→62f linear（5 帧）驱动背景 白→墨黑 `#0b1020`、描边、文字 墨→白，同时 ✓ 从 0 宽长出
- **按压回弹**：`sc = 1 + sin(pr·π)*0.04`，pr 走 57→66f——正弦保证起止都精确回到 1
- **余项降级**：57→66f outQuad 把 opacity 压到 18%，`transform` 恒为 `none`
- 主角光：反黑后 chip 底下亮一圈极淡钴蓝落地光（只给主角一次），阴影随抬升变深变大
- **收束**：101f 起（选中后≈1.5s）余项 9f 归零；黑 chip 18f smooth 上移到 y=330、scale→0.88、
  横向回中线（几何由固定宽算出，不运行时测量）；问句同时上移淡出让位
- 结算：108f 原价 $42.00 升起 → 118f 一道划线划掉并退灰 → 116f 起现价 $34.44 逐字升起（180px）
  → 128f 钴蓝「Save 18% · billed $413.28 yearly」overshoot 弹出；134–165f hold

## 参数表
| 参数 | 典型值 | 调节手感 |
|------|--------|----------|
| 入场 | 8f 起、间隔 3f、各 16f snappy | 5 个 chip 在 1s 内铺完，把时间留给选中段 |
| 选中时刻 | FS = 56f（约全片 1/3） | 前段读题、后段看结果；早于 40f 观众还没读完选项 |
| 灰闪 | 1 帧，rgba(120,128,146,.5) | **就一帧**：给 2 帧以上就读作 hover 高亮，不是按下 |
| 反黑 | 57→62f linear（5f） | linear 是故意的：加 ease 会让"变黑"这件事有过程感，太软 |
| 按压回弹 | 1 + sin(pr·π)·0.04，跨 9f | 0.04 是极轻；到 0.1 就成了弹跳按钮，抢戏 |
| 余项降级 | 降到 18%，位置 transform:none | **位置锁死是命门**：降到 18% 仍在原位，才读作"没被选中"而非"消失了" |
| 收束时刻 | 101f（选中后≈1.5s）起，18f smooth in-out | 1.5s 是让观众看清选中态的最短驻留；缩到 0.5s 就赶 |
| 上移收窄 | 到 y=330、scale→0.88，横向补回中线 | 不补中线的话上移后会偏在左边，读作"被拖走"；缩过 0.85 字低于 32px |
| 结算顺序 | 原价 → 划线 → 现价 → 省额胶囊，间隔 8–10f | 先给旧价再划掉，观众才读得到"变便宜了"的因果 |

## 已知坑
- 选中 chip 的回中线位移由固定 chip 宽算出（不运行时测量 offsetWidth）——改文案时要同步改宽度表，
  否则字溢出或上移后偏离中线
- 其余 chip 的 `transform` 必须显式写 `'none'`，不能靠 flex 自动重排，否则余项归零时会横向滑动
- 占位内容：5 条计费周期选项名（Annual billing … Nonprofit rate）+ 结算「$42.00 → $34.44/mo、Save 18%」，
  落地全部替换；选项名过长会撑破固定宽（第三条 "Two-year commitment" 是长名压力测试）

## 参考实现
demos/interaction/chip-grid-single-select-blackout/
（ChipGridSingleSelectBlackout.tsx）


---
Source: [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) by Vincentwei1021,
Apache License 2.0 (see `LICENSE`). Repackaged as a standalone skill; content unmodified.
