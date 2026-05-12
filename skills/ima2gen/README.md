# ima2gen — AI 图像生成 Skill

将你的想法转化为精确的图像生成提示词，并自动调用 OpenAI-compatible API 生成图像。

## 安装

```bash
# 1. 添加 Ericoding Marketplace（如未添加）
/plugin marketplace add sheacoding/Ericoding-skills

# 2. 安装 ima2gen
/plugin install ima2gen@ericoding-skills
```

## 首次使用

```bash
/ima2gen
```

首次调用时会自动引导配置 API 服务商和 Key：

1. 选择服务商（BEIMA AI / OpenAI 官方 / 自定义）
2. 输入 API Key
3. 确认模型名称

配置保存在 `~/.config/ima2gen/config.json`，后续使用无需重复输入。

## 支持的服务商

| 服务商 | base_url | 推荐模型 |
|--------|----------|---------|
| **BEIMA AI**（推荐，国内可用） | `https://bmai.kun8.vip/v1` | `gpt-image-2` |
| OpenAI 官方 | `https://api.openai.com/v1` | `gpt-image-1` |
| 任意 OpenAI-compatible 端点 | 自定义 | 自定义 |

## 使用流程

```
/ima2gen
  ↓
1. 环境检查（自动）
2. 描述图像内容 + 选择风格类别 + 质量偏好
3. 选择画面比例 + 数量 + 保存路径
4. Claude 构建专业英文提示词（可确认/修改）
5. 调用 API 生成图像
6. 图像保存到指定路径
```

## 支持的图像类别

| 类别 | 适用场景 |
|------|---------|
| 人物 / 肖像 | 商业肖像、角色设计、古风人物、赛博朋克 |
| 海报 / 设计 | 活动海报、品牌物料、展览设计 |
| 产品渲染 | 电商主图、香水/数码/食品/服装 |
| 风景 / 环境 | 自然风光、城市夜景、极地极光、水墨山水 |
| 动漫 / 插画 | 吉卜力风、赛博朋克动漫、仙侠风格 |
| 摄影风格 | 胶片街拍、野生动物、建筑、长曝光 |
| UI / 界面 | App界面、仪表板、落地页、线框图 |
| 技术图表 | 架构图、流程图、思维导图、时间线 |

## 生成参数

| 参数 | 可选值 | 说明 |
|------|--------|------|
| quality | `standard` / `hd` | hd 质量更高但耗时稍长 |
| size | `1024x1024` / `1792x1024` / `1024x1792` | 方形 / 横版 / 竖版 |
| style | `vivid` / `natural` | 鲜艳生动 / 真实自然 |
| n | 1-4 | 单次生成数量 |

## 更新配置

切换服务商或更新 API Key：

```bash
python3 ~/.config/ima2gen/ima2gen.py setup
```

## 文件结构

```
skills/ima2gen/
├── SKILL.md                  # 核心 skill 逻辑
├── README.md                 # 本文件
├── cli/
│   ├── ima2gen.py            # Python CLI
│   └── requirements.txt      # 依赖列表
└── templates/
    ├── portrait.md           # 人物/肖像模板
    ├── poster.md             # 海报/设计模板
    ├── product.md            # 产品渲染模板
    ├── landscape.md          # 风景/环境模板
    ├── anime.md              # 动漫/插画模板
    ├── photography.md        # 摄影风格模板
    ├── ui.md                 # UI/界面模板
    ├── technical.md          # 技术图表模板
    └── cn_social_poster.md   # 中文社交媒体视觉海报模板
```

## 模板来源致谢

| 模板 | 来源 |
|------|------|
| `cn_social_poster.md` 中文社交媒体视觉海报 | [@iswangwenbin](https://x.com/iswangwenbin/status/2054008842321858747) |

## 凭证配置

**推荐：环境变量（不会被 git 追踪）**

```bash
# 写入 ~/.zshrc 或 ~/.bashrc
export IMA2GEN_API_KEY="your-api-key"
export IMA2GEN_BASE_URL="https://bmai.kun8.vip/v1"  # 可选，默认 BEIMA AI
export IMA2GEN_MODEL="gpt-image-2"                   # 可选
```

**备选：交互向导**（写入 `~/.config/ima2gen/config.json`，已被 .gitignore 排除）

```bash
uv run --with click --with rich --with requests \
  python3 skills/ima2gen/cli/ima2gen.py setup
```

## 依赖管理（uv）

使用 uv 运行，无需手动安装：

```bash
uv run --with click --with rich --with requests \
  python3 skills/ima2gen/cli/ima2gen.py --help
```

或通过 `pyproject.toml` 安装到虚拟环境：

```bash
cd skills/ima2gen/cli
uv sync
uv run ima2gen --help
```

## 许可证

MIT
