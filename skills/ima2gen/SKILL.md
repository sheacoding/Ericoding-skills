---
name: ima2gen
description: 当用户需要生成图片、AI作图、文生图、画图、image generation、制作图像时调用。自动引导构建专业提示词并调用 API 生成图像。支持人物/海报/产品/风景/动漫/摄影/UI/技术图表等多种风格。
disable-model-invocation: false
---

# ima2gen — AI 图像生成助手

## 工作流程

你是一个图像生成专家助手，帮助用户通过精确的提示词调用 OpenAI-compatible API 生成高质量图像。

---

## Step 1：凭证检查与首次配置

**CRITICAL**：skill 启动后，立即用 Bash 检查凭证是否存在：

```bash
test -f ~/.config/ima2gen/config.json && echo "configured" || echo "not_configured"
```

### 已配置 → 直接进入 Step 2

### 未配置 → 用 AskUserQuestion 引导用户完成配置（**全程在对话框内完成，无需用户手动执行命令**）

```javascript
AskUserQuestion({
  questions: [
    {
      question: "请选择图像生成 API 服务商",
      header: "服务商",
      multiSelect: false,
      options: [
        {
          label: "BEIMA AI（推荐）",
          description: "国内可用，无需科学上网，模型 gpt-image-2，填入 BEIMA AI Key 即可"
        },
        {
          label: "OpenAI 官方",
          description: "需科学上网，模型 gpt-image-1，填入 OpenAI API Key"
        },
        {
          label: "自定义端点",
          description: "任意 OpenAI-compatible 服务，自行填写 base_url 和 Key"
        }
      ]
    },
    {
      question: "请粘贴你的 API Key",
      header: "API Key",
      multiSelect: false,
      options: [
        { label: "粘贴 Key", description: "在下方「其他」输入框中粘贴你的 API Key" }
      ]
    }
  ]
})
```

收到用户填写的 API Key 后，根据选择的服务商确定 `base_url` 和 `model`：

| 服务商 | base_url | model |
|--------|----------|-------|
| apimart.ai | `https://api.apimart.ai/v1` | `gpt-image-2` |
| BEIMA AI | `https://bmai.kun8.vip/v1` | `gpt-image-2` |
| OpenAI 官方 | `https://api.openai.com/v1` | `gpt-image-1` |
| 自定义 | 再问一次 base_url | `gpt-image-2` |

**自定义端点时额外问：**
```javascript
AskUserQuestion({
  questions: [
    {
      question: "请输入自定义 API 端点（base_url）",
      header: "base_url",
      multiSelect: false,
      options: [
        { label: "输入端点", description: "如 https://your-proxy.com/v1" }
      ]
    }
  ]
})
```

**收集完毕后，Claude 用 Write 工具写入配置文件（不执行任何交互式 shell 命令）：**

```
写入路径：~/.config/ima2gen/config.json
内容：
{
  "api_key": "<用户填写的 Key>",
  "base_url": "<对应服务商的 URL>",
  "model": "<对应模型名>"
}
```

写入成功后，告知用户配置已保存，继续 Step 2。

---

## Step 2：收集生图需求（AskUserQuestion — 第一轮）

**CRITICAL**：使用 AskUserQuestion 工具，一次性问 3 个问题：

```javascript
AskUserQuestion({
  questions: [
    {
      question: "你想生成什么样的图像？请描述核心内容",
      header: "图像描述",
      multiSelect: false,
      options: [
        { label: "我来描述", description: "我会在下方输入自定义描述" }
      ]
    },
    {
      question: "图像的风格类别是什么？",
      header: "风格类别",
      multiSelect: false,
      options: [
        { label: "人物 / 肖像", description: "人物写真、商业肖像、角色设计" },
        { label: "海报 / 设计", description: "活动海报、品牌设计、排版作品" },
        { label: "产品渲染", description: "商品展示、电商主图、3D产品图" },
        { label: "风景 / 环境", description: "自然风光、城市景观、概念场景" },
        { label: "动漫 / 插画", description: "日漫、国漫、概念艺术插画" },
        { label: "摄影风格", description: "模拟真实摄影效果，胶片/数码" },
        { label: "UI / 界面", description: "App界面、网页设计、数据面板" },
        { label: "技术图表", description: "架构图、流程图、信息可视化" }
      ]
    },
    {
      question: "图像质量和风格偏好？",
      header: "质量 & 风格",
      multiSelect: false,
      options: [
        { label: "HD + 鲜艳生动（推荐）", description: "高清质量，色彩饱满有冲击力，适合大多数场景" },
        { label: "HD + 真实自然", description: "高清质量，色调真实克制，适合摄影和写实图" },
        { label: "标准 + 鲜艳生动", description: "标准质量，生成更快，成本更低" },
        { label: "标准 + 真实自然", description: "标准质量，真实色调，快速预览用" }
      ]
    }
  ]
})
```

---

## Step 3：收集输出参数（AskUserQuestion — 第二轮）

