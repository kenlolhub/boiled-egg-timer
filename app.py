"""Gradio Egg Timer app — bilingual (廣東話/English), sound alert, confetti, custom doneness."""

from __future__ import annotations

import time
from typing import Any

import gradio as gr

from egg_timing import DONENESS_BASE_SECONDS, calculate_cook_seconds, format_mm_ss

DEFAULT_EGG_COUNT = 1
DEFAULT_CUSTOM_SECONDS = 480
PLACEHOLDER_TIME = "--:--"

# Radio choices: (display_label, internal_value)
DONENESS_CHOICES = {
    "廣東話": [("流心", "Jammy"), ("8成熟", "Soft boiled"), ("全熟", "Hard boiled"), ("自訂", "Custom")],
    "English": [("Jammy", "Jammy"), ("Soft boiled", "Soft boiled"), ("Hard boiled", "Hard boiled"), ("Custom", "Custom")],
}

STRINGS = {
    "廣東話": {
        "action_idle":        "開始流程",
        "action_boil":        "水已經滾起",
        "action_simmer":      "已經轉細火",
        "action_add_eggs":    "已放蛋，開始計時",
        "action_countdown":   "計時中…",
        "action_done":        "已完成",
        "action_no_doneness": "請先選熟度",
        "time_sublabel":      "倒數焓蛋時間",
        "custom_label":       "自訂",
        "status_welcome":     "### 歡迎你！\n請先揀要焓到幾熟，之後我會逐步教你煮，弱智都識。",
        "status_idle_ready":  "### 準備好可以開始\n目前設定：**{egg_count} 隻蛋 / {doneness}**\n建議時間：**{time}**",
        "status_boil":        "### 第 1 步：煲滾水\n等到水大滾先進入下一步，唔使急，我等你。",
        "status_simmer":      "### 第 2 步：轉細火\n轉做微滾狀態，等水穩定啲再放蛋。",
        "status_add_eggs":    "### 第 3 步：輕輕放蛋\n而家會用 **{egg_count} 隻蛋 / {doneness}** 去計時。\n建議時間：**{time}**",
        "status_countdown":   "### 第 4 步：正式計時中\n目標：**{doneness}**｜蛋數：**{egg_count}** 隻\n加油，差唔多完成啦！",
        "status_done":        "### 完成！\n雞蛋煮好啦，可以即刻過冰水 30-60 秒，口感會更靚。",
        "status_done_detail": "### 搞掂！\n你嘅 **{doneness}** 雞蛋已經完成。\n建議即刻放入冰水 30-60 秒，會更易剝殼同保持口感。",
        "status_blocked":     "### 未可以開始\n請先揀熟度。",
        "app_title":          "# 焓蛋計時小幫手",
        "app_subtitle":       "陪你一步一步煮出理想熟度，慢慢嚟，最緊要快。",
        "label_doneness":     "熟度（必選）",
    },
    "English": {
        "action_idle":        "Start Process",
        "action_boil":        "Water is Boiling",
        "action_simmer":      "Reduced to Simmer",
        "action_add_eggs":    "Eggs Added, Start Timer",
        "action_countdown":   "Timing…",
        "action_done":        "Done",
        "action_no_doneness": "Select doneness first",
        "time_sublabel":      "Egg Timer Countdown",
        "custom_label":       "Custom",
        "status_welcome":     "### Welcome!\nSelect a doneness level and I'll walk you through cooking step by step.",
        "status_idle_ready":  "### Ready to Begin\nSettings: **{egg_count} egg(s) / {doneness}**\nSuggested time: **{time}**",
        "status_boil":        "### Step 1: Bring Water to a Full Boil\nWait for a rolling boil before moving on.",
        "status_simmer":      "### Step 2: Reduce to a Simmer\nLower the heat until the water is gently bubbling.",
        "status_add_eggs":    "### Step 3: Gently Add Eggs\nUsing **{egg_count} egg(s) / {doneness}**.\nSuggested time: **{time}**",
        "status_countdown":   "### Step 4: Timer Running\nTarget: **{doneness}** | Eggs: **{egg_count}**\nAlmost there!",
        "status_done":        "### Done!\nYour eggs are ready. Transfer to ice water for 30–60 seconds for best results.",
        "status_done_detail": "### Done!\nYour **{doneness}** eggs are ready.\nTransfer to ice water for 30–60 seconds for easier peeling.",
        "status_blocked":     "### Cannot Start\nPlease select a doneness level first.",
        "app_title":          "# Boiled Egg Timer",
        "app_subtitle":       "Step-by-step guidance for your perfect egg.",
        "label_doneness":     "Doneness (required)",
    },
}


