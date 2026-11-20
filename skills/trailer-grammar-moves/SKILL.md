---
name: trailer-grammar-moves
description: "Remotion motion shot card 'trailer grammar moves' (opening、transition). 预告片语法一式——trailer-bumper 前置速剪钩子：三镜 9f 速剪 + 黑场静默一拍，再开场标题。适用: 预告片的开场钩子（cold open）：正片前先塞三个最抓眼的镜头，再静默一拍正式开场. Use when the user asks for the trailer-grammar-moves effect/shot, or a video/reel/promo moment that fits it (حركة موشن جاهزة: trailer grammar moves)."
---

# trailer-grammar-moves

Motion recipe card + tuned Remotion reference implementation, packaged as a
standalone skill. Original card text is Chinese (kept verbatim below so frame
counts and parameters stay exact).

| Field | Value |
|---|---|
| One-liner (一句话) | 预告片语法一式——trailer-bumper 前置速剪钩子：三镜 9f 速剪 + 黑场静默一拍，再开场标题 |
| Best for (适用) | 预告片的开场钩子（cold open）：正片前先塞三个最抓眼的镜头，再静默一拍正式开场 |
| Duration (时长) | A ~4.7s（140f） |
| Energy (能量) | A 高 |
| Category (标签) | opening、transition |

## How to use

1. Read the whole card below before writing code (intent → motion core → parameter table).
2. Needs **Remotion 4 + React 19** (FFmpeg for checks). Copy the `demos/` folder from this
   skill into your Remotion project's `src/` so relative imports (`../../_fixtures/...`) resolve.
3. Register the component in `Root.tsx` as a `<Composition>` (1920×1080 @ 30fps unless the
   card says otherwise) and render with `npx remotion render <id> out.mp4`.
4. Swap placeholder copy, colors (`_fixtures/Brand.tsx`) and screenshots for the user's own.
5. Live preview gallery: https://vincentwei1021.github.io/video-shotcraft/

### Files
- `demos/rhythm/trailer-grammar-moves/TrailerBumper.tsx`

---

## Card (original)

## 意图
库内节奏卡各管一段：beat-cut 管切点排布、rhythm-interrupt 管打断。
本卡管**预告片的结构性时刻**——不是某个
镜头怎么动，是整片的关节怎么接：A 是开场钩——正片前 0.9 秒塞
三个最抓眼镜头速剪 + 黑场静默一拍再开场，预告片的"预告"。

## 式选型
| 式 | 做法 | 适用 |
|----|------|------|
| A trailer-bumper | 三镜头各 9f 等长硬切（0/9/18），每镜内部 scale 1→1.04 微推保活；27–33f 纯黑静默，33f 起标题 16f 淡入 + 44px out-cubic 微升（demo 标题是 video-shotcraft 字标 + 品牌 tagline） | 正片开场前的钩子；cold open |

## 参数表
| 参数 | 典型值 | 调节手感 |
|------|--------|----------|
| A 速剪 | 三镜等长 9f，零过渡；镜头 3 对焦中列 Top pages 卡放大 2.2x 怼脸特写（CSS zoom，字不糊） | 节拍感靠等长；三镜构图必须明显不同 |
| A 微推 | 每镜内部 scale 1→1.04 线性 | 静帧三连读作幻灯片——命门 |
| A 黑场 | 27–33f 纯黑 #000 空 div，6f | 黑场里放任何东西都毁掉"静默一拍" |
| 收尾 | A 静止 77f（≥40f） | 字距收拢完（63f）后整帧冻结，真静止 |

## 已知坑
- demo 在灰阶/占位素材上调校通过——参数是调校起点非实战定稿，
  首次实战须以真实素材回验
- A 黑场必须纯黑无物（drop-blackout 判例同族）——黑场是喘息，
  不是又一张字卡
- A 三连切每切一声打点、黑场全消音（sound-design §4.5）

## 参考实现
demos/rhythm/trailer-grammar-moves/
（TrailerBumper.tsx）


---
Source: [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) by Vincentwei1021,
Apache License 2.0 (see `LICENSE`). Repackaged as a standalone skill; content unmodified.
