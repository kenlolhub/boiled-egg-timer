"""Gradio Egg Timer app with a single action button.

Designed to avoid flaky multi-button visibility updates in Gradio.
"""

from __future__ import annotations

import time
from typing import Any

import gradio as gr

from egg_timing import DONENESS_BASE_SECONDS, calculate_cook_seconds, format_mm_ss

DEFAULT_EGG_COUNT = 1
PLACEHOLDER_TIME = "--:--"

ACTION_LABELS = {
    "idle": "開始流程",
    "boil": "水已經滾起",
    "simmer": "已經轉細火",
    "add_eggs": "已放蛋，開始計時",
    "countdown": "計時中…",
    "done": "已完成",
}


def _timer_html(display_time: str) -> str:
    return (
        '<div style="text-align:center; margin: 8px 0 16px;">'
        '<div style="font-size:16px; color:#6b7280; margin-bottom:6px;">建議/剩餘時間</div>'
        f'<div style="font-size:clamp(56px, 12vw, 110px); line-height:1; font-weight:700; letter-spacing:2px;">{display_time}</div>'
        "</div>"
    )


def _build_status(stage: str, egg_count: int, doneness: str | None, total_seconds: int | None) -> str:
    if stage == "idle":
        if not doneness:
            return "### 歡迎你！\n請先選擇熟度，之後我會一步一步陪你煮。"
        return (
            "### 準備好可以開始\n"
            f"目前設定：**{egg_count} 隻蛋 / {doneness}**\n"
            f"建議時間：**{format_mm_ss(total_seconds or 0)}**"
        )
    if stage == "boil":
        return "### 第 1 步：煲滾水\n等到水大滾先進入下一步，唔使急，我等你。"
    if stage == "simmer":
        return "### 第 2 步：轉細火\n轉做微滾狀態，等水穩定啲再放蛋。"
    if stage == "add_eggs":
        return (
            "### 第 3 步：輕輕放蛋\n"
            f"而家會用 **{egg_count} 隻蛋 / {doneness}** 去計時。\n"
            f"建議時間：**{format_mm_ss(total_seconds or 0)}**"
        )
    if stage == "countdown":
        return (
            "### 第 4 步：正式計時中\n"
            f"目標：**{doneness}**｜蛋數：**{egg_count}** 隻\n加油，差唔多完成啦！"
        )
    return "### 完成！\n雞蛋煮好啦，可以即刻過冰水 30-60 秒，口感會更靚。"


def _expected_action_label(stage: str, doneness: str | None) -> str:
    if stage == "idle" and not doneness:
        return "請先選熟度"
    return ACTION_LABELS.get(stage, "未知")


def _controls_locked(stage: str) -> bool:
    return stage in {"countdown", "done"}


def _action_button_update(stage: str, doneness: str | None) -> Any:
    if stage == "countdown":
        return gr.update(value=ACTION_LABELS[stage], visible=True, interactive=False)
    if stage == "done":
        return gr.update(value=ACTION_LABELS[stage], visible=True, interactive=False)
    if stage == "idle" and not doneness:
        return gr.update(value="請先選熟度", visible=True, interactive=False)
    return gr.update(value=ACTION_LABELS.get(stage, "下一步"), visible=True, interactive=True)


def _build_debug_text(
    *,
    stage: str,
    source: str,
    egg_count: int | None,
    doneness: str | None,
    running: bool,
    total_seconds: int,
    remaining_seconds: int,
) -> str:
    egg_text = "-" if egg_count is None else str(egg_count)
    doneness_text = "-" if doneness is None else doneness
    return (
        f"source={source} | "
        f"stage={stage} | "
        f"eggs={egg_text} | "
        f"doneness={doneness_text} | "
        f"running={running} | "
        f"total={total_seconds} | "
        f"remaining={remaining_seconds} | "
        f"expected_action={_expected_action_label(stage, doneness)} | "
        f"controls_locked={_controls_locked(stage)}"
    )


def _render_screen(
    *,
    stage: str,
    source: str,
    egg_count: int,
    doneness: str | None,
    total_seconds: int,
    remaining_seconds: int,
    running: bool,
    status_override: str | None = None,
):
    display_seconds = remaining_seconds if stage in {"countdown", "done"} else total_seconds
    display_text = PLACEHOLDER_TIME if display_seconds <= 0 else format_mm_ss(display_seconds)
    status = status_override or _build_status(stage, egg_count, doneness, total_seconds)
    debug_text = _build_debug_text(
        stage=stage,
        source=source,
        egg_count=egg_count,
        doneness=doneness,
        running=running,
        total_seconds=total_seconds,
        remaining_seconds=remaining_seconds,
    )
    return (
        status,
        debug_text,
        _timer_html(display_text),
        _action_button_update(stage, doneness),
        gr.update(interactive=not _controls_locked(stage)),
        gr.update(interactive=not _controls_locked(stage)),
    )


