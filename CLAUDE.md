# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库定位

这是 **Ericoding Skills** 的分发平台（marketplace）。通过 Claude Code 的 `/plugin` 系统，用户可以安装和使用这里发布的 skills。当前已有两个 skill：

| Skill | 触发命令 | 用途 |
|-------|---------|------|
| `seedance-storyboard` | `/seedance-storyboard` | 即梦 Seedance 2.0 分镜提示词生成器 |
| `ima2gen` | `/ima2gen` | AI 图像生成：引导构建提示词并调用 OpenAI-compatible API 生图 |

## 关键配置文件

- `.claude-plugin/marketplace.json` — marketplace 入口，控制整个 marketplace 的元数据和 plugins 列表。每新增一个 skill，必须在 `plugins` 数组中注册它。
- `skills/<skill-name>/SKILL.md` — skill 的核心逻辑文件，frontmatter 中的 `name` 字段决定触发命令（`/<name>`）。

## Skill 的结构规范

每个 skill 目录应包含：

```
skills/<skill-name>/
├── SKILL.md          # 核心逻辑（必须），frontmatter 含 name/description
├── README.md         # 面向用户的说明
├── quick-reference.md  # 快速参考（可选）
├── templates/        # 模板文件（可选）
└── examples/         # 示例（可选）
```

SKILL.md 的 frontmatter 格式：
```yaml
---
name: <skill-name>          # 对应触发命令 /<skill-name>
description: <触发时机描述>
disable-model-invocation: false
---
```

## 新增 Skill 的流程

1. 在 `skills/` 下创建新目录，按上述结构组织文件
2. 在 `.claude-plugin/marketplace.json` 的 `plugins` 数组中注册：
   ```json
   {
     "name": "<skill-name>",
     "description": "<描述>",
     "version": "1.0.0",
     "source": "./",
     "strict": false,
     "skills": ["./skills/<skill-name>"]
   }
   ```
3. 同步更新根目录 `README.md`（安装方式、使用说明、文件结构）
4. 更新 marketplace.json 顶层 `version` 字段

## 用户安装方式

```bash
# 添加 marketplace
/plugin marketplace add sheacoding/Ericoding-skills

# 安装某个 skill
/plugin install <skill-name>@ericoding-skills
```

## seedance-storyboard Skill 的核心设计

SKILL.md 中使用 `AskUserQuestion` 工具做结构化引导（Plan Mode 选项确认模式），分四步收集用户需求：
1. 品类速选（AI漫剧/真人短剧/产品广告/互动接龙等 11 类）
2. 核心参数配置（时长/比例/风格，品类专属参数）
3. 素材情况确认（多选）
4. 内容细节收集 → 生成提示词

**硬性约束**：生成的提示词正文 ≤ 1000 字（平台限制）；禁止使用具体真实人名（平台审核会拦截）。

## ima2gen Skill 的核心设计

与 seedance-storyboard 不同，ima2gen 包含一个 **Python CLI 组件**，负责实际调用 API。

- **CLI 位置**：`skills/ima2gen/cli/ima2gen.py`，首次使用时 Claude 将其复制到 `~/.config/ima2gen/ima2gen.py`
- **凭证存储**：`~/.config/ima2gen/config.json`（api_key + base_url + model）
- **平台适配**：`PROVIDER_REGISTRY` 注册表按 hostname 匹配已知平台，未知平台首次请求自动探测并缓存模式
- **CLI 命令**：`setup`（配置向导）/ `generate`（生成图片）/ `check`（检查配置及平台模式）
- **提示词构建**：Claude 读取 `skills/ima2gen/templates/` 中对应类别模板，构建英文提示词后确认再执行
- **Response 处理**：同步（b64_json/url 直接返回）和异步（task_id 轮询）双模式自动路由

### 已验证平台（2025-05-12）

| 平台 | base_url | 模式 | 验证结果 |
|------|----------|------|---------|
| apimart.ai | `https://api.apimart.ai/v1` | async | ✅ 1152×2048 PNG，~45s |
| BEIMA AI | `https://bmai.kun8.vip/v1` | sync | ✅ 1024×1024 PNG，即时返回 |