def _display_doneness(doneness: str | None, lang: str) -> str:
    """Return the display label for a doneness internal key."""
    if doneness is None:
        return ""
    for label, value in DONENESS_CHOICES[lang]:
        if value == doneness:
            return label
    return doneness


def _timer_html(display_time: str, lang: str = "English", stage: str = "") -> str:
    sublabel = STRINGS[lang]["time_sublabel"]
    base = (
        '<div style="text-align:center; margin: 8px 0 16px;">'
        f'<div style="font-size:16px; color:#6b7280; margin-bottom:6px;">{sublabel}</div>'
        f'<div style="font-size:clamp(56px, 12vw, 110px); line-height:1; font-weight:700; letter-spacing:2px;">{display_time}</div>'
        "</div>"
    )
    if stage != "done":
        return base

    sound_script = """
<script>
(function(){
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    gain.gain.setValueAtTime(0.4, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.0);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 1.0);
  } catch(e) {}
})();
</script>"""

    confetti_script = """
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js"></script>
<script>
(function(){
  function go(){
    if(typeof confetti==='function'){
      confetti({particleCount:150,spread:70,origin:{y:0.6}});
    } else {
      setTimeout(go, 100);
    }
  }
  go();
})();
</script>"""

    return base + sound_script + confetti_script


def _build_status(
    stage: str,
    egg_count: int,
    doneness: str | None,
    total_seconds: int | None,
    lang: str = "English",
) -> str:
    s = STRINGS[lang]
    dn = _display_doneness(doneness, lang)
    if stage == "idle":
        if not doneness:
            return s["status_welcome"]
        return s["status_idle_ready"].format(
            egg_count=egg_count,
            doneness=dn,
            time=format_mm_ss(total_seconds or 0),
        )
    if stage == "boil":
        return s["status_boil"]
    if stage == "simmer":
        return s["status_simmer"]
    if stage == "add_eggs":
        return s["status_add_eggs"].format(
            egg_count=egg_count,
            doneness=dn,
            time=format_mm_ss(total_seconds or 0),
        )
    if stage == "countdown":
        return s["status_countdown"].format(doneness=dn, egg_count=egg_count)
    return s["status_done"]


def _expected_action_label(stage: str, doneness: str | None, lang: str = "English") -> str:
    if stage == "idle" and not doneness:
        return STRINGS[lang]["action_no_doneness"]
    return STRINGS[lang].get(f"action_{stage}", "?")


def _controls_locked(stage: str) -> bool:
    return stage in {"countdown", "done"}


