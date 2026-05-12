#!/usr/bin/env python3
"""
ima2gen CLI — 多平台 OpenAI-compatible 图像生成工具

凭证读取优先级：
  1. 环境变量 IMA2GEN_API_KEY / IMA2GEN_BASE_URL / IMA2GEN_MODEL
  2. ~/.config/ima2gen/config.json（fallback）

平台适配优先级：
  1. PROVIDER_REGISTRY 已知平台（精确匹配 hostname）
  2. config.json 中缓存的 _mode / _poll_path（上次探测结果）
  3. 自动探测：发请求 → 检测响应结构 → 写回 config 缓存
"""

import base64
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import click
import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

# --------------------------------------------------------------------------- #
CONFIG_DIR  = Path.home() / ".config" / "ima2gen"
CONFIG_FILE = CONFIG_DIR / "config.json"
console     = Console()

# 已知平台注册表 — 新平台经过测试后在此添加
PROVIDER_REGISTRY: dict[str, dict] = {
    "api.apimart.ai": {
        "mode":       "async",
        "poll_path":  "/v1/tasks/{task_id}",  # GET 轮询路径
        "size_hint":  "ratio",                # "1:1" / "16:9" / "9:16"
    },
    "bmai.kun8.vip": {
        "mode":      "sync",
        "size_hint": "pixels",                # "1024x1024"
    },
    "api.openai.com": {
        "mode":      "sync",
        "size_hint": "pixels",
    },
}

PRESETS = [
    {
        "name":     "apimart.ai（推荐，异步高清）",
        "base_url": "https://api.apimart.ai/v1",
        "model":    "gpt-image-2",
        "env_hint": "APIMART_API_KEY",
    },
    {
        "name":     "BEIMA AI（国内可用）",
        "base_url": "https://bmai.kun8.vip/v1",
        "model":    "gpt-image-2",
        "env_hint": "BEIMA_AI_API_KEY",
    },
    {
        "name":     "OpenAI 官方",
        "base_url": "https://api.openai.com/v1",
        "model":    "gpt-image-1",
        "env_hint": "OPENAI_API_KEY",
    },
    {
        "name":     "自定义端点",
        "base_url": None,
        "model":    "gpt-image-2",
        "env_hint": "IMA2GEN_API_KEY",
    },
]

ENV_API_KEY  = "IMA2GEN_API_KEY"
ENV_BASE_URL = "IMA2GEN_BASE_URL"
ENV_MODEL    = "IMA2GEN_MODEL"
# --------------------------------------------------------------------------- #


def _hostname(url: str) -> str:
    return urlparse(url).hostname or ""


def detect_provider(base_url: str) -> dict:
    """从注册表匹配已知平台，返回平台元数据（不含 API Key）。"""
    return PROVIDER_REGISTRY.get(_hostname(base_url), {})


def load_config() -> dict:
    env_key   = os.environ.get(ENV_API_KEY)
    env_url   = os.environ.get(ENV_BASE_URL)
    env_model = os.environ.get(ENV_MODEL)

    if env_key:
        return {
            "api_key":  env_key,
            "base_url": env_url or "https://api.apimart.ai/v1",
            "model":    env_model or "gpt-image-2",
            "_source":  "env",
        }

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        cfg["_source"] = "file"
        return cfg

    console.print(
        f"[red]未找到凭证。请设置环境变量 {ENV_API_KEY}，"
        f"或运行 `ima2gen setup` 进行交互配置。[/red]"
    )
    sys.exit(1)


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    skip = {"_source", "_mode", "_poll_path"}  # 运行时字段不持久化
    with open(CONFIG_FILE, "w") as f:
        json.dump({k: v for k, v in cfg.items() if k not in skip}, f, indent=2, ensure_ascii=False)


def _patch_provider_cache(cfg: dict, mode: str, poll_path: str = "") -> None:
    """把探测到的平台模式写回 config 文件，避免下次重复探测。"""
    if cfg.get("_source") != "file":
        return
    raw = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    raw["_cached_mode"]      = mode
    raw["_cached_poll_path"] = poll_path
    CONFIG_FILE.write_text(json.dumps(raw, indent=2, ensure_ascii=False))


