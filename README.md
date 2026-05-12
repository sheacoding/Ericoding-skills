# Ericoding Skills — Claude Code Skills Marketplace

<p align="center">
  <img src="https://img.shields.io/github/stars/sheacoding/Ericoding-skills?logo=github&logoColor=white&labelColor=333&color=ffb700&style=for-the-badge" alt="stars" />
  &nbsp;
  <img src="https://img.shields.io/github/forks/sheacoding/Ericoding-skills?logo=github&logoColor=white&labelColor=333&color=3498db&style=for-the-badge" alt="forks" />
  &nbsp;
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2ecc71?style=for-the-badge&labelColor=333&logo=open-source-initiative&logoColor=white" alt="license" /></a>
  &nbsp;
  <img src="https://img.shields.io/badge/Version-1.3.0-blue?style=for-the-badge&labelColor=333" alt="version" />
</p>

<p align="center">
  <b>Eric 的 Claude Code Skills 合集 — 持续更新的 AI 工作流增强工具包</b>
  <br/>
  <sub>视频分镜提示词 | AI 图像生成 | 更多 Skills 持续开发中</sub>
</p>

---

## 快速开始

```bash
# 1. 添加 Ericoding Marketplace（一次性操作）
/plugin marketplace add sheacoding/Ericoding-skills

# 2. 安装你需要的 Skill
/plugin install seedance-storyboard@ericoding-skills
/plugin install ima2gen@ericoding-skills
```

## Skills 列表

| Skill | 命令 | 用途 | 版本 |
|-------|------|------|------|
| [seedance-storyboard](#-seedance-storyboard) | `/seedance-storyboard` | 即梦 Seedance 2.0 专业分镜提示词生成 | v1.2.0 |
| [ima2gen](#-ima2gen) | `/ima2gen` | AI 图像生成 — 智能提示词 + API 直接出图 | v1.0.0 |

---

## 更新 Skills

```bash
# 在 Claude Code 中运行 /plugin
# → Marketplaces 标签页 → ericoding-skills → Update marketplace
```

也可开启 **Enable auto-update**，每次启动自动获取最新版本。

---

## 🎬 seedance-storyboard

> 将任何想法转换成即梦 Seedance 2.0 专业分镜提示词

**安装：**

```bash
/plugin install seedance-storyboard@ericoding-skills
```

**使用：**

```bash
/seedance-storyboard
```

**核心能力：**
- 11 个视频品类快速定位（AI漫剧、真人短剧、产品广告、互动接龙等）
- 8 大高阶技法：四段式运镜公式、首尾帧变身、色调宣言、嵌入式对白
- 多模态语法支持（`@图片1`/`@视频1` 引用素材）
- 提示词硬性控制 ≤ 1000 字（平台截断限制）

**示例：**

```
你的想法：一个女孩在樱花树下跳舞

生成的提示词：
电影级写实风格，15秒，16:9宽屏，日落黄金时刻的温暖氛围

0-3秒：远景缓慢推近，海平线夕阳，女孩剪影站在沙滩上，裙摆被海风吹动
3-7秒：中景环绕镜头，女孩开始旋转起舞，长发和裙摆飞扬，夕阳逆光形成轮廓光
...
```

**更多示例** → [`skills/seedance-storyboard/README.md`](skills/seedance-storyboard/README.md)

> **Fork 说明**：本 skill 基于 [elementsix/elementsix-skills](https://github.com/elementsix/elementsix-skills) v1.1.0 深度强化，整合字节跳动《小云雀 x Seedance2.0 实测案例》官方达人手册。

---

## 🖼️ ima2gen

> AI 图像生成 — 智能构建提示词，直接调用 API 出图

> 💡 推荐使用 [apimart.ai](https://apimart.ai/register?aff=MmEW) 作为 API 服务商（注册即送额度）

**安装：**

```bash
/plugin install ima2gen@ericoding-skills
```

**使用：**

```bash
/ima2gen
```

**工作流程：**

1. 首次使用引导配置 API 服务商和 Key（保存本地，后续免填）
2. 描述图像内容 + 选择风格类别
3. 设置质量、比例、风格、保存路径
4. Claude 自动构建专业英文提示词并确认
5. 调用 API 生成图像，保存到指定路径

**支持的服务商：**

| 服务商 | 推荐理由 |
|--------|---------|
| [**apimart.ai**](https://apimart.ai/register?aff=MmEW)（默认） | 异步高清，支持 1k/2k/4k，gpt-image-2 |
| BEIMA AI | 国内可用，gpt-image-2，无需科学上网 |
| OpenAI 官方 | 官方渠道，gpt-image-1 |
| 任意 OpenAI-compatible 端点 | 自定义 base_url，CLI 自动探测请求格式 |

**支持的图像类别：**

人物/肖像 · 海报/设计 · 产品渲染 · 风景/环境 · 动漫/插画 · 摄影风格 · UI/界面 · 技术图表

**示例：**

```
你的需求：生成一张赛博朋克风格的城市夜景，用于壁纸

ima2gen 构建的提示词：
Neon-soaked rain-drenched cyberpunk cityscape at night, towering skyscrapers
with holographic advertisements in Chinese and Japanese, flying vehicles leaving
light trails, street level crowded with umbrella-carrying pedestrians, reflective
wet asphalt, electric blue and magenta color palette, cinematic ultra-wide angle,
hyperdetailed photorealistic, 8K resolution

→ 自动调用 API，图片保存到你指定的路径
```

---

## 📁 仓库结构

```
Ericoding-skills/
├── .claude-plugin/
│   └── marketplace.json                  # Marketplace 配置（skills 注册表）
├── CLAUDE.md                             # Claude Code 开发指南
├── README.md                             # 本文件
└── skills/
    ├── seedance-storyboard/              # Seedance 分镜提示词 skill
    │   ├── SKILL.md
    │   ├── README.md
    │   ├── quick-reference.md
    │   ├── templates/
    │   └── examples/
    └── ima2gen/                          # AI 图像生成 skill
        ├── SKILL.md
        ├── README.md
        ├── cli/
        │   ├── ima2gen.py                # Python CLI（API 调用）
        │   └── requirements.txt
        └── templates/                    # 8 类风格提示词模板
            ├── portrait.md / poster.md / product.md / landscape.md
            └── anime.md / photography.md / ui.md / technical.md
```

---

## 贡献

欢迎提交 Issue 和 PR。如果你有好的 Skill 想法，也欢迎讨论。

## 许可证

MIT License

---

## ⭐ Star History

<p align="center">
  <a href="https://star-history.com/#sheacoding/Ericoding-skills&Date">
    <img src="https://api.star-history.com/svg?repos=sheacoding/Ericoding-skills&type=Date" alt="Star History" width="800" />
  </a>
</p>
