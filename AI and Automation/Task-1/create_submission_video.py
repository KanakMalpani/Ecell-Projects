"""Generate a short submission demo video explaining the 10-K risk classifier."""

from __future__ import annotations

import asyncio
import json
import textwrap
from pathlib import Path

import edge_tts
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "video"
SLIDES_DIR = OUTPUT_DIR / "slides"
AUDIO_DIR = OUTPUT_DIR / "audio"
REPORT_PATH = PROJECT_ROOT / "reports" / "evaluation_report.json"

WIDTH, HEIGHT = 1920, 1080
BG = "#0f172a"
ACCENT = "#38bdf8"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
SUCCESS = "#4ade80"

VOICE = "en-US-GuyNeural"

SLIDES = [
    {
        "id": "01_title",
        "title": "10-K Financial Risk Classifier",
        "subtitle": "E-Cell AI & Automation — Task 1",
        "bullets": [
            "End-to-end ML pipeline for SEC filing analysis",
            "Classifies financial risk: low · medium · high",
        ],
        "narration": (
            "Welcome to the 10-K Financial Risk Classifier, "
            "an end-to-end machine learning system built for the "
            "E-Cell AI and Automation assignment."
        ),
    },
    {
        "id": "02_problem",
        "title": "The Problem",
        "subtitle": "Document intelligence on SEC 10-K filings",
        "bullets": [
            "10-K reports = annual filings by US public companies",
            "Dataset: Hugging Face 10-K SEC filings (800 loaded, 283 kept)",
            "Goal: predict financial risk level from filing text",
        ],
        "narration": (
            "The system classifies SEC 10-K annual filings into three risk levels: "
            "low, medium, and high, using text from company risk disclosures."
        ),
    },
    {
        "id": "03_pipeline",
        "title": "5-Stage Pipeline",
        "subtitle": "From raw text to live predictions",
        "flow": [
            "1. Preprocess",
            "2. TF-IDF Features",
            "3. Train Models",
            "4. Evaluate",
            "5. FastAPI",
        ],
        "narration": (
            "The pipeline has five stages. First, download and preprocess filings "
            "from Hugging Face. Then engineer TF-IDF features, train three boosting "
            "models, evaluate them, and deploy the best model through FastAPI."
        ),
    },
    {
        "id": "04_labels",
        "title": "Label Creation",
        "subtitle": "Derived from the Risk Factors section",
        "bullets": [
            "High-risk keywords (litigation, bankruptcy) weighted ×3",
            "Medium-risk keywords (uncertain, regulatory) weighted ×1",
            "Score → rank → split into 3 equal groups (low / med / high)",
        ],
        "narration": (
            "Since the dataset has no labels, we create them from the Risk Factors "
            "section using keyword scoring, then split filings into low, medium, "
            "and high risk groups."
        ),
    },
    {
        "id": "05_features",
        "title": "Feature Engineering",
        "subtitle": "TF-IDF + custom numeric features",
        "bullets": [
            "TF-IDF: 5000 features, unigrams + bigrams",
            "Custom: word counts per section, risk/total length ratio",
            "Label score is NOT used as a feature (no leakage)",
        ],
        "narration": (
            "Features include TF-IDF with unigrams and bigrams, plus custom features "
            "like word counts and risk section ratios, without using the label score "
            "to avoid leakage."
        ),
    },
    {
        "id": "06_models",
        "title": "Model Comparison",
        "subtitle": "80/20 stratified split · macro F1",
        "table": True,
        "narration": (
            "We trained XGBoost, AdaBoost, and CatBoost on the same features. "
            "XGBoost achieved the best results with 74 percent accuracy "
            "and a macro F1 score of 0.71."
        ),
    },
    {
        "id": "07_results",
        "title": "Best Model: XGBoost",
        "subtitle": "Balanced performance across risk classes",
        "confusion": True,
        "narration": (
            "High-risk filings were detected reliably. Medium risk was the hardest "
            "class due to overlapping language. The confusion matrix shows "
            "XGBoost's overall balanced performance."
        ),
    },
    {
        "id": "08_api",
        "title": "Live API Deployment",
        "subtitle": "FastAPI — POST /predict",
        "code": (
            'POST /predict\n'
            '{"text": "litigation, covenant breaches..."}\n'
            '→ {"label": "high", "confidence": 0.85}'
        ),
        "narration": (
            "The trained model is served through a FastAPI endpoint. "
            "Send filing text to POST slash predict, and receive a risk label "
            "with a confidence score."
        ),
    },
]