def _action_button_update(stage: str, doneness: str | None, lang: str = "English") -> Any:
    s = STRINGS[lang]
    if stage == "countdown":
        return gr.update(value=s["action_countdown"], visible=True, interactive=False)
    if stage == "done":
        return gr.update(value=s["action_done"], visible=True, interactive=False)
    if stage == "idle" and not doneness:
        return gr.update(value=s["action_no_doneness"], visible=True, interactive=False)
    return gr.update(value=s.get(f"action_{stage}", "?"), visible=True, interactive=True)


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
    lang: str = "English",
    status_override: str | None = None,
):
    """Returns 7-tuple: (status, debug, timer_html, btn_action, egg_interactive, don_interactive, custom_vis)."""
    display_seconds = remaining_seconds if stage in {"countdown", "done"} else total_seconds
    display_text = PLACEHOLDER_TIME if display_seconds <= 0 else format_mm_ss(display_seconds)
    status = status_override or _build_status(stage, egg_count, doneness, total_seconds, lang)
    debug_text = _build_debug_text(
        stage=stage,
        source=source,
        egg_count=egg_count,
        doneness=doneness,
        running=running,
        total_seconds=total_seconds,
        remaining_seconds=remaining_seconds,
    )
    locked = _controls_locked(stage)
    custom_visible = stage == "idle" and doneness == "Custom"
    return (
        status,
        debug_text,
        _timer_html(display_text, lang, stage),
        _action_button_update(stage, doneness, lang),
        gr.update(interactive=not locked),
        gr.update(interactive=not locked),
        gr.update(visible=custom_visible),
    )


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def preview_settings(
    egg_count: int,
    doneness: str | None,
    stage: str,
    running: bool,
    remaining_seconds: int,
    custom_seconds: int,
    lang: str,
):
    """Fires when egg_count, doneness, or custom_time_slider changes. Returns 10-tuple."""
    total_seconds = calculate_cook_seconds(egg_count, doneness, custom_seconds) if doneness else 0

    if stage == "idle":
        status, debug_text, timer_html, btn_action, egg_update, don_update, custom_vis = _render_screen(
            stage="idle",
            source="preview_idle",
            egg_count=egg_count,
            doneness=doneness,
            total_seconds=total_seconds,
            remaining_seconds=total_seconds,
            running=False,
            lang=lang,
        )
        return (
            total_seconds,   # total_state
            total_seconds,   # remaining_state
            timer_html,      # timer_display
            status,          # status_md
            btn_action,      # btn_action
            debug_text,      # debug_text
            egg_update,      # egg_count
            don_update,      # doneness
            custom_vis,      # custom_time_slider
            custom_seconds,  # custom_seconds_state
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
    locked = _controls_locked(stage)
    return (
        total_seconds,
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        debug_text,
        gr.update(interactive=not locked),
        gr.update(interactive=not locked),
        gr.update(),
        custom_seconds,
    )


def handle_action(
    stage: str,
    egg_count: int,
    doneness: str | None,
    total_seconds: int,
    custom_seconds: int,
    lang: str,
):
    """Handles action button click. Returns 13-tuple."""
    if stage == "idle":
        if not doneness:
            return (
                stage, total_seconds, total_seconds, False, 0.0,
                gr.update(active=False),
                *_render_screen(
                    stage="idle", source="action_idle_blocked",
                    egg_count=egg_count, doneness=doneness,
                    total_seconds=0, remaining_seconds=0, running=False,
                    lang=lang, status_override=STRINGS[lang]["status_blocked"],
                ),
            )
        new_total = calculate_cook_seconds(egg_count, doneness, custom_seconds)
        return (
            "boil", new_total, new_total, False, 0.0,
            gr.update(active=False),
            *_render_screen(
                stage="boil", source="action_to_boil",
                egg_count=egg_count, doneness=doneness,
                total_seconds=new_total, remaining_seconds=new_total, running=False,
                lang=lang,
            ),
        )

    if stage == "boil":
        return (
            "simmer", total_seconds, total_seconds, False, 0.0,
            gr.update(active=False),
            *_render_screen(
                stage="simmer", source="action_to_simmer",
                egg_count=egg_count, doneness=doneness,
                total_seconds=total_seconds, remaining_seconds=total_seconds, running=False,
                lang=lang,
            ),
        )

    if stage == "simmer":
        return (
            "add_eggs", total_seconds, total_seconds, False, 0.0,
            gr.update(active=False),
            *_render_screen(
                stage="add_eggs", source="action_to_add_eggs",
                egg_count=egg_count, doneness=doneness,
                total_seconds=total_seconds, remaining_seconds=total_seconds, running=False,
                lang=lang,
            ),
        )

    if stage == "add_eggs":
        end_timestamp = time.time() + total_seconds
        return (
            "countdown", total_seconds, total_seconds, True, end_timestamp,
            gr.update(active=True),
            *_render_screen(
                stage="countdown", source="action_begin_countdown",
                egg_count=egg_count, doneness=doneness,
                total_seconds=total_seconds, remaining_seconds=total_seconds, running=True,
                lang=lang,
            ),
        )

    return (
        stage, total_seconds, total_seconds, False, 0.0,
        gr.update(active=False),
        *_render_screen(
            stage=stage, source="action_noop",
            egg_count=egg_count, doneness=doneness,
            total_seconds=total_seconds, remaining_seconds=total_seconds, running=False,
            lang=lang,
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
    lang: str,
):
    """Fires every second during countdown. Returns 11-tuple."""
    if stage != "countdown" or not running:
        return (
            stage, remaining_seconds, running,
            gr.update(), gr.update(), gr.update(), gr.update(),
            gr.update(), gr.update(), gr.update(),
            gr.update(active=False),
        )

    new_remaining = max(0, int(end_timestamp - time.time()))

    if new_remaining > 0:
        debug_text = _build_debug_text(
            stage=stage, source="tick_countdown",
            egg_count=egg_count, doneness=doneness,
            running=True, total_seconds=total_seconds, remaining_seconds=new_remaining,
        )
        return (
            stage, new_remaining, True,
            _timer_html(format_mm_ss(new_remaining), lang, stage),
            debug_text,
            gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
            gr.update(active=True),
        )

    dn = _display_doneness(doneness, lang)
    done_message = STRINGS[lang]["status_done_detail"].format(doneness=dn)
    status, debug_text, timer_html, btn_action, egg_update, don_update, custom_vis = _render_screen(
        stage="done", source="tick_done",
        egg_count=egg_count, doneness=doneness,
        total_seconds=total_seconds, remaining_seconds=0, running=False,
        lang=lang, status_override=done_message,
    )
    return (
        "done", 0, False,
        timer_html, debug_text, status, btn_action,
        egg_update, don_update, custom_vis,
        gr.update(active=False),
    )


def reset_ui(lang: str):
    """Resets to idle, preserving current language. Returns 14-tuple."""
    s = STRINGS[lang]
    doneness_choices = DONENESS_CHOICES[lang]
    return (
        "idle", 0, 0, False, 0.0,
        gr.update(active=False),
        _build_status("idle", DEFAULT_EGG_COUNT, None, 0, lang),
        _build_debug_text(
            stage="idle", source="reset_ui",
            egg_count=DEFAULT_EGG_COUNT, doneness=None,
            running=False, total_seconds=0, remaining_seconds=0,
        ),
        _timer_html(PLACEHOLDER_TIME, lang, "idle"),
        gr.update(value=s["action_no_doneness"], visible=True, interactive=False),
        gr.update(value=DEFAULT_EGG_COUNT, interactive=True),
        gr.update(value=DEFAULT_EGG_COUNT),
        gr.update(value=None, interactive=True, choices=doneness_choices),
        gr.update(visible=False),
    )


def change_language(
    lang: str,
    stage: str,
    egg_count: int,
    doneness: str | None,
    total_seconds: int,
    remaining_seconds: int,
    running: bool,
    custom_seconds: int,
):
    """Re-renders UI text when language toggle changes. Returns 8-tuple."""
    s = STRINGS[lang]
    doneness_choices = DONENESS_CHOICES[lang]
    display_secs = remaining_seconds if stage in {"countdown", "done"} else total_seconds
    display_text = PLACEHOLDER_TIME if display_secs <= 0 else format_mm_ss(display_secs)
    if stage == "done":
        dn = _display_doneness(doneness, lang)
        status = s["status_done_detail"].format(doneness=dn)
    else:
        status = _build_status(stage, egg_count, doneness, total_seconds, lang)
    custom_visible = stage == "idle" and doneness == "Custom"
    return (
        lang,
        s["app_title"],
        s["app_subtitle"],
        status,
        _timer_html(display_text, lang, stage),
        _action_button_update(stage, doneness, lang),
        gr.update(choices=doneness_choices, label=s["label_doneness"]),
        gr.update(visible=custom_visible),
    )


def set_initial_language(browser_lang: str):
    """Detects browser language on page load, sets UI language. Returns 8-tuple."""
    if browser_lang and any(x in browser_lang for x in ("zh-HK", "zh-TW", "zh-Hant", "yue")):
        lang = "廣東話"
    else:
        lang = "English"
    s = STRINGS[lang]
    doneness_choices = DONENESS_CHOICES[lang]
    return (
        lang,
        lang,  # lang_toggle value
        s["app_title"],
        s["app_subtitle"],
        s["status_welcome"],
        _timer_html(PLACEHOLDER_TIME, lang, "idle"),
        gr.update(value=s["action_no_doneness"], visible=True, interactive=False),
        gr.update(choices=doneness_choices, label=s["label_doneness"]),
    )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

_INIT_LANG = "English"
_INIT_S = STRINGS[_INIT_LANG]
_INIT_CHOICES = DONENESS_CHOICES[_INIT_LANG]

with gr.Blocks(title="Egg Timer / 焓蛋計時小幫手") as demo:

    title_md = gr.Markdown(_INIT_S["app_title"])
    subtitle_md = gr.Markdown(_INIT_S["app_subtitle"])

    lang_toggle = gr.Radio(
        choices=["廣東話", "English"],
        value=_INIT_LANG,
        label="Language / 語言",
    )

    with gr.Row():
        with gr.Column(scale=1):
            with gr.Row():
                egg_count_num = gr.Number(
                    value=DEFAULT_EGG_COUNT,
                    minimum=1,
                    maximum=12,
                    step=1,
                    label="雞蛋數量 / No. of Eggs",
                    scale=3,
                )
                egg_reset_btn = gr.Button("↺", scale=0, min_width=50)
            egg_count = gr.Slider(
                minimum=1,
                maximum=12,
                step=1,
                value=DEFAULT_EGG_COUNT,
                show_label=False,
            )
        doneness = gr.Radio(
            choices=_INIT_CHOICES,
            value=None,
            label=_INIT_S["label_doneness"],
            scale=1,
        )
        custom_time_slider = gr.Slider(
            minimum=60,
            maximum=900,
            step=5,
            value=DEFAULT_CUSTOM_SECONDS,
            label="Custom / 自訂 (s)",
            visible=False,
            scale=1,
        )

    # State
    stage_state = gr.State("idle")
    total_state = gr.State(0)
    remaining_state = gr.State(0)
    running_state = gr.State(False)
    end_ts_state = gr.State(0.0)
    lang_state = gr.State(_INIT_LANG)
    custom_seconds_state = gr.State(DEFAULT_CUSTOM_SECONDS)

    status_md = gr.Markdown(_build_status("idle", DEFAULT_EGG_COUNT, None, None, _INIT_LANG))
    timer_display = gr.HTML(_timer_html(PLACEHOLDER_TIME, _INIT_LANG, "idle"))
    debug_text = gr.Textbox(
        value=_build_debug_text(
            stage="idle", source="init",
            egg_count=DEFAULT_EGG_COUNT, doneness=None,
            running=False, total_seconds=0, remaining_seconds=0,
        ),
        label="Debug state",
        interactive=False,
        visible=True,
    )

    with gr.Row():
        btn_action = gr.Button(
            _INIT_S["action_no_doneness"],
            variant="primary",
            visible=True,
            interactive=False,
        )
        btn_reset = gr.Button("重新開始 / Start Over")

    ticker = gr.Timer(value=1.0, active=False)

    # Auto-detect browser language on page load
    demo.load(
        fn=set_initial_language,
        inputs=[],
        outputs=[lang_state, lang_toggle, title_md, subtitle_md, status_md, timer_display, btn_action, doneness],
        js="() => [navigator.language || 'en']",
    )

    # Language toggle
    lang_toggle.change(
        fn=change_language,
        inputs=[lang_toggle, stage_state, egg_count, doneness, total_state, remaining_state, running_state, custom_seconds_state],
        outputs=[lang_state, title_md, subtitle_md, status_md, timer_display, btn_action, doneness, custom_time_slider],
    )

    # Egg count: sync number ↔ slider (slider is primary source of truth for preview_settings)
    egg_count.change(
        fn=lambda x: gr.update(value=x),
        inputs=[egg_count],
        outputs=[egg_count_num],
    )
    egg_count_num.change(
        fn=lambda x: gr.update(value=x),
        inputs=[egg_count_num],
        outputs=[egg_count],
    )
    egg_reset_btn.click(
        fn=lambda: (gr.update(value=DEFAULT_EGG_COUNT), gr.update(value=DEFAULT_EGG_COUNT)),
        inputs=[],
        outputs=[egg_count, egg_count_num],
    )

    # Settings preview (egg_count, doneness, custom_time_slider)
    _preview_inputs = [egg_count, doneness, stage_state, running_state, remaining_state, custom_seconds_state, lang_state]
    _preview_outputs = [total_state, remaining_state, timer_display, status_md, btn_action, debug_text, egg_count, doneness, custom_time_slider, custom_seconds_state]
    for _comp in (egg_count, doneness, custom_time_slider):
        _comp.change(fn=preview_settings, inputs=_preview_inputs, outputs=_preview_outputs)

    btn_action.click(
        fn=handle_action,
        inputs=[stage_state, egg_count, doneness, total_state, custom_seconds_state, lang_state],
        outputs=[
            stage_state, total_state, remaining_state, running_state, end_ts_state, ticker,
            status_md, debug_text, timer_display, btn_action, egg_count, doneness, custom_time_slider,
        ],
    )

    btn_reset.click(
        fn=reset_ui,
        inputs=[lang_state],
        outputs=[
            stage_state, total_state, remaining_state, running_state, end_ts_state, ticker,
            status_md, debug_text, timer_display, btn_action,
            egg_count, egg_count_num, doneness, custom_time_slider,
        ],
    )

    ticker.tick(
        fn=tick,
        inputs=[stage_state, running_state, end_ts_state, remaining_state, egg_count, doneness, total_state, lang_state],
        outputs=[
            stage_state, remaining_state, running_state,
            timer_display, debug_text, status_md, btn_action,
            egg_count, doneness, custom_time_slider,
            ticker,
        ],
    )


if __name__ == "__main__":
    demo.launch(ssr_mode=False)