def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "***"
    return key[:4] + "..." + key[-4:]


def _detect_proxies() -> dict | None:
    proxy = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("ALL_PROXY")
        or os.environ.get("all_proxy")
    )
    return {"http": proxy, "https": proxy} if proxy else None


# --------------------------------------------------------------------------- #
# 适配器层
# --------------------------------------------------------------------------- #

def _build_request_variants(base_body: dict) -> list[dict]:
    """按兼容性降级的请求参数列表。"""
    quality = base_body.pop("_quality", None)
    style   = base_body.pop("_style", None)
    variants = []
    if quality and style:
        variants.append({**base_body, "quality": quality, "style": style, "response_format": "b64_json"})
        variants.append({**base_body, "quality": quality, "style": style})
    variants.append(base_body)
    return variants


def _post_with_fallback(gen_url: str, base_body: dict, headers: dict, proxies) -> list:
    """发送生图请求，自动降级参数，返回原始 data 列表。"""
    variants = _build_request_variants(dict(base_body))
    last_err = None
    for body in variants:
        try:
            r = requests.post(gen_url, json=body, headers=headers, proxies=proxies, timeout=300)
            r.raise_for_status()
            return r.json().get("data", [])
        except Exception as e:
            last_err = e
    raise RuntimeError(f"API 调用失败：{last_err}")


def _sync_adapter(raw_data: list, proxies) -> list[dict]:
    """同步响应 → 统一为 [{"b64_json"|"url": ...}] 格式。"""
    return raw_data  # 已是标准格式


def _async_adapter(
    raw_data: list,
    base_url: str,
    poll_path: str,
    headers: dict,
    proxies,
    cfg: dict,
) -> list[dict]:
    """异步响应 → 轮询至完成 → 返回图片列表。"""
    task_id  = raw_data[0]["task_id"]
    hostname = _hostname(base_url)

    # 拼轮询 URL：注册表 > 缓存 > 默认 /v1/tasks/{task_id}
    if not poll_path:
        poll_path = PROVIDER_REGISTRY.get(hostname, {}).get("poll_path", "/v1/tasks/{task_id}")

    base = base_url.rstrip("/").rsplit("/v1", 1)[0]
    poll_url = base + poll_path.format(task_id=task_id)

    console.print(f"  [cyan]task_id: {task_id}[/cyan]")

    for attempt in range(120):
        time.sleep(5)
        r = requests.get(poll_url, headers=headers, proxies=proxies, timeout=15)
        r.raise_for_status()
        task    = r.json().get("data", {})
        status  = task.get("status", "")
        progress = task.get("progress", 0)
        console.print(f"  [dim]{attempt*5}s — {progress}% ({status})[/dim]", end="\r")

        if status == "completed":
            images = task.get("result", {}).get("images", [])
            result = []
            for img in images:
                urls = img.get("url", [])
                result.extend({"url": u} for u in (urls if isinstance(urls, list) else [urls]))
            return result

        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"任务失败：{task}")

    raise TimeoutError("任务超时（600s），请稍后重试")