def preview_settings(egg_count: int, doneness: str | None, stage: str, running: bool, remaining_seconds: int):
    total_seconds = calculate_cook_seconds(egg_count, doneness) if doneness else 0

    if stage == "idle":
        status, debug_text, timer_html, btn_action, egg_update, doneness_update = _render_screen(
            stage="idle",
            source="preview_idle",
            egg_count=egg_count,
            doneness=doneness,
            total_seconds=total_seconds,
            remaining_seconds=total_seconds,
            running=False,
        )
        return (
            total_seconds,
            total_seconds,
            timer_html,
            status,
            btn_action,
            debug_text,
            egg_update,
            doneness_update,
        )

    debug_text = _build_debug_text(
        stage=stage,
        source="preview_non_idle",
        egg_count=egg_count,
        doneness=doneness,
        running=running,
        total_seconds=total_seconds,
        remaining_seconds=remaining_seconds,
    )
    return (
        total_seconds,
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        debug_text,
        gr.update(interactive=not _controls_locked(stage)),
        gr.update(interactive=not _controls_locked(stage)),
    )


def handle_action(stage: str, egg_count: int, doneness: str | None, total_seconds: int):
    if stage == "idle":
        if not doneness:
            return (
                stage,
                total_seconds,
                total_seconds,
                False,
                0.0,
                gr.update(active=False),
                *_render_screen(
                    stage="idle",
                    source="action_idle_blocked",
                    egg_count=egg_count,
                    doneness=doneness,
                    total_seconds=0,
                    remaining_seconds=0,
                    running=False,
                    status_override="### 未可以開始\n請先揀熟度。",
                ),
            )
        new_total = calculate_cook_seconds(egg_count, doneness)
        return (
            "boil",
            new_total,
            new_total,
            False,
            0.0,
            gr.update(active=False),
            *_render_screen(
                stage="boil",
                source="action_to_boil",
                egg_count=egg_count,
                doneness=doneness,
                total_seconds=new_total,
                remaining_seconds=new_total,
                running=False,
            ),
        )

    if stage == "boil":
        return (
            "simmer",
            total_seconds,
            total_seconds,
            False,
            0.0,
            gr.update(active=False),
            *_render_screen(
                stage="simmer",
                source="action_to_simmer",
                egg_count=egg_count,
                doneness=doneness,
                total_seconds=total_seconds,
                remaining_seconds=total_seconds,
                running=False,
            ),
        )

    if stage == "simmer":
        return (
            "add_eggs",
            total_seconds,
            total_seconds,
            False,
            0.0,
            gr.update(active=False),
            *_render_screen(
                stage="add_eggs",
                source="action_to_add_eggs",
                egg_count=egg_count,
                doneness=doneness,
                total_seconds=total_seconds,
                remaining_seconds=total_seconds,
                running=False,
            ),
        )

    if stage == "add_eggs":
        end_timestamp = time.time() + total_seconds
        return (
            "countdown",
            total_seconds,
            total_seconds,
            True,
            end_timestamp,
            gr.update(active=True),
            *_render_screen(
                stage="countdown",
                source="action_begin_countdown",
                egg_count=egg_count,
                doneness=doneness,
                total_seconds=total_seconds,
                remaining_seconds=total_seconds,
                running=True,
            ),
        )

    return (
        stage,
        total_seconds,
        total_seconds,
        False,
        0.0,
        gr.update(active=False),
        *_render_screen(
            stage=stage,
            source="action_noop",
            egg_count=egg_count,
            doneness=doneness,
            total_seconds=total_seconds,
            remaining_seconds=total_seconds,
            running=False,
        ),
    )