def _setup_figure() -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(WIDTH / 100, HEIGHT / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _draw_header(ax: plt.Axes, title: str, subtitle: str) -> None:
    ax.text(0.06, 0.88, title, fontsize=42, color=TEXT, fontweight="bold", va="top")
    ax.text(0.06, 0.80, subtitle, fontsize=22, color=ACCENT, va="top")
    ax.plot([0.06, 0.94], [0.76, 0.76], color="#334155", linewidth=2)


def _draw_bullets(ax: plt.Axes, bullets: list[str], y_start: float = 0.62) -> None:
    for index, bullet in enumerate(bullets):
        y = y_start - index * 0.1
        ax.add_patch(
            FancyBboxPatch(
                (0.06, y - 0.055),
                0.88,
                0.08,
                boxstyle="round,pad=0.01,rounding_size=0.015",
                facecolor="#1e293b",
                edgecolor="#334155",
                linewidth=1.5,
            )
        )
        ax.text(0.09, y, f"•  {bullet}", fontsize=20, color=TEXT, va="center")


def _draw_flow(ax: plt.Axes, steps: list[str]) -> None:
    x_positions = np.linspace(0.12, 0.88, len(steps))
    for index, (step, x) in enumerate(zip(steps, x_positions)):
        ax.add_patch(
            FancyBboxPatch(
                (x - 0.075, 0.42),
                0.15,
                0.14,
                boxstyle="round,pad=0.01,rounding_size=0.02",
                facecolor="#1e293b",
                edgecolor=ACCENT,
                linewidth=2,
            )
        )
        ax.text(x, 0.49, step, fontsize=16, color=TEXT, ha="center", va="center", fontweight="bold")
        if index < len(steps) - 1:
            ax.annotate(
                "",
                xy=(x_positions[index + 1] - 0.08, 0.49),
                xytext=(x + 0.08, 0.49),
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=2.5),
            )


def _load_metrics() -> dict:
    with REPORT_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _draw_model_table(ax: plt.Axes, report: dict) -> None:
    rows = [
        ("Model", "Accuracy", "F1 (macro)"),
        ("XGBoost", "74%", "0.71"),
        ("CatBoost", "72%", "0.68"),
        ("AdaBoost", "63%", "0.53"),
    ]
    y = 0.58
    for row_index, row in enumerate(rows):
        color = ACCENT if row_index == 0 else TEXT
        weight = "bold" if row_index == 0 else "normal"
        highlight = row_index == 1
        if highlight:
            ax.add_patch(
                FancyBboxPatch(
                    (0.14, y - 0.045),
                    0.72,
                    0.07,
                    boxstyle="round,pad=0.005,rounding_size=0.01",
                    facecolor="#14532d",
                    edgecolor=SUCCESS,
                    linewidth=2,
                )
            )
        ax.text(0.22, y, row[0], fontsize=22, color=SUCCESS if highlight else color, fontweight=weight, ha="left")
        ax.text(0.48, y, row[1], fontsize=22, color=SUCCESS if highlight else color, fontweight=weight, ha="center")
        ax.text(0.68, y, row[2], fontsize=22, color=SUCCESS if highlight else color, fontweight=weight, ha="center")
        y -= 0.09

    best = report["best_model"].upper()
    ax.text(0.5, 0.22, f"★ Best model: {best}", fontsize=26, color=SUCCESS, ha="center", fontweight="bold")