def _save_images(raw_data: list, output: str, n: int, proxies) -> list[Path]:
    output_path = Path(output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    saved = []
    for i, item in enumerate(raw_data):
        path = (
            output_path.parent / f"{output_path.stem}_{i+1}{output_path.suffix or '.png'}"
            if n > 1 else output_path
        )
        if item.get("b64_json"):
            path.write_bytes(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            dl = requests.get(item["url"], proxies=proxies, timeout=120)
            dl.raise_for_status()
            path.write_bytes(dl.content)
        else:
            console.print(f"[red]第 {i+1} 张图像数据为空，跳过[/red]")
            continue
        saved.append(path)
        console.print(f"[green]✓ 已保存：{path}[/green]")
    return saved


# --------------------------------------------------------------------------- #
# CLI 命令
# --------------------------------------------------------------------------- #

@click.group()
def cli():
    """ima2gen — 多平台 AI 图像生成 CLI"""


@cli.command()
def setup():
    """配置 API 端点和 Key，写入 ~/.config/ima2gen/config.json。"""
    console.print(Panel.fit("[bold cyan]ima2gen 配置向导[/bold cyan]", border_style="cyan"))
    console.print(
        f"\n[dim]💡 也可通过环境变量配置：[/dim]\n"
        f"[dim]   export {ENV_API_KEY}='your-key'[/dim]\n"
        f"[dim]   export {ENV_BASE_URL}='https://api.apimart.ai/v1'[/dim]\n"
        f"[dim]   export {ENV_MODEL}='gpt-image-2'[/dim]\n"
    )

    if os.environ.get(ENV_API_KEY):
        console.print(f"[green]✓ 检测到环境变量 {ENV_API_KEY}（当前生效）[/green]")
        if not Confirm.ask("仍要写入 config 文件作为 fallback？", default=False):
            return

    if CONFIG_FILE.exists():
        existing = json.loads(CONFIG_FILE.read_text())
        console.print(f"\n[yellow]已有 config 文件：[/yellow]")
        console.print(f"  base_url : {existing.get('base_url', '未知')}")
        console.print(f"  api_key  : {mask_key(existing.get('api_key', ''))}")
        provider = detect_provider(existing.get("base_url", ""))
        if provider:
            mode = provider.get("mode", "?")
            console.print(f"  平台模式 : {mode}（已知平台，自动适配）")
        elif existing.get("_cached_mode"):
            console.print(f"  平台模式 : {existing['_cached_mode']}（探测缓存）")
        if not Confirm.ask("\n是否覆盖？", default=False):
            console.print("[green]配置未变更。[/green]")
            return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("序号", style="cyan", width=4)
    table.add_column("服务商", style="white")
    table.add_column("base_url", style="dim")
    table.add_column("默认模型", style="yellow")
    for i, p in enumerate(PRESETS, 1):
        prov = detect_provider(p["base_url"] or "")
        mode_tag = f" [{prov['mode']}]" if prov else ""
        table.add_row(str(i), p["name"] + mode_tag, p["base_url"] or "手动输入", p["model"])
    console.print(table)

    choice = Prompt.ask("\n请选择服务商序号", choices=["1", "2", "3", "4"], default="1")
    preset = PRESETS[int(choice) - 1]

    base_url = (
        Prompt.ask("请输入 base_url（如 https://your-proxy.com/v1）").rstrip("/")
        if preset["base_url"] is None
        else preset["base_url"]
    )

    api_key = Prompt.ask("请输入 API Key", password=True)
    if not api_key.strip():
        console.print("[red]API Key 不能为空[/red]")
        sys.exit(1)

    model = Prompt.ask("模型名称", default=preset["model"])

    cfg = {"api_key": api_key.strip(), "base_url": base_url, "model": model.strip()}
    provider = detect_provider(base_url)
    if provider:
        console.print(f"\n[green]✓ 已知平台，模式：{provider['mode']}，自动适配[/green]")
    else:
        console.print("\n[yellow]未知平台，首次生图时将自动探测请求格式并缓存[/yellow]")

    save_config(cfg)
    console.print(f"[green]✓ 已写入 {CONFIG_FILE}[/green]")


@cli.command()
@click.option("--prompt",     required=True, help="图像生成提示词（英文效果最佳）")
@click.option("--quality",    default="hd", type=click.Choice(["standard", "hd"]), show_default=True)
@click.option("--size",       default="1:1", show_default=True,
              help="画面比例/尺寸。apimart: 1:1/16:9/9:16；BEIMA/OpenAI: 1024x1024/1792x1024/1024x1792")
@click.option("--style",      default="vivid", type=click.Choice(["vivid", "natural"]), show_default=True)
@click.option("--resolution", default=None, help="分辨率（apimart 支持）：1k / 2k / 4k")
@click.option("--output",     required=True, help="保存路径（如 ~/Desktop/output.png）")
@click.option("--n",          default=1, type=click.IntRange(1, 4), show_default=True)
def generate(prompt, quality, size, style, resolution, output, n):
    """调用 API 生成图像并保存到指定路径（自动适配同步/异步平台）"""
    cfg      = load_config()
    proxies  = _detect_proxies()
    headers  = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
    gen_url  = cfg["base_url"].rstrip("/") + "/images/generations"

    # 解析平台元数据：注册表 > config 缓存 > 待探测
    provider = detect_provider(cfg["base_url"])
    cached_mode      = cfg.get("_cached_mode")
    cached_poll_path = cfg.get("_cached_poll_path", "")
    known_mode = provider.get("mode") or cached_mode  # None = 未知，首次探测

    # 构建请求 body
    base_body: dict = {
        "model": cfg["model"], "prompt": prompt, "n": n, "size": size,
        "_quality": quality, "_style": style,
    }
    if resolution:
        base_body["resolution"] = resolution

    res_tag = f" | [bold]分辨率[/bold]: {resolution}" if resolution else ""
    mode_tag = f" [dim]({known_mode or '自动探测'})[/dim]"
    console.print(Panel.fit(
        f"[bold]模型[/bold]: {cfg['model']}  [dim]({cfg.get('_source','?')})[/dim]\n"
        f"[bold]端点[/bold]: {cfg['base_url']}{mode_tag}\n"
        f"[bold]质量[/bold]: {quality} | [bold]尺寸[/bold]: {size}{res_tag} | "
        f"[bold]风格[/bold]: {style} | [bold]数量[/bold]: {n}",
        title="[cyan]ima2gen[/cyan]", border_style="cyan",
    ))
    console.print(f"\n[dim]提示词:[/dim] {prompt}\n")

    with console.status("[bold green]正在提交生图请求...[/bold green]", spinner="dots"):
        try:
            raw_data = _post_with_fallback(gen_url, base_body, headers, proxies)
        except Exception as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)

    # 探测响应模式（首次未知平台）
    is_async = bool(raw_data and raw_data[0].get("task_id"))

    if is_async and known_mode == "sync":
        # 注册表说是同步但返回了 task_id，以实际响应为准
        known_mode = "async"

    if not known_mode:
        detected = "async" if is_async else "sync"
        console.print(f"[cyan]首次探测：该平台为 {detected} 模式，已缓存[/cyan]")
        _patch_provider_cache(cfg, detected, provider.get("poll_path", "") if is_async else "")
        known_mode = detected

    # 路由到对应适配器
    try:
        if is_async:
            console.print("[cyan]异步任务已提交，轮询中...[/cyan]")
            poll_path = provider.get("poll_path") or cached_poll_path or "/v1/tasks/{task_id}"
            with console.status("[bold green]等待生成完成...[/bold green]", spinner="dots"):
                raw_data = _async_adapter(raw_data, cfg["base_url"], poll_path, headers, proxies, cfg)
        else:
            raw_data = _sync_adapter(raw_data, proxies)
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    saved = _save_images(raw_data, output, n, proxies)
    if saved:
        console.print(f"\n[bold green]生成完成，共 {len(saved)} 张图片。[/bold green]")
    else:
        console.print("[red]未能保存任何图片。[/red]")
        sys.exit(1)


@cli.command()
def check():
    """检查凭证与平台配置是否可用。"""
    env_key = os.environ.get(ENV_API_KEY)
    if env_key:
        url   = os.environ.get(ENV_BASE_URL, "https://api.apimart.ai/v1")
        model = os.environ.get(ENV_MODEL, "gpt-image-2")
        provider = detect_provider(url)
        mode = provider.get("mode", "未知") if provider else "未知"
        console.print(f"[green]✓ 已配置（环境变量）[/green] — {url} / {model} / 模式:{mode}")
        sys.exit(0)

    if CONFIG_FILE.exists():
        cfg  = json.loads(CONFIG_FILE.read_text())
        url  = cfg.get("base_url", "?")
        model = cfg.get("model", "?")
        provider = detect_provider(url)
        if provider:
            mode = provider["mode"]
            hint = "已知平台"
        elif cfg.get("_cached_mode"):
            mode = cfg["_cached_mode"]
            hint = "探测缓存"
        else:
            mode = "未探测"
            hint = "首次生图时自动探测"
        console.print(f"[green]✓ 已配置（config 文件）[/green] — {url} / {model}")
        console.print(f"  平台模式: [cyan]{mode}[/cyan] ({hint})")
        sys.exit(0)

    console.print(f"[yellow]未配置。请设置 {ENV_API_KEY} 或运行 `ima2gen setup`[/yellow]")
    sys.exit(1)


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    cli()