def tick(
    stage: str,
    running: bool,
    end_timestamp: float,
    remaining_seconds: int,
    egg_count: int,
    doneness: str | None,
    total_seconds: int,
):
    if stage != "countdown" or not running:
        return (
            stage,
            remaining_seconds,
            running,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(active=False),
        )

    new_remaining = max(0, int(end_timestamp - time.time()))

    if new_remaining > 0:
        debug_text = _build_debug_text(
            stage=stage,
            source="tick_countdown",
            egg_count=egg_count,
            doneness=doneness,
            running=True,
            total_seconds=total_seconds,
            remaining_seconds=new_remaining,
        )
        return (
            stage,
            new_remaining,
            True,
            _timer_html(format_mm_ss(new_remaining)),
            debug_text,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(active=True),
        )

    done_message = (
        "### 搞掂！
"
        f"你嘅 **{doneness}** 雞蛋已經完成。
"
        "建議即刻放入冰水 30-60 秒，會更易剝殼同保持口感。"
    )
    status, debug_text, timer_html, btn_action, egg_update, doneness_update = _render_screen(
        stage="done",
        source="tick_done",
        egg_count=egg_count,
        doneness=doneness,
        total_seconds=total_seconds,
        remaining_seconds=0,
        running=False,
        status_override=done_message,
    )
    return (
        "done",
        0,
        False,
        timer_html,
        debug_text,
        status,
        btn_action,
        egg_update,
        doneness_update,
        gr.update(active=False),
    )

def reset_ui():
    stage = "idle"
    total_seconds = 0
    remaining_seconds = 0
    return (
        stage,
        total_seconds,
        remaining_seconds,
        False,
        0.0,
        gr.update(active=False),
        *_render_screen(
            stage=stage,
            source="reset_ui",
            egg_count=DEFAULT_EGG_COUNT,
            doneness=None,
            total_seconds=total_seconds,
            remaining_seconds=remaining_seconds,
            running=False,
        ),
        gr.update(value=DEFAULT_EGG_COUNT, interactive=True),
        gr.update(value=None, interactive=True),
    )


with gr.Blocks(title="蛋蛋計時小幫手") as demo:
    gr.Markdown("# 蛋蛋計時小幫手")
    gr.Markdown("陪你一步一步煮出理想熟度，慢慢嚟就得。")

    with gr.Row():
        egg_count = gr.Slider(minimum=1, maximum=12, step=1, value=DEFAULT_EGG_COUNT, label="雞蛋數量")
        doneness = gr.Radio(
            choices=list(DONENESS_BASE_SECONDS.keys()),
            value=None,
            label="熟度（必選）",
        )

    stage_state = gr.State("idle")
    total_state = gr.State(0)
    remaining_state = gr.State(0)
    running_state = gr.State(False)
    end_ts_state = gr.State(0.0)

    status_md = gr.Markdown(_build_status("idle", DEFAULT_EGG_COUNT, None, None))
    timer_display = gr.HTML(_timer_html(PLACEHOLDER_TIME))
    debug_text = gr.Textbox(
        value=_build_debug_text(
            stage="idle",
            source="init",
            egg_count=DEFAULT_EGG_COUNT,
            doneness=None,
            running=False,
            total_seconds=0,
            remaining_seconds=0,
        ),
        label="Debug state",
        interactive=False,
        visible=True,
    )

    with gr.Row():
        btn_action = gr.Button("請先選熟度", variant="primary", visible=True, interactive=False)
        btn_reset = gr.Button("重新開始")

    ticker = gr.Timer(value=1.0, active=False)

    for input_component in (egg_count, doneness):
        input_component.change(
            fn=preview_settings,
            inputs=[egg_count, doneness, stage_state, running_state, remaining_state],
            outputs=[total_state, remaining_state, timer_display, status_md, btn_action, debug_text, egg_count, doneness],
        )

    btn_action.click(
        fn=handle_action,
        inputs=[stage_state, egg_count, doneness, total_state],
        outputs=[
            stage_state,
            total_state,
            remaining_state,
            running_state,
            end_ts_state,
            ticker,
            status_md,
            debug_text,
            timer_display,
            btn_action,
            egg_count,
            doneness,
        ],
    )

    btn_reset.click(
        fn=reset_ui,
        inputs=[],
        outputs=[
            stage_state,
            total_state,
            remaining_state,
            running_state,
            end_ts_state,
            ticker,
            status_md,
            debug_text,
            timer_display,
            btn_action,
            egg_count,
            doneness,
        ],
    )

    ticker.tick(
        fn=tick,
        inputs=[
            stage_state,
            running_state,
            end_ts_state,
            remaining_state,
            egg_count,
            doneness,
            total_state,
        ],
        outputs=[
            stage_state,
            remaining_state,
            running_state,
            timer_display,
            debug_text,
            status_md,
            btn_action,
            egg_count,
            doneness,
            ticker,
        ],
    )


if __name__ == "__main__":
    demo.launch(ssr_mode=False)