```javascript
AskUserQuestion({
  questions: [
    {
      question: "图像的画面比例？",
      header: "画面比例",
      multiSelect: false,
      options: [
        { label: "1:1 方形", description: "社交媒体头像/贴子，通用" },
        { label: "16:9 横屏", description: "桌面壁纸/横版海报/风景图" },
        { label: "9:16 竖屏", description: "手机壁纸/竖版海报/人物图" }
      ]
    },
    {
      question: "生成几张？",
      header: "生成数量",
      multiSelect: false,
      options: [
        { label: "1 张（推荐）", description: "快速生成，先看效果" },
        { label: "2 张", description: "对比两个方向" },
        { label: "4 张", description: "批量生成，从中挑选最佳" }
      ]
    },
    {
      question: "图片保存到哪个路径？",
      header: "保存路径",
      multiSelect: false,
      options: [
        { label: "当前目录 output.png", description: "保存到当前工作目录，文件名 output.png" },
        { label: "桌面 output.png", description: "保存到 ~/Desktop/output.png" },
        { label: "自定义路径", description: "我来指定完整路径（在下方输入）" }
      ]
    }
  ]
})
```

---

## Step 4：构建专业提示词（Claude 内部推理）

根据用户选择的风格类别，**在内部推理中**参考以下对应的模板结构：

| 风格类别 | 提示词结构公式 |
|---------|--------------|
| 人物/肖像 | `[lighting], [shot type] portrait of [subject], [clothing], [background], [style], [mood], [quality]` |
| 海报/设计 | `[layout] poster for [purpose], [main visual], [typography], [color palette], [style reference]` |
| 产品渲染 | `[shot type] product photography of [product], [material], [background], [lighting], [brand aesthetic]` |
| 风景/环境 | `[time of day] [weather], [landscape type] with [features], [foreground], [lighting], [style], [mood]` |
| 动漫/插画 | `[style reference], [character description], [scene], [action/pose], [lighting], [color palette]` |
| 摄影风格 | `[genre] photography, [subject], [location], [camera/lens], [film type], [lighting], [composition]` |
| UI/界面 | `[UI type] design for [product], [screen name], [design system], [components], [color theme], [device]` |
| 技术图表 | `[diagram type] for [system], [components], [flow direction], [visual style], [color scheme]` |

### 提示词构建原则（CRITICAL）

1. **语言**：最终提示词使用**英文**（GPT Image 对英文效果显著优于中文）
2. **结构**：按公式逐层填入用户的描述内容，补充专业细节
3. **长度**：100-300 词为最佳，过长会降低连贯性
4. **细节层次**：
   - 主体描述（who/what）→ 环境背景（where）→ 光线氛围（how it looks）→ 风格指向（artistic reference）→ 质量词（resolution/detail）
5. **禁止堆砌**：避免无意义地叠加形容词，每个词都应有具体含义

### 展示和确认

构建完成后，向用户展示：

```
📝 即将使用的提示词：

[完整英文提示词]

⚙️ 生成参数：
- 质量：[quality]   比例：[size]   风格：[style]   数量：[n]
- 保存至：[output path]

是否确认生成？（或告诉我如何调整提示词）
```

---

## Step 5：调用 CLI 生成图像（Bash）

用户确认后，运行：

```bash
uv run --with click --with rich --with requests \
  python3 ~/.config/ima2gen/ima2gen.py generate \
  --prompt "[构建好的英文提示词]" \
  --quality [standard|hd] \
  --size [1:1|16:9|9:16] \
  --resolution [1k|2k|4k] \
  --style [vivid|natural] \
  --output "[完整保存路径]" \
  --n [1|2|4]
```

**注意：`--resolution` 仅 apimart.ai 支持，BEIMA AI / OpenAI 请省略该参数。**

**路径映射：**
- "当前目录 output.png" → `$(pwd)/output.png`（或用当前对话工作目录）
- "桌面 output.png" → `~/Desktop/output.png`
- "自定义路径" → 用户输入的路径

---

## Step 6：展示结果 & 迭代

生成成功后：

1. 告知用户图片保存路径
2. 提供迭代建议：
   - 想调整风格或内容？→ 告诉我修改方向，重新生成
   - 想生成更多变体？→ 可以保持提示词，再生成 2-4 张对比
   - 想切换比例？→ 可以换 size 参数

---

## 重置配置

如果用户想换服务商或更新 API Key，重新走 Step 1 的 AskUserQuestion 流程，覆盖写入 `~/.config/ima2gen/config.json` 即可。

---

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 依赖未安装 | uv 会自动按需安装，无需用户手动操作 |
| API 认证失败 | 重新走 Step 1 配置流程，覆盖 Key |
| 模型不支持该参数 | 去掉 `--style` 或 `--quality` 参数重试（部分服务商不支持） |
| 输出目录不存在 | CLI 会自动创建父目录，否则提示用户检查路径权限 |
| rate limit / quota | 提示等待或切换服务商 |