def _draw_confusion_matrix(ax: plt.Axes, matrix: list[list[int]]) -> None:
    labels = ["low", "medium", "high"]
    data = np.array(matrix)
    im_ax = ax.inset_axes([0.28, 0.18, 0.44, 0.48])
    im = im_ax.imshow(data, cmap="Blues", vmin=0, vmax=data.max())
    im_ax.set_xticks(range(3), labels, fontsize=14)
    im_ax.set_yticks(range(3), labels, fontsize=14)
    im_ax.set_xlabel("Predicted", fontsize=15, color=MUTED, labelpad=10)
    im_ax.set_ylabel("Actual", fontsize=15, color=MUTED, labelpad=10)
    im_ax.set_title("XGBoost Confusion Matrix", fontsize=18, color=TEXT, pad=12)
    for row in range(3):
        for col in range(3):
            color = TEXT if data[row, col] > data.max() / 2 else "#0f172a"
            im_ax.text(col, row, str(data[row, col]), ha="center", va="center", fontsize=18, color=color, fontweight="bold")
    plt.colorbar(im, ax=im_ax, fraction=0.046, pad=0.04)


def _draw_code_block(ax: plt.Axes, code: str) -> None:
    wrapped = "\n".join(textwrap.wrap(code, width=52)) if "\n" not in code else code
    ax.add_patch(
        FancyBboxPatch(
            (0.1, 0.25),
            0.8,
            0.38,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            facecolor="#1e293b",
            edgecolor=ACCENT,
            linewidth=2,
        )
    )
    ax.text(0.14, 0.56, wrapped, fontsize=22, color="#e2e8f0", va="top", family="monospace", linespacing=1.6)
    ax.text(0.5, 0.16, "Run: uvicorn api.app:app --reload  →  http://127.0.0.1:8000/docs", fontsize=18, color=MUTED, ha="center")


def render_slide(slide: dict, report: dict) -> Path:
    fig, ax = _setup_figure()
    _draw_header(ax, slide["title"], slide["subtitle"])

    if "bullets" in slide:
        _draw_bullets(ax, slide["bullets"])
    elif "flow" in slide:
        _draw_flow(ax, slide["flow"])
        ax.text(
            0.5,
            0.28,
            "run_pipeline.py orchestrates all stages end to end",
            fontsize=18,
            color=MUTED,
            ha="center",
        )
    elif slide.get("table"):
        _draw_model_table(ax, report)
    elif slide.get("confusion"):
        matrix = report["models"]["xgboost"]["confusion_matrix"]
        _draw_confusion_matrix(ax, matrix)
    elif "code" in slide:
        _draw_code_block(ax, slide["code"])

    output = SLIDES_DIR / f"{slide['id']}.png"
    # Fixed canvas size (no tight crop) so ffmpeg gets even 1920x1080 frames.
    fig.savefig(output, facecolor=BG, dpi=100)
    plt.close(fig)
    return output


async def synthesize_narration(slide: dict) -> Path:
    output = AUDIO_DIR / f"{slide['id']}.mp3"
    communicate = edge_tts.Communicate(slide["narration"], VOICE)
    await communicate.save(str(output))
    return output


def build_video(slide_specs: list[dict]) -> Path:
    clips = []
    for slide in slide_specs:
        audio = AudioFileClip(str(slide["audio"]))
        image = ImageClip(str(slide["image"])).with_duration(audio.duration).with_audio(audio)
        clips.append(image)

    final = concatenate_videoclips(clips, method="compose")
    output = OUTPUT_DIR / "submission_demo.mp4"
    final.write_videofile(
        str(output),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=[
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "main",
            "-movflags",
            "+faststart",
        ],
        logger=None,
    )
    for clip in clips:
        clip.close()
    final.close()
    return output


async def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    SLIDES_DIR.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)

    report = _load_metrics()
    rendered = []

    for slide in SLIDES:
        image_path = render_slide(slide, report)
        audio_path = await synthesize_narration(slide)
        rendered.append({"image": image_path, "audio": audio_path})
        print(f"Rendered slide: {slide['id']}")

    video_path = build_video(rendered)
    print(f"\nVideo saved to: {video_path}")


if __name__ == "__main__":
    asyncio.run(main())
