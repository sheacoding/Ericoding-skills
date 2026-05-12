# 中文社交媒体视觉海报模板

> 模板来源：[@iswangwenbin](https://x.com/iswangwenbin/status/2054008842321858747)

## 用途

适用于微信公众号封面、小红书图文、抖音封面、B站封面等中文社交媒体场景。拟人化动物主角 + 强冲击力排版，病毒式传播风格。

## 提示词结构公式

```
Ultra-high resolution Chinese social media visual poster. Theme: [主题]. Aspect ratio: [比例].

COMPOSITION: Asymmetric high-impact layout. Oversized main title text dominates the left side or visual center. [核心主体动物] positioned on the right as the key visual subject. Restrained radial lines or light rays behind the animal — dynamic but not distracting — locking visual focus on the title and animal expression. Maximum 3 auxiliary label tags, arranged neatly at the edges or bottom, never scattered.

TYPOGRAPHY: Main title in expressive Chinese calligraphy or cracked-texture bold black typeface — powerful, structured, zero distortion. Title characters have strong outer stroke or drop shadow for complete separation from background. All auxiliary small-text labels use standard bold sans-serif (黑体 Bold), embedded in solid flat-color rectangular chips (pure yellow or red) with clean edges — no overlap with complex background textures. Every Chinese character stroke must be razor-sharp and legible.

COLOR: Classic high-contrast palette — vermilion red, bright yellow, pure black, crisp white. Large deep-colored background neutralizes glare, achieving "eye-catching without blinding." Subtle vintage comic halftone dots or ink splatter accents add tactile depth.

ANIMAL: [核心主体动物] with hyper-anthropomorphized, exaggerated expression perfectly matching the theme emotion (ecstatic joy / wide-eyed shock / smug confidence). Ultra-detailed fur texture, vivid eyes.

BOTTOM: One clean summary tagline at the bottom as visual closure.

OUTPUT: Poster-grade resolution, artistic yet legible main title, clean auxiliary text with zero garbled characters, saturated unified style.
```

## 使用方式

将提示词中的三处变量替换后，使用 `--size` 传入比例，Claude 将其翻译为 API 支持的格式：

| 用户输入比例 | apimart `--size` |
|------------|-----------------|
| 16:9 / 横版 | `16:9` |
| 9:16 / 竖版 | `9:16` |
| 1:1 / 方形  | `1:1` |
| 3:2 / 5:2  | 近似选 `16:9` |

推荐参数：`--quality hd --resolution 2k --style vivid`

## 示例提示词（已填入变量）

**主题**：摸鱼摸到老板来了  
**核心主体动物**：柴犬  
**画面比例**：9:16

```
Ultra-high resolution Chinese social media visual poster. Theme: "Slacking off until the boss walks in". Aspect ratio: 9:16 vertical.

COMPOSITION: Asymmetric high-impact layout. Oversized main title "摸鱼警报" dominates left-center in cracked-texture bold black. Shiba Inu positioned right, hyper-anthropomorphized wide-eyed shock expression, paws frozen mid-type on a keyboard. Restrained radial white light rays behind the dog. Maximum 3 auxiliary label tags at bottom edge.

TYPOGRAPHY: Main title "摸鱼警报" in cracked metallic bold Chinese typeface, strong black outer stroke. Auxiliary labels "上班摸鱼" "老板突袭" "人在工位心在外" in bold sans-serif white text inside pure red rectangular chips with flat edges.

COLOR: Vermilion red and bright yellow on deep black background. Vintage comic halftone dot texture overlay on background. Ink splatter accents at corners.

ANIMAL: Shiba Inu — wide eyes at maximum size, mouth agape, ears pinned back, one paw still on laptop keyboard. Ultra-detailed fur, expressive glossy eyes conveying pure panic.

BOTTOM: Clean tagline "班味突然就来了" in white bold sans-serif on dark bar.

OUTPUT: Poster-grade, artistic main title, clean auxiliary text zero garbled characters, saturated vivid unified style.
```

## 关键防乱码原则

1. 辅助小字**必须**放入实色矩形色块内（纯黄 / 纯红 / 纯白底），不可直接叠加在纹理背景上
2. 主标题需指定 `outer stroke` 或 `drop shadow`，确保与背景分离
3. 动物神态描述越具体越好（如 `mouth agape, ears pinned back`），模型更容易生成准确表情
