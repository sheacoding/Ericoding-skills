#!/usr/bin/env python3
"""
ima2gen CLI — OpenAI-compatible 图像生成工具
支持 BEIMA AI / apimart.ai / OpenAI 官方 / 任意兼容端点

凭证读取优先级：
  1. 环境变量 IMA2GEN_API_KEY / IMA2GEN_BASE_URL / IMA2GEN_MODEL
  2. ~/.config/ima2gen/config.json（fallback）
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

import click
import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

# --------------------------------------------------------------------------- #
CONFIG_DIR = Path.home() / ".config" / "ima2gen"
CONFIG_FILE = CONFIG_DIR / "config.json"
console = Console()

PRESETS = [
    {
        "name": "apimart.ai（推荐，异步高清）",
        "base_url": "https://api.apimart.ai/v1",
        "model": "gpt-image-2",
        "env_hint": "APIMART_API_KEY",
    },
    {
        "name": "BEIMA AI（国内可用）",
        "base_url": "https://bmai.kun8.vip/v1",
        "model": "gpt-image-2",
        "env_hint": "BEIMA_AI_API_KEY",
    },
    {
        "name": "OpenAI 官方",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-image-1",
        "env_hint": "OPENAI_API_KEY",
    },
    {
        "name": "自定义端点",
        "base_url": None,
        "model": "gpt-image-2",
        "env_hint": "IMA2GEN_API_KEY",
    },
]

ENV_API_KEY  = "IMA2GEN_API_KEY"
ENV_BASE_URL = "IMA2GEN_BASE_URL"
ENV_MODEL    = "IMA2GEN_MODEL"
# --------------------------------------------------------------------------- #


def load_config() -> dict:
    """读取凭证：环境变量优先，其次 config 文件。"""
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
    cfg_to_save = {k: v for k, v in cfg.items() if not k.startswith("_")}
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg_to_save, f, indent=2, ensure_ascii=False)


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


def _poll_task(base_url: str, task_id: str, headers: dict, proxies) -> list:
    """轮询异步任务直到完成，返回图片数据列表。"""
    poll_url = base_url.rstrip("/").rsplit("/v1", 1)[0] + "/v1/tasks/" + task_id
    for _ in range(120):  # 最多等 600s
        time.sleep(5)
        r = requests.get(poll_url, headers=headers, proxies=proxies, timeout=15)
        r.raise_for_status()
        task = r.json().get("data", {})
        status = task.get("status", "")
        progress = task.get("progress", 0)
        console.print(f"  [dim]进度 {progress}% ({status})[/dim]", end="\r")
        if status == "completed":
            images = task.get("result", {}).get("images", [])
            # 统一为 [{"url": "..."}, ...] 格式
            result = []
            for img in images:
                urls = img.get("url", [])
                if isinstance(urls, list):
                    result.extend({"url": u} for u in urls)
                else:
                    result.append({"url": urls})
            return result
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"任务失败：{task}")
    raise TimeoutError("任务超时（600s）")


# --------------------------------------------------------------------------- #


@click.group()
def cli():
    """ima2gen — AI 图像生成 CLI"""


@cli.command()
def setup():
    """配置 API 端点和 Key，写入 ~/.config/ima2gen/config.json。
    提示：也可直接设置环境变量 IMA2GEN_API_KEY / IMA2GEN_BASE_URL / IMA2GEN_MODEL，
    环境变量优先级高于 config 文件，且不会被 git 追踪。
    """
    console.print(Panel.fit("[bold cyan]ima2gen 配置向导[/bold cyan]", border_style="cyan"))
    console.print(
        "\n[dim]💡 提示：也可通过环境变量配置（无需此向导）：[/dim]\n"
        f"[dim]   export {ENV_API_KEY}='your-key'[/dim]\n"
        f"[dim]   export {ENV_BASE_URL}='https://api.apimart.ai/v1'  # 可选[/dim]\n"
        f"[dim]   export {ENV_MODEL}='gpt-image-2'                   # 可选[/dim]\n"
    )

    if os.environ.get(ENV_API_KEY):
        console.print(f"[green]✓ 检测到环境变量 {ENV_API_KEY}（当前生效）[/green]")
        if not Confirm.ask("仍要写入 config 文件作为 fallback？", default=False):
            return

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            existing = json.load(f)
        console.print("\n[yellow]已有 config 文件：[/yellow]")
        console.print(f"  base_url : {existing.get('base_url', '未知')}")
        console.print(f"  api_key  : {mask_key(existing.get('api_key', ''))}")
        if not Confirm.ask("\n是否覆盖？", default=False):
            console.print("[green]配置未变更。[/green]")
            return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("序号", style="cyan", width=4)
    table.add_column("服务商", style="white")
    table.add_column("base_url", style="dim")
    table.add_column("默认模型", style="yellow")
    table.add_column("建议 env var", style="green")
    for i, p in enumerate(PRESETS, 1):
        table.add_row(str(i), p["name"], p["base_url"] or "手动输入", p["model"], p["env_hint"])
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
    save_config(cfg)
    console.print(f"\n[green]✓ 已写入 {CONFIG_FILE}[/green]")
    console.print(f"  base_url : {base_url}")
    console.print(f"  model    : {model}")
    console.print(f"  api_key  : {mask_key(api_key)}")
    console.print(
        f"\n[dim]建议同时将 API Key 写入 shell profile（~/.zshrc 或 ~/.bashrc）：[/dim]\n"
        f"[bold]  export {preset['env_hint']}='{mask_key(api_key)}'[/bold]"
    )


@cli.command()
@click.option("--prompt", required=True, help="图像生成提示词（英文效果最佳）")
@click.option("--quality", default="hd", type=click.Choice(["standard", "hd"]), show_default=True)
@click.option("--size", default="1:1", show_default=True,
              help="画面比例或尺寸。apimart: 1:1 / 16:9 / 9:16；BEIMA/OpenAI: 1024x1024 / 1792x1024 / 1024x1792")
@click.option("--style", default="vivid", type=click.Choice(["vivid", "natural"]), show_default=True)
@click.option("--resolution", default=None,
              help="分辨率（仅 apimart 支持）：1k / 2k / 4k")
@click.option("--output", required=True, help="保存路径（如 /path/to/output.png）")
@click.option("--n", default=1, type=click.IntRange(1, 4), show_default=True, help="生成数量")
def generate(prompt, quality, size, style, resolution, output, n):
    """调用 API 生成图像并保存到指定路径"""
    cfg = load_config()
    source_tag = "[dim](来自环境变量)[/dim]" if cfg.get("_source") == "env" else "[dim](来自 config 文件)[/dim]"

    res_tag = f" | [bold]分辨率[/bold]: {resolution}" if resolution else ""
    console.print(Panel.fit(
        f"[bold]模型[/bold]: {cfg['model']}  {source_tag}\n"
        f"[bold]端点[/bold]: {cfg['base_url']}\n"
        f"[bold]质量[/bold]: {quality} | [bold]尺寸[/bold]: {size}{res_tag} | "
        f"[bold]风格[/bold]: {style} | [bold]数量[/bold]: {n}",
        title="[cyan]ima2gen[/cyan]",
        border_style="cyan",
    ))
    console.print(f"\n[dim]提示词:[/dim] {prompt}\n")

    proxies = _detect_proxies()
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    gen_url = cfg["base_url"].rstrip("/") + "/images/generations"

    # 按兼容性逐步降级：全参 → 省略 style/quality → 最小参数集
    base_body: dict = {"model": cfg["model"], "prompt": prompt, "n": n, "size": size}
    if resolution:
        base_body["resolution"] = resolution

    param_sets = [
        {**base_body, "quality": quality, "style": style, "response_format": "b64_json"},
        {**base_body, "quality": quality, "style": style},
        base_body,
    ]

    with console.status("[bold green]正在提交生图请求...[/bold green]", spinner="dots"):
        raw_data = None
        last_err = None
        for body in param_sets:
            try:
                r = requests.post(gen_url, json=body, headers=headers, proxies=proxies, timeout=300)
                r.raise_for_status()
                raw_data = r.json().get("data", [])
                break
            except Exception as e:
                last_err = e
                continue

    if raw_data is None:
        console.print(f"[red]API 调用失败：{last_err}[/red]")
        sys.exit(1)

    # 异步模式：服务商返回 task_id 而非图片
    if raw_data and raw_data[0].get("task_id"):
        task_id = raw_data[0]["task_id"]
        console.print(f"[cyan]异步任务已提交，task_id: {task_id}[/cyan]")
        try:
            with console.status("[bold green]等待生成完成...[/bold green]", spinner="dots"):
                raw_data = _poll_task(cfg["base_url"], task_id, headers, proxies)
        except Exception as e:
            console.print(f"[red]轮询失败：{e}[/red]")
            sys.exit(1)

    output_path = Path(output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for i, img_item in enumerate(raw_data):
        path = (
            output_path.parent / f"{output_path.stem}_{i+1}{output_path.suffix or '.png'}"
            if n > 1
            else output_path
        )

        if img_item.get("b64_json"):
            path.write_bytes(base64.b64decode(img_item["b64_json"]))
        elif img_item.get("url"):
            dl = requests.get(img_item["url"], proxies=proxies, timeout=120)
            dl.raise_for_status()
            path.write_bytes(dl.content)
        else:
            console.print(f"[red]第 {i+1} 张图像数据为空，跳过[/red]")
            continue

        saved_paths.append(path)
        console.print(f"[green]✓ 已保存：{path}[/green]")

    if saved_paths:
        console.print(f"\n[bold green]生成完成，共 {len(saved_paths)} 张图片。[/bold green]")
    else:
        console.print("[red]未能保存任何图片。[/red]")
        sys.exit(1)


@cli.command()
def check():
    """检查凭证是否可用（供 SKILL.md 调用）"""
    env_key = os.environ.get(ENV_API_KEY)
    if env_key:
        base_url = os.environ.get(ENV_BASE_URL, "https://api.apimart.ai/v1")
        model = os.environ.get(ENV_MODEL, "gpt-image-2")
        console.print(f"[green]✓ 已配置（环境变量）[/green] — {base_url} / {model}")
        sys.exit(0)

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        console.print(f"[green]✓ 已配置（config 文件）[/green] — {cfg.get('base_url', '?')} / {cfg.get('model', '?')}")
        sys.exit(0)

    console.print(f"[yellow]未配置。请设置 {ENV_API_KEY} 或运行 `ima2gen setup`[/yellow]")
    sys.exit(1)


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    cli()
