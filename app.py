import base64
import copy
import random
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from map_generator import (
    CHUNK_SIZE_OPTIONS,
    DEFAULT_CHUNK_SIZE,
    MAP_OPTION_COUNT,
    generate_maps,
)
from initiative_tracker import next_turn, ordered_combatants, roll_initiative


# Hier startet die App und hier werden die zwei Karten-Werkzeuge geladen.
st.set_page_config(page_title="DND Diceroller", page_icon="🎲", layout="wide")
image_pin_board = components.declare_component(
    "image_pin_board", path=str(Path(__file__).parent / "image_pin_component")
)
map_builder_component = components.declare_component(
    "map_builder", path=str(Path(__file__).parent / "map_builder_component")
)

# Diese Listen sagen der App, welche Würfel, Farben und Effekte es gibt.
PALETTE = ["#E76F51", "#2A9D8F", "#E9C46A", "#6C9A8B", "#F4A261"]
MAX_BOSSES = 10
ROLL_GLYPHS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%*+=?~^"
ROLL_STEPS = 12
DICE = {
    "D2": 2,
    "D4": 4,
    "D6": 6,
    "D8": 8,
    "D10": 10,
    "D12": 12,
    "D20": 20,
    "D50": 50,
    "D100": 100,
    "D250": 250,
}
EFFECTS = [
    "Vergiftet",
    "Müde",
    "Ohnmächtig",
    "Kalt",
    "Warm",
    "Unter Zauber",
    "Polymorph",
    "Wildshape",
    "Konzentration",
    "Gelähmt",
    "Gefangen",
    "Verwirrt",
    "Blindheit",
    "Fasziniert",
    "Betäubt",
]
ELEMENTS = [
    "Feuer",
    "Eis",
    "Gift",
    "Licht",
    "Schatten",
    "Pflanzen",
    "Gestein",
    "Metall",
    "Wasser",
    "Juwel",
]


# Kleine Helfer machen die Würfel und ihre Farben hübsch und lesbar.
def readable_text_color(hex_color: str) -> str:
    """Wählt anhand der Helligkeit einer Würfelfarbe eine gut lesbare Textfarbe."""
    red, green, blue = (int(hex_color[index : index + 2], 16) for index in (1, 3, 5))
    luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
    return "#17211E" if luminance > 0.58 else "#FFFFFF"


def darken_color(hex_color: str, factor: float = 0.22) -> str:
    """Verdunkelt eine Hex-Farbe um den angegebenen Anteil."""
    red, green, blue = (int(hex_color[index : index + 2], 16) for index in (1, 3, 5))
    darkened = tuple(max(0, int(channel * (1 - factor))) for channel in (red, green, blue))
    return "#" + "".join(f"{channel:02x}" for channel in darkened)


def die_action_icon(symbol_name: str) -> str:
    """Ordnet einer Aktionsauswahl das passende Symbol zu."""
    icons = {
        "Keine": "",
        "Heilung": "❤️",
        "Angriff": "⚔️",
        "Gift": "💀",
        "Ausweichen": "💨",
    }
    return icons.get(symbol_name, "")


def die_face(die_type: str, value: int) -> str:
    """Formatiert das sichtbare Ergebnis eines Würfels."""
    if die_type == "D2":
        return "X" if value == 1 else "O"
    return str(value)


def scramble_frames(face: str) -> list[str]:
    """Erzeugt Symbolzeilen für die Animation bis zum Würfelergebnis."""
    return [
        "".join(random.choice(ROLL_GLYPHS) for _ in face)
        for _ in range(ROLL_STEPS)
    ]


def die_shape_style(die_type: str) -> str:
    """Liefert CSS für die Form des kleinen Würfelsymbols."""
    shapes = {
        "D2": "border-radius: 50%; width: 14px; height: 14px;",
        "D4": "width: 14px; height: 14px; transform: rotate(45deg); border-radius: 3px;",
        "D6": "border-radius: 5px; width: 14px; height: 14px;",
        "D8": "width: 14px; height: 14px; transform: rotate(45deg); border-radius: 2px;",
        "D10": "clip-path: polygon(25% 6%, 75% 6%, 100% 50%, 75% 94%, 25% 94%, 0% 50%); width: 14px; height: 14px;",
        "D12": "clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%); width: 14px; height: 14px;",
        "D20": "clip-path: polygon(50% 0%, 62% 14%, 86% 18%, 100% 38%, 100% 62%, 86% 82%, 62% 86%, 50% 100%, 38% 86%, 14% 82%, 0% 62%, 0% 38%, 14% 18%, 38% 14%); width: 14px; height: 14px;",
        "D50": "clip-path: polygon(50% 0%, 63% 12%, 88% 21%, 100% 50%, 88% 79%, 63% 88%, 50% 100%, 37% 88%, 12% 79%, 0% 50%, 12% 21%, 37% 12%); width: 14px; height: 14px;",
        "D100": "clip-path: polygon(50% 0%, 64% 8%, 92% 22%, 100% 50%, 92% 78%, 64% 92%, 50% 100%, 36% 92%, 8% 78%, 0% 50%, 8% 22%, 36% 8%); width: 14px; height: 14px;",
    }
    return shapes.get(die_type, "border-radius: 4px; width: 14px; height: 14px;")


# Hier wird das Aussehen der ganzen Seite festgelegt.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
    .stApp {
        --app-text: #17211e;
        --paper: #f3f2eb;
        --panel: #ffffff;
        --forest: #193c32;
        --forest-light: #285c4d;
        --coral: #bd573d;
        --muted: #68766f;
        --menu-icon-fill: #ffffff;
        --menu-icon-stroke: #17211e;
        --panel-soft: color-mix(in srgb, var(--panel) 72%, var(--paper));
        --line: rgba(25, 60, 50, 0.18);
        background-color: var(--paper);
        background-image: repeating-linear-gradient(
            135deg, color-mix(in srgb, var(--app-text) 2%, transparent) 0,
            color-mix(in srgb, var(--app-text) 2%, transparent) 1px,
            transparent 1px, transparent 12px
        );
    }
    [data-testid="stAppViewContainer"] { background-color: var(--paper); }
    main#stMain {
        background-color: var(--background-color, var(--paper)) !important;
    }
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 4rem; }
    html, body, .stApp { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { color: var(--forest); }
    h2 { font-size: 1.15rem; }
    .eyebrow {
        color: var(--coral); font-size: 0.72rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.1em;
    }
    .masthead {
        display: flex; align-items: end; justify-content: space-between; gap: 2rem;
        padding: 0.6rem 0 1.5rem; margin-bottom: 1.2rem;
        border-bottom: 1px solid rgba(25, 60, 50, 0.18);
    }
    .hero-title {
        color: var(--forest); font: 3rem/1.08 'DM Serif Display', Georgia, serif;
        margin-top: 0.35rem;
    }
    .hero-subtitle { color: var(--muted); margin-top: 0.55rem; font-size: 0.95rem; }
    .masthead-mark {
        color: var(--forest); font-family: 'DM Serif Display', Georgia, serif;
        font-size: 1.15rem; border: 1px solid rgba(25, 60, 50, 0.25);
        border-radius: 6px; padding: 0.55rem 0.8rem; white-space: nowrap;
    }
    .masthead-mark span { color: var(--coral) !important; }
    .type-label {
        display: inline-flex; align-items: center; min-height: 2.4rem;
        color: var(--forest); font-size: 0.9rem; font-weight: 700;
    }
    .effects-panel-title { color: var(--forest); font-size: 1rem; font-weight: 700; }
    .st-key-boss_hp_panel {
        margin-bottom: 1rem; padding: 1rem;
        border: 1px solid rgba(25, 60, 50, 0.18);
        border-top: 3px solid var(--coral); border-radius: 6px;
        background: var(--panel);
        box-shadow: 0 8px 18px rgba(25, 60, 50, 0.05);
    }
    .boss-panel-title { color: var(--forest); font-size: 1rem; font-weight: 700; }
    .st-key-dice_selector_heading h2,
    .st-key-dice_selector_heading h3 {
        color: var(--app-text) !important;
    }
    .st-key-boss_hp_panel div[data-testid="stPopover"] {
        display: inline-flex !important; width: auto !important;
    }
    .st-key-boss_hp_panel div[data-testid="stPopover"] > div {
        width: auto !important; max-width: none !important;
    }
    .st-key-boss_hp_panel div[data-testid="stPopover"] button {
        width: 2.2rem !important; min-width: 2.2rem; max-width: 2.2rem;
        height: 2.2rem; min-height: 2.2rem; padding: 0;
        border: 0; border-radius: 50%; background: var(--forest); color: #fff;
        font-size: 1.35rem; line-height: 1;
    }
    .st-key-boss_hp_panel div[data-testid="stPopover"] button:hover {
        background: var(--forest-light); color: #fff;
    }
    [class*="st-key-boss_card_"] {
        margin-top: 0.75rem; padding: 0.75rem;
        border: 1px solid rgba(25, 60, 50, 0.14); border-radius: 5px;
        background: var(--panel-soft);
    }
    .boss-name { color: var(--forest); font-weight: 700; }
    .st-key-boss_hp_panel [class*="st-key-boss_card_"] [data-testid="stMarkdownContainer"] p {
        color: var(--app-text) !important;
    }
    .st-key-boss_hp_panel [data-testid="stProgress"] [data-testid="stMarkdownContainer"] {
        color: var(--app-text) !important;
    }
    .st-key-boss_hp_panel [data-testid="stProgressBarTrack"] {
        background-color: var(--panel-soft) !important;
    }
    .st-key-boss_hp_panel [data-testid="stProgressBarTrack"] > div {
        background-color: var(--coral) !important;
    }
    .st-key-boss_hp_panel [data-testid="stWidgetLabel"] p,
    .st-key-boss_hp_panel label {
        color: var(--app-text) !important;
    }
    .st-key-boss_hp_panel [data-testid="stCaptionContainer"] {
        color: var(--app-text) !important;
    }
    .st-key-boss_hp_panel [class*="st-key-apply_hp_change_"] button {
        background: #098aed; border-color: #098aed; color: #fff !important;
    }
    .st-key-boss_hp_panel [class*="st-key-apply_hp_change_"] button * {
        color: #fff !important;
    }
    .st-key-boss_hp_panel [class*="st-key-apply_hp_change_"] button:hover {
        background: #ff7575; border-color: #ff7575; color: #fff !important;
    }
    .st-key-boss_hp_panel [class*="st-key-delete_boss_"] button {
        width: 3rem; min-width: 3rem; height: 2.5rem; padding: 0;
    }
    .st-key-effects_panel {
        padding: 1rem; border: 1px solid rgba(25, 60, 50, 0.18);
        border-top: 3px solid var(--coral); border-radius: 6px;
        background: var(--panel);
        box-shadow: 0 8px 18px rgba(25, 60, 50, 0.05);
    }
    .st-key-effects_panel div[data-testid="stPopover"] {
        display: inline-flex !important; width: auto !important;
    }
    .st-key-effects_panel div[data-testid="stPopover"] > div {
        width: auto !important; max-width: none !important;
    }
    .st-key-effects_panel div[data-testid="stPopover"] button {
        width: 2.2rem !important; min-width: 2.2rem; max-width: 2.2rem;
        height: 2.2rem; min-height: 2.2rem; padding: 0;
        border: 0; border-radius: 50%; background: var(--forest); color: #fff;
        font-size: 1.35rem; line-height: 1;
    }
    .st-key-effects_panel div[data-testid="stPopover"] button:hover {
        background: var(--forest-light); color: #fff;
    }
    .effect-chip {
        display: inline-flex; align-items: center; min-height: 1.9rem;
        padding: 0.25rem 0.65rem; border: 1px solid rgba(25, 60, 50, 0.16);
        border-radius: 999px; background: rgba(42, 157, 143, 0.12);
        color: var(--forest); font-size: 0.8rem; font-weight: 600;
    }
    .effects-empty {
        margin-top: 1rem; padding: 1.15rem 0.6rem;
        border: 1px dashed rgba(25, 60, 50, 0.24); border-radius: 5px;
        background: var(--panel-soft); color: var(--muted);
        font-size: 0.82rem; text-align: center;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) {
        align-items: center; gap: 0.5rem; padding: 0.35rem 0.55rem;
        margin-bottom: 0.55rem; border: 1px solid rgba(25, 60, 50, 0.16);
        border-left: 3px solid var(--coral); border-radius: 6px;
        background: var(--panel-soft);
        box-sizing: border-box;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) > div[data-testid="column"] {
        min-width: 0;
    }
    .roll-summary {
        display: flex; justify-content: space-between; align-items: center;
        border-top: 1px solid rgba(25, 60, 50, 0.18);
        border-bottom: 1px solid rgba(25, 60, 50, 0.18);
        padding: 0.75rem 0; margin: 0.4rem 0 1.1rem; color: var(--muted);
        font-size: 0.86rem;
    }
    .roll-summary strong { color: var(--forest); font-size: 1.3rem; }
    .result-heading { margin: 0.25rem 0 1.2rem; }
    .result-kicker {
        color: var(--coral); font-size: 0.7rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.09em;
    }
    .result-title { color: var(--forest); font-size: 1.05rem; font-weight: 700; margin-top: 0.25rem; }
    .image-mode-preview { margin-top: 1rem; }
    div[data-testid="stMetric"] {
        background: var(--panel); border-left: 3px solid var(--coral);
        padding: 0.8rem 1rem; border-radius: 4px;
    }
    div[data-testid="stMetricLabel"] { color: var(--muted); }
    div[data-testid="stMetricValue"] { color: var(--forest); }
    div[data-testid="stPopover"] {
        display: flex !important; width: 100% !important; max-width: 100%;
    }
    div[data-testid="stPopover"] > div {
        width: 100% !important; max-width: 100% !important;
    }
    div[data-testid="stPopover"] button {
        min-height: 2.9rem; padding: 0.55rem 1.1rem; border-color: rgba(25, 60, 50, 0.25);
        color: var(--forest); background: var(--panel);
        border-radius: 5px; font-size: 0.84rem; font-weight: 700;
        white-space: nowrap; min-width: 0; width: 100% !important;
        max-width: 100%; overflow: visible; text-overflow: clip;
    }
    div[data-testid="stPopover"] button > span,
    div[data-testid="stPopover"] button > div {
        white-space: nowrap; overflow: visible; text-overflow: clip;
    }
    div[data-testid="stPopover"] button [aria-hidden="true"] {
        display: none !important;
    }
    div[data-testid="stPopover"] button:hover {
        border-color: var(--coral); color: var(--coral);
    }
    div.stButton > button[kind="primary"] {
        background: var(--forest); border-color: var(--forest); color: #fff;
        min-height: 3.1rem; font-weight: 700; border-radius: 5px;
        box-shadow: 0 4px 12px rgba(25, 60, 50, 0.14);
        transition: background 160ms ease, transform 160ms ease;
    }
    div.stButton > button[kind="primary"]:hover {
        background: var(--forest-light); border-color: var(--forest-light);
        color: #fff; transform: translateY(-1px);
    }
    [class*="st-key-add_effect_button"] button,
    [class*="st-key-add_effect_button"] button * {
        color: var(--app-text) !important;
    }
    .die {
        position: relative; width: min(100%, 112px); aspect-ratio: 1;
        display: flex; align-items: center; justify-content: center;
        padding: 12px; border-radius: 18px; box-sizing: border-box;
        margin: 0 auto 14px; border: 2px solid rgba(255,255,255,0.34);
        box-shadow: 0 12px 20px rgba(27, 39, 33, 0.16),
                    inset 0 2px 0 rgba(255,255,255,0.28),
                    inset -8px -10px 18px rgba(0,0,0,0.12);
        transform: perspective(700px) rotateX(8deg) rotateY(-8deg);
    }
    .die-label {
        position: absolute; top: 10px; left: 12px; font-size: 0.62rem;
        font-weight: 700; letter-spacing: 0.06em; opacity: 0.82;
    }
    .die-value {
        display: block; height: 1em; overflow: hidden;
        font-size: clamp(2.2rem, 2.7vw, 3.2rem); line-height: 1;
        font-weight: 800; text-align: center; text-shadow: 0 2px 8px rgba(0,0,0,0.12);
    }
    .die-reel {
        display: flex; flex-direction: column; align-items: center;
    }
    .die-reel-face {
        display: flex; flex: 0 0 1em; height: 1em;
        align-items: center; justify-content: center; white-space: nowrap;
    }
    .die-symbol {
        position: absolute; right: 10px; bottom: 8px; width: 18px; height: 18px;
        display: flex; align-items: center; justify-content: center;
    }
    .die-badge {
        position: absolute; top: 10px; right: 10px; min-width: 20px; height: 20px;
        padding: 0 5px; display: inline-flex; align-items: center; justify-content: center;
        border-radius: 999px; background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.2); font-size: 0.75rem; line-height: 1;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06);
    }
    .die-shape {
        display: block; background: currentColor; border: 1px solid rgba(0,0,0,0.08);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.15);
    }
    @media (prefers-reduced-motion: reduce) {
        .die-reel { animation: none !important; transform: translateY(-12em); }
    }
    @media (max-width: 720px) {
        .block-container { padding-top: 1.2rem; }
        .hero-title { font-size: 2.35rem; }
        .masthead { align-items: start; gap: 0.8rem; }
        .masthead-mark { font-size: 0.9rem; padding: 0.45rem 0.6rem; }
        .hero-subtitle { max-width: 26rem; }
    }
    .stApp .stTextInput input,
    .stApp .stNumberInput input,
    .stApp .stTextArea textarea,
    .stApp [data-baseweb="select"] > div,
    .stApp [data-testid="stSelectbox"] > div,
    .stApp [data-testid="stSelectbox"] input,
    .stApp [data-testid="stFileUploader"] input {
        background: var(--panel) !important;
        color: var(--app-text) !important;
        border-color: var(--line) !important;
        box-shadow: none;
    }
    .stApp .stTextInput label,
    .stApp .stNumberInput label,
    .stApp .stTextArea label,
    .stApp [data-testid="stSelectbox"] label,
    .stApp [data-testid="stFileUploader"] label {
        color: var(--app-text) !important;
    }
    .stApp svg[viewBox="0 0 24 24"][fill="currentColor"],
    .stApp svg[viewBox="0 0 24 24"][fill="currentColor"] path,
    .stApp svg[viewBox="0 0 24 24"][fill="currentColor"] circle,
    .stApp svg[viewBox="0 0 24 24"][fill="currentColor"] line,
    .stApp svg[viewBox="0 0 24 24"][fill="currentColor"] polyline,
    .stApp svg[viewBox="0 0 24 24"][fill="currentColor"] path[d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"] {
        color: var(--app-text) !important;
        fill: var(--app-text) !important;
        stroke: var(--app-text) !important;
    }
    #MainMenu button {
        color: var(--app-text) !important;
        background: var(--panel) !important;
        border: 1px solid var(--line) !important;
        border-radius: 6px;
    }
    #MainMenu button svg,
    #MainMenu button svg * {
        color: var(--app-text) !important;
        fill: var(--menu-icon-fill) !important;
        stroke: var(--menu-icon-stroke) !important;
        opacity: 1 !important;
    }
    #MainMenu button:hover {
        background: var(--panel-soft) !important;
        border-color: var(--coral) !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
        background: var(--panel-soft) !important;
        border-color: var(--line) !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"],
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: var(--app-text) !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button {
        background: var(--app-text) !important;
        border-color: var(--app-text) !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button,
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button * {
        font-size: 0 !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button::after {
        content: "Upload";
        color: var(--paper) !important;
        font-size: 0.9rem !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button:hover {
        background: var(--forest-light) !important;
        border-color: var(--forest-light) !important;
    }
    .st-key-boss_hp_panel div[data-testid="stPopover"] button,
    .st-key-effects_panel div[data-testid="stPopover"] button,
    div.stButton > button[kind="primary"] {
        background: var(--panel) !important;
        border-color: var(--line) !important;
        color: var(--app-text) !important;
    }
    .st-key-boss_hp_panel div[data-testid="stPopover"] button:hover,
    .st-key-effects_panel div[data-testid="stPopover"] button:hover,
    div.stButton > button[kind="primary"]:hover {
        background: var(--panel-soft) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
@st.fragment(run_every="2s")
def sync_theme_styles():
    # Wenn Streamlit dunkel ist, ändern wir die passenden Farben mit.
    if st.context.theme.type == "dark":
        st.markdown(
            """
            <style>
            .stApp {
                --app-text: #f0f3f1;
                --paper: #151719;
                --panel: #202326;
                --forest: #e3e9e5;
                --forest-light: #c8d6cf;
                --coral: #ff9b80;
                --muted: #a6b0ab;
                --menu-icon-fill: #202326;
                --menu-icon-stroke: #f0f3f1;
                --panel-soft: #292d30;
                --line: rgba(240, 245, 242, 0.18);
                background-color: var(--paper) !important;
                background-image: repeating-linear-gradient(
                    135deg, rgba(240, 245, 242, 0.02) 0,
                    rgba(240, 245, 242, 0.02) 1px,
                    transparent 1px, transparent 12px
                ) !important;
            }
            [data-testid="stAppViewContainer"],
            main#stMain {
                background-color: var(--paper) !important;
            }
            .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button {
                background: #353535 !important;
                border-color: #4b4b4b !important;
            }
            .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button::after {
                color: #f0f3f1 !important;
            }
            .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button:hover {
                background: #454545 !important;
                border-color: #606060 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


sync_theme_styles()
# Hier merkt sich die App, was während dieser Sitzung passiert.
if "die_colors" not in st.session_state:
    st.session_state.die_colors = {}
if "die_actions" not in st.session_state:
    st.session_state.die_actions = {}
if "active_effects" not in st.session_state:
    st.session_state.active_effects = []
if "bosses" not in st.session_state:
    st.session_state.bosses = []
if "initiative_combatants" not in st.session_state:
    st.session_state.initiative_combatants = []
if "initiative_round" not in st.session_state:
    st.session_state.initiative_round = 1
if "initiative_active_id" not in st.session_state:
    st.session_state.initiative_active_id = None
if "image_upload_key" not in st.session_state:
    st.session_state.image_upload_key = "display_image_upload"
for boss in st.session_state.bosses:
    boss.setdefault("id", uuid.uuid4().hex)
    boss.setdefault("token", 1)
    boss.setdefault("element", ELEMENTS[0])


# Diese Funktionen reagieren auf Knöpfe und speichern kleine Änderungen.
def save_die_color(color_id: str, widget_key: str) -> None:
    """Übernimmt eine geänderte Würfelfarbe in den gespeicherten Spielzustand."""
    st.session_state.die_colors[color_id] = st.session_state[widget_key]


def save_die_action(die_id: str, widget_key: str) -> None:
    """Speichert das Aktionssymbol, das einem Würfel zugewiesen wurde."""
    st.session_state.die_actions[die_id] = st.session_state[widget_key]


def sync_count_from_slider(die_type: str) -> None:
    """Synchronisiert den Zahlenwert mit dem Schieberegler eines Würfeltyps."""
    st.session_state[f"count_input_{die_type}"] = st.session_state[f"count_{die_type}"]


def sync_count_from_input(die_type: str) -> None:
    """Synchronisiert den Schieberegler mit dem Zahlenwert eines Würfeltyps."""
    st.session_state[f"count_{die_type}"] = st.session_state[f"count_input_{die_type}"]


def add_effect(effect_name: str) -> None:
    """Fügt einen aktiven Effekt hinzu, sofern er noch nicht vorhanden ist."""
    if effect_name not in st.session_state.active_effects:
        st.session_state.active_effects.append(effect_name)


def remove_effect(effect_index: int) -> None:
    """Entfernt einen aktiven Effekt anhand seiner Position in der Liste."""
    del st.session_state.active_effects[effect_index]


def remove_boss(boss_id: str) -> None:
    """Entfernt den Gegner mit der angegebenen ID aus der HP-Verwaltung."""
    st.session_state.bosses = [
        boss for boss in st.session_state.bosses if boss["id"] != boss_id
    ]


def remove_initiative_combatant(combatant_id: str) -> None:
    # Entfernt eine Person aus der Zugliste.
    st.session_state.initiative_combatants = [
        combatant
        for combatant in st.session_state.initiative_combatants
        if combatant["id"] != combatant_id
    ]
    if st.session_state.initiative_active_id == combatant_id:
        st.session_state.initiative_active_id = None


def advance_initiative_turn() -> None:
    # Geht zur nächsten Person und zählt nach der letzten Person die Runde hoch.
    active_id, round_number = next_turn(
        st.session_state.initiative_combatants,
        st.session_state.initiative_active_id,
        st.session_state.initiative_round,
    )
    st.session_state.initiative_active_id = active_id
    st.session_state.initiative_round = round_number


def reset_initiative_tracker() -> None:
    # Räumt die Zugliste komplett leer.
    st.session_state.initiative_combatants = []
    st.session_state.initiative_round = 1
    st.session_state.initiative_active_id = None


def restart_initiative_round() -> None:
    # Beginnt Runde eins wieder mit der Person mit der höchsten Initiative.
    active_id, _ = next_turn(
        st.session_state.initiative_combatants,
        None,
        1,
    )
    st.session_state.initiative_round = 1
    st.session_state.initiative_active_id = active_id


def load_map_in_image_mode(svg: str) -> None:
    # Öffnet eine Karte im Bildmodus und löscht alte Markierungen.
    """Opens the selected generated map in the pin-enabled image mode."""
    st.session_state.display_image = svg.encode("utf-8")
    st.session_state.display_image_type = "image/svg+xml"
    st.session_state.image_pins = []
    st.session_state.image_pins_revision = 0
    st.session_state.fog_strokes = []
    st.session_state.fog_base_revealed = False
    st.session_state.fog_revision = st.session_state.get("fog_revision", 0) + 1
    st.session_state.image_pin_component_key = uuid.uuid4().hex
    st.session_state.image_upload_key = uuid.uuid4().hex
    st.session_state.app_mode = "Bild-Modus"


def open_built_map_in_image_mode(
    component_key: str,
    fallback_svg: str,
) -> None:
    component_state = st.session_state.get(component_key)
    svg = (
        component_state.get("svg")
        if isinstance(component_state, dict)
        and isinstance(component_state.get("svg"), str)
        else fallback_svg
    )
    load_map_in_image_mode(svg)


def start_map_builder(map_index: int, collection_name: str = "generated_maps") -> None:
    # Bereitet eine Karte für den Baumodus vor.
    """Opens a generated or temporarily saved map in the interactive builder."""
    map_data = st.session_state[collection_name][map_index]
    map_data.setdefault("builder_rooms", [dict(room) for room in map_data["rooms"]])
    map_data.setdefault(
        "builder_encounter_points",
        [dict(point) for point in map_data.get("encounter_points", [])],
    )
    map_data.setdefault("builder_decorations", [])
    map_data.setdefault("builder_custom_rooms", [])
    map_data.setdefault("builder_stairs", [])
    map_data.setdefault("builder_lights", [])
    map_data.setdefault("builder_terrain", [])
    map_data.setdefault("builder_darkness_enabled", False)
    map_data.setdefault("builder_grid_visible", True)
    map_data.setdefault("builder_coordinates_visible", False)
    map_data.setdefault("builder_light_markers_visible", True)
    map_data.setdefault("builder_svg", map_data["svg"])
    map_data.setdefault("builder_revision", 0)
    map_data.setdefault("builder_selected_id", None)
    st.session_state.map_builder_collection = collection_name
    st.session_state.map_builder_index = map_index


def start_saved_map_builder(map_index: int) -> None:
    start_map_builder(map_index, "saved_maps")


def save_map_temporarily(
    map_index: int,
    collection_name: str = "generated_maps",
) -> None:
    # Macht eine Kopie, die nur für kurze Zeit in der Sitzung bleibt.
    saved_maps = st.session_state.setdefault("saved_maps", [])
    map_copy = copy.deepcopy(st.session_state[collection_name][map_index])
    map_copy["saved_id"] = uuid.uuid4().hex
    saved_maps.append(map_copy)
    if len(saved_maps) > 8:
        del saved_maps[0]


def remove_saved_map(saved_id: str) -> None:
    # Löscht eine einzelne gespeicherte Karte.
    st.session_state.saved_maps = [
        map_data
        for map_data in st.session_state.get("saved_maps", [])
        if map_data.get("saved_id") != saved_id
    ]


def clear_saved_maps() -> None:
    # Löscht alle gespeicherten Karten auf einmal.
    st.session_state.saved_maps = []


def return_to_map_gallery() -> None:
    """Closes the builder and returns to the generated map choices."""
    st.session_state.map_builder_index = None


# Hier beginnt der sichtbare Teil der Website mit Überschrift und Modi.
st.markdown(
    """
    <header class="masthead">
        <div>
            <div class="eyebrow">DND Diceroller</div>
            <div class="hero-title">Klapperkiste!</div>
        </div>
        <div class="masthead-mark">D2 <span style="color:#bd573d">·</span> D100</div>
    </header>
    """,
    unsafe_allow_html=True,
)

@st.fragment
def render_image_mode():
    # Hier lädst du Bilder hoch, setzt Pins und deckst den Nebel auf.
    st.subheader("Bild anzeigen")
    upload_column, _ = st.columns([1, 1])
    with upload_column:
        st.caption("Bild hierher ziehen oder über Upload auswählen.")
        uploaded_image = st.file_uploader(
            "Bild hochladen",
            type=["png", "jpg", "jpeg", "webp", "gif"],
            key=st.session_state.image_upload_key,
        )
    if uploaded_image is not None:
        image_bytes = uploaded_image.getvalue()
        if image_bytes != st.session_state.get("display_image"):
            st.session_state.display_image = image_bytes
            st.session_state.image_pins = []
            st.session_state.image_pins_revision = 0
            st.session_state.fog_strokes = []
            st.session_state.fog_base_revealed = False
            st.session_state.fog_revision = st.session_state.get("fog_revision", 0) + 1
            st.session_state.image_pin_component_key = uuid.uuid4().hex
        st.session_state.display_image_type = uploaded_image.type or "image/png"

    if st.session_state.get("display_image") is not None:
        st.session_state.setdefault("image_pins", [])
        st.session_state.setdefault("image_pins_revision", 0)
        st.session_state.setdefault("image_pin_component_key", uuid.uuid4().hex)
        st.session_state.setdefault("fog_strokes", [])
        st.session_state.setdefault("fog_base_revealed", False)
        st.session_state.setdefault("fog_revision", 0)
        with st.container(key="image_mode_preview"):
            selected_pin_label = st.selectbox(
                "Pin-Beschriftung",
                ["Monster", "Spieler", "Mimik", "Schatz", "Gefahr", "Ziel", "Sonstiges"],
                key="image_pin_label",
            )
            show_pin_details = st.toggle(
                "Pin Namen Ausschalten.",
                value=True,
                key="image_pin_details_visible",
            )
            fog_controls = st.columns([1.2, 1, 1])
            with fog_controls[0]:
                fog_enabled = st.toggle(
                    "Nebel des Krieges",
                    value=False,
                    key="fog_enabled",
                    help="Verdeckt die Karte. Aufgedeckte Bereiche bleiben sichtbar.",
                )
            with fog_controls[1]:
                fog_mode = st.selectbox(
                    "Nebel-Werkzeug",
                    ["Aufdecken", "Verdecken"],
                    key="fog_mode",
                    disabled=not fog_enabled,
                )
            with fog_controls[2]:
                fog_brush_size = st.slider(
                    "Pinselgröße",
                    min_value=3,
                    max_value=30,
                    value=10,
                    step=1,
                    format="%d%%",
                    key="fog_brush_size",
                    disabled=not fog_enabled,
                )
            fog_actions = st.columns(2)
            with fog_actions[0]:
                if st.button(
                    "Alles verdecken",
                    disabled=not fog_enabled,
                    key="fog_cover_all",
                    use_container_width=True,
                ):
                    st.session_state.fog_strokes = []
                    st.session_state.fog_base_revealed = False
                    st.session_state.fog_revision += 1
            with fog_actions[1]:
                if st.button(
                    "Alles aufdecken",
                    disabled=not fog_enabled,
                    key="fog_reveal_all",
                    use_container_width=True,
                ):
                    st.session_state.fog_strokes = []
                    st.session_state.fog_base_revealed = True
                    st.session_state.fog_revision += 1
            pins = image_pin_board(
                image_data=base64.b64encode(st.session_state.display_image).decode("ascii"),
                image_type=st.session_state.get("display_image_type", "image/png"),
                pins=st.session_state.image_pins,
                pins_revision=st.session_state.image_pins_revision,
                selected_label=selected_pin_label,
                show_pin_details=show_pin_details,
                fog_enabled=fog_enabled,
                fog_mode=fog_mode,
                fog_brush_size=fog_brush_size,
                fog_strokes=st.session_state.fog_strokes,
                fog_base_revealed=st.session_state.fog_base_revealed,
                fog_revision=st.session_state.fog_revision,
                key=f"image_pin_board_{st.session_state.image_pin_component_key}",
                default={
                    "revision": st.session_state.image_pins_revision,
                    "pins": st.session_state.image_pins,
                    "fog_revision": st.session_state.fog_revision,
                    "fog_strokes": st.session_state.fog_strokes,
                    "fog_base_revealed": st.session_state.fog_base_revealed,
                },
            )
            if isinstance(pins, dict) and isinstance(pins.get("pins"), list):
                revision = pins.get("revision")
                if isinstance(revision, int) and revision >= st.session_state.image_pins_revision:
                    st.session_state.image_pins = pins["pins"]
                    st.session_state.image_pins_revision = revision
                fog_revision = pins.get("fog_revision")
                if isinstance(fog_revision, int) and fog_revision >= st.session_state.fog_revision:
                    st.session_state.fog_strokes = pins.get("fog_strokes", [])
                    st.session_state.fog_base_revealed = (
                        pins.get("fog_base_revealed") is True
                    )
                    st.session_state.fog_revision = fog_revision
    else:
        st.info("Lade ein Bild hoch, um es hier groß anzuzeigen.")


def render_map_generator() -> None:
    # Hier stellst du den Kartengenerator ein und siehst die neuen Karten.
    builder_index = st.session_state.get("map_builder_index")
    if builder_index is not None:
        render_map_builder(
            builder_index,
            st.session_state.get("map_builder_collection", "generated_maps"),
        )
        return

    st.subheader("Acht Karten für dein Abenteuer")
    st.caption(
        "Erzeuge acht zufällige Karten für deine Runde. Wähle ein Thema oder mische "
        "Verlies, Wald, Höhle und Ruinen."
    )
    settings_column, _ = st.columns([1, 2])
    with settings_column:
        theme = st.selectbox(
            "Thema",
            ["Alle", "Verlies", "Wald", "Höhle", "Ruinen"],
            help="Alle mischt die vier Schauplätze; ein einzelnes Thema füllt alle acht Karten.",
            key="map_theme",
        )
        layout = st.selectbox(
            "Wegeführung",
            ["Zufällig", "Kreuzung"],
            help="Bei Zufällig wird jede Karte unabhängig kurvig oder als Kreuzung aufgebaut.",
            key="map_route_layout",
        )
        chunk_size = st.selectbox(
            "Kartengröße",
            CHUNK_SIZE_OPTIONS,
            index=CHUNK_SIZE_OPTIONS.index(DEFAULT_CHUNK_SIZE),
            format_func=lambda size: (
                f"{size[0]}x{size[1]} Chunks"
                + (" (Empfohlen)" if size == DEFAULT_CHUNK_SIZE else "")
            ),
            help="Bestimmt Breite und Höhe des Kartenrasters.",
            key="map_chunk_size",
        )
        room_count = st.slider(
            "Räume / Wegpunkte pro Karte",
            min_value=3,
            max_value=10,
            value=5,
            help="Legt die Anzahl der Räume im Verlies und der Wegpunkte in den anderen Karten fest.",
            key="map_room_count",
        )
        room_shape = st.selectbox(
            "Raumform im Verlies",
            ["Gemischt", "Eckig", "Organisch"],
            help="Bei Gemischt erhält jeder Raum zufällig eine eckige oder organische Form.",
            key="map_room_shape",
        )
        corridor_width = st.slider(
            "Wegbreite",
            min_value=1,
            max_value=3,
            value=1,
            help="Breite der Wege in Rasterfeldern.",
            key="map_corridor_width",
        )
        branch_count = st.slider(
            "Zusätzliche Abzweigungen",
            min_value=0,
            max_value=4,
            value=2,
            help="Bei Kreuzungen kommt die zentrale Querung zusätzlich zu diesen Abzweigungen hinzu.",
            key="map_branch_count",
        )
        include_encounter_points = st.checkbox(
            "Begegnungspunkte einzeichnen",
            value=False,
            help="Markiert Start, Begegnung, Gefahr und Schatz auf den Wegen bzw. in den Räumen.",
            key="map_encounter_points",
        )
    if st.button("Acht neue Maps generieren", type="primary"):
        st.session_state.generated_maps = generate_maps(
            layout=layout,
            room_count=room_count,
            chunk_size=chunk_size,
            theme=theme,
            room_shape=room_shape,
            branch_count=branch_count,
            corridor_width=corridor_width,
            include_encounter_points=include_encounter_points,
        )

    generated_maps = st.session_state.get("generated_maps", [])
    saved_maps = st.session_state.get("saved_maps", [])
    if not generated_maps and not saved_maps:
        st.info("Generiere acht Maps, um mögliche Schauplätze für deine Runde zu sehen.")
        return

    if not generated_maps:
        st.info("Generiere neue Maps, um weitere Schauplätze zu sehen.")

    for index, map_data in enumerate(generated_maps):
        if index % 4 == 0:
            columns = st.columns(4, gap="medium")
        with columns[index % 4]:
            with st.container(border=True):
                st.markdown(f"#### {map_data['title']}")
                st.caption(
                    f"{map_data['description']} · Wege: {map_data['layout']} · "
                    f"Thema: {map_data['theme']}"
                    + (
                        f" · Begegnungspunkte: {len(map_data['encounter_points'])}"
                        if map_data["encounter_points"]
                        else ""
                    )
                )
                svg_data = base64.b64encode(map_data["svg"].encode("utf-8")).decode(
                    "ascii"
                )
                st.markdown(
                    f'<img src="data:image/svg+xml;base64,{svg_data}" '
                    'alt="Zufällig generierte Karte" '
                    'style="display:block;width:100%;height:auto;border-radius:4px;">',
                    unsafe_allow_html=True,
                )
                st.button(
                    "Im Bildmodus öffnen",
                    key=f"open_generated_map_{index}",
                    use_container_width=True,
                    on_click=load_map_in_image_mode,
                    args=(map_data["svg"],),
                )
                st.button(
                    "Baumodus",
                    key=f"edit_generated_map_{index}",
                    use_container_width=True,
                    on_click=start_map_builder,
                    args=(index,),
                )
                st.button(
                    "Temporär speichern",
                    key=f"save_generated_map_{index}",
                    use_container_width=True,
                    on_click=save_map_temporarily,
                    args=(index,),
                    help="Behält eine Kopie nur für diese Sitzung. Bei mehr als acht Karten wird die älteste ersetzt.",
                )


    if saved_maps:
        st.divider()
        st.subheader("Temporär gespeicherte Karten")
        st.caption(
            "Diese Karten bleiben nur in der aktuellen Sitzung verfügbar. Beim "
            "Neuladen können sie verschwinden; spätestens beim Ende der Sitzung werden sie gelöscht. "
            "Es werden maximal acht Karten behalten."
        )
        if st.button("Alle temporären Karten löschen", key="clear_saved_maps"):
            clear_saved_maps()
            st.rerun()
        for index, map_data in enumerate(saved_maps):
            with st.container(border=True):
                st.markdown(f"#### {map_data['title']}")
                st.caption(f"{map_data['description']} · {map_data['theme']}")
                actions = st.columns(3)
                actions[0].button(
                    "Im Bildmodus öffnen",
                    key=f"open_saved_map_{index}",
                    use_container_width=True,
                    on_click=load_map_in_image_mode,
                    args=(map_data.get("builder_svg", map_data["svg"]),),
                )
                actions[1].button(
                    "Baumodus",
                    key=f"edit_saved_map_{index}",
                    use_container_width=True,
                    on_click=start_saved_map_builder,
                    args=(index,),
                )
                actions[2].button(
                    "Entfernen",
                    key=f"remove_saved_map_{index}",
                    use_container_width=True,
                    on_click=remove_saved_map,
                    args=(map_data["saved_id"],),
                )


def render_map_builder(
    map_index: int,
    collection_name: str = "generated_maps",
) -> None:
    # Hier kannst du Räume, Licht und Deko auf der Karte verändern.
    map_data = st.session_state[collection_name][map_index]
    st.subheader(f"Baumodus: {map_data['title']}")
    st.caption(
        "Ziehe Räume an eine neue Stelle und nutze den Griff unten rechts zum "
        "Ändern der Größe. Wähle eine Dekoration und klicke auf die Karte, um "
        "sie zu platzieren. Kisten, Fässer, Fackeln, Tische, Stühle, Betten, "
        "Bücherregale und Teppiche lassen sich anschließend ziehen und "
        "in 45-Grad-Schritten drehen und am Griff unten rechts größer oder "
        "kleiner ziehen. Begegnungspunkte lassen sich verschieben, "
        "umbenennen und entfernen. Mit „Raum: 4 Ecken setzen“ klickst du die "
        "Raumecken der Reihe nach an; mit dem Tür-Werkzeug kannst du Türen an "
        "Wänden hinzufügen oder entfernen. Mit dem Treppen-Werkzeug platzierst "
        "oder entfernst du Treppenmarker in Räumen und Gebäuden. Die letzten fünf Bearbeitungsschritte "
        "lassen sich rückgängig machen. Über „Dunkelheit“ kannst du die Karte "
        "abdunkeln und den Bereich um gesetzte Lichtquellen sichtbar lassen; "
        "deren Helligkeit passt du in der Gruppe „Auswahl bearbeiten“ an. "
        "Für Wasser, Lava oder Gruben wählst du einen Geländetyp, setzt mehrere "
        "Randpunkte und schließt die Fläche ab."
    )
    if not map_data["rooms"]:
        st.info(
            "Diese Karte hat keine vorgefertigten Räume. Du kannst mit „Raum: "
            "4 Ecken setzen“ eigene Räume zeichnen und Dekorationen oder "
            "Gebäude platzieren."
        )

    decoration_column, _ = st.columns([1, 2])
    with decoration_column:
        selected_decoration = st.selectbox(
            "Dekoration zum Platzieren",
            [
                "Auswählen",
                "Kiste",
                "Fass",
                "Fackel",
                "Tisch",
                "Stuhl",
                "Bett",
                "Bücherregal",
                "Teppich",
            ],
            key="map_builder_decoration_type_v3",
        )
        selected_terrain_type = st.selectbox(
            "Geländeart",
            ["Wasser", "Lava", "Grube"],
            key="map_builder_terrain_type",
        )

    builder_component_key = f"map_builder_{collection_name}_{map_index}"
    builder_state = map_builder_component(
        svg=map_data["svg"],
        rooms=map_data["builder_rooms"],
        encounter_points=map_data["builder_encounter_points"],
        decorations=map_data["builder_decorations"],
        custom_rooms=map_data["builder_custom_rooms"],
        stairs=map_data["builder_stairs"],
        lights=map_data["builder_lights"],
        terrain=map_data["builder_terrain"],
        darkness_enabled=map_data["builder_darkness_enabled"],
        grid_visible=map_data["builder_grid_visible"],
        coordinates_visible=map_data["builder_coordinates_visible"],
        light_markers_visible=map_data["builder_light_markers_visible"],
        selected_id=map_data.get("builder_selected_id"),
        selected_decoration=selected_decoration,
        selected_terrain_type=selected_terrain_type,
        revision=map_data["builder_revision"],
        key=builder_component_key,
        default={
            "svg": map_data.get("builder_svg", map_data["svg"]),
            "rooms": map_data["builder_rooms"],
            "encounter_points": map_data["builder_encounter_points"],
            "decorations": map_data["builder_decorations"],
            "custom_rooms": map_data["builder_custom_rooms"],
            "stairs": map_data["builder_stairs"],
            "lights": map_data["builder_lights"],
            "terrain": map_data["builder_terrain"],
            "darkness_enabled": map_data["builder_darkness_enabled"],
            "grid_visible": map_data["builder_grid_visible"],
            "coordinates_visible": map_data["builder_coordinates_visible"],
            "light_markers_visible": map_data["builder_light_markers_visible"],
            "selected_id": map_data.get("builder_selected_id"),
            "revision": map_data["builder_revision"],
        },
    )
    if isinstance(builder_state, dict):
        if isinstance(builder_state.get("svg"), str):
            map_data["builder_svg"] = builder_state["svg"]
        if isinstance(builder_state.get("rooms"), list):
            map_data["builder_rooms"] = builder_state["rooms"]
        if isinstance(builder_state.get("encounter_points"), list):
            map_data["builder_encounter_points"] = builder_state["encounter_points"]
        if isinstance(builder_state.get("decorations"), list):
            map_data["builder_decorations"] = builder_state["decorations"]
        if isinstance(builder_state.get("custom_rooms"), list):
            map_data["builder_custom_rooms"] = builder_state["custom_rooms"]
        if isinstance(builder_state.get("stairs"), list):
            map_data["builder_stairs"] = builder_state["stairs"]
        if isinstance(builder_state.get("lights"), list):
            map_data["builder_lights"] = builder_state["lights"]
        if isinstance(builder_state.get("terrain"), list):
            map_data["builder_terrain"] = builder_state["terrain"]
        if isinstance(builder_state.get("darkness_enabled"), bool):
            map_data["builder_darkness_enabled"] = builder_state["darkness_enabled"]
        if isinstance(builder_state.get("grid_visible"), bool):
            map_data["builder_grid_visible"] = builder_state["grid_visible"]
        if isinstance(builder_state.get("coordinates_visible"), bool):
            map_data["builder_coordinates_visible"] = builder_state["coordinates_visible"]
        if isinstance(builder_state.get("light_markers_visible"), bool):
            map_data["builder_light_markers_visible"] = builder_state["light_markers_visible"]
        if isinstance(builder_state.get("revision"), int):
            map_data["builder_revision"] = builder_state["revision"]
        map_data["builder_selected_id"] = builder_state.get("selected_id")

    action_columns = st.columns(3)
    with action_columns[0]:
        st.button(
            "Zurück zu den Karten",
            on_click=return_to_map_gallery,
            use_container_width=True,
        )
    with action_columns[1]:
        st.button(
            "Temporär speichern",
            key=f"save_built_map_{collection_name}_{map_index}",
            on_click=save_map_temporarily,
            args=(map_index, collection_name),
            use_container_width=True,
        )
    with action_columns[2]:
        st.button(
            "Im Bildmodus öffnen",
            key=f"open_built_map_{collection_name}_{map_index}",
            on_click=open_built_map_in_image_mode,
            args=(
                builder_component_key,
                map_data.get("builder_svg", map_data["svg"]),
            ),
            type="primary",
            use_container_width=True,
        )


mode = st.radio(
    "Modus",
    ["Würfel-Modus", "Bild-Modus", "Map generierer"],
    horizontal=True,
    key="app_mode",
)

if mode == "Bild-Modus":
    render_image_mode()
    st.stop()
if mode == "Map generierer":
    render_map_generator()
    st.stop()

# Links suchst du Würfel aus und legst ihre Anzahl fest.
controls, results, empty_space = st.columns([1, 2, 1], gap="large")
with controls:
    with st.container(key="dice_selector_heading"):
        st.subheader("Würfel auswählen")
    counts = {}
    for die_type in DICE:
        slider_key = f"count_{die_type}"
        input_key = f"count_input_{die_type}"
        if slider_key not in st.session_state:
            st.session_state[slider_key] = 0
        if input_key not in st.session_state:
            st.session_state[input_key] = st.session_state[slider_key]

        type_column, settings_column = st.columns([0.55, 3.35], gap="small")
        with type_column:
            st.markdown(f'<div class="type-label">{die_type}</div>', unsafe_allow_html=True)
        with settings_column:
            with st.popover(
                "⚙️ Einstellungen",
                use_container_width=False,
            ):
                st.caption(f"Würfel für {die_type}")
                if st.session_state[slider_key] == 0:
                    st.caption("Wähle zuerst mindestens einen Würfel dieser Art.")
                else:
                    symbol_options = ["Keine", "Heilung", "Angriff", "Gift", "Ausweichen"]
                    for die_index in range(st.session_state[slider_key]):
                        color_id = f"{die_type}_{die_index + 1}"
                        action_id = color_id
                        color_key = f"color_{color_id}"
                        action_key = f"action_{action_id}"
                        default_color = PALETTE[die_index % len(PALETTE)]
                        default_action = st.session_state.die_actions.get(action_id, "Keine")
                        if color_key not in st.session_state:
                            st.session_state[color_key] = st.session_state.die_colors.get(
                                color_id, default_color
                            )
                        if action_key not in st.session_state:
                            st.session_state[action_key] = default_action

                        st.write(f"Würfel {die_index + 1}")
                        color_column_ui, action_column_ui = st.columns([1.4, 1.2])
                        with color_column_ui:
                            st.color_picker(
                                f"Farbe {die_type} Würfel {die_index + 1}",
                                key=color_key,
                                on_change=save_die_color,
                                args=(color_id, color_key),
                                label_visibility="collapsed",
                            )
                        with action_column_ui:
                            selected_action = st.selectbox(
                                f"Symbol {die_type} Würfel {die_index + 1}",
                                options=symbol_options,
                                index=symbol_options.index(st.session_state[action_key]),
                                key=action_key,
                                on_change=save_die_action,
                                args=(action_id, action_key),
                                label_visibility="collapsed",
                            )
                            st.session_state.die_actions[action_id] = selected_action

        slider_column, input_column = st.columns([2, 1], gap="small")
        with slider_column:
            counts[die_type] = st.slider(
                f"Anzahl {die_type}",
                min_value=0,
                max_value=32,
                key=slider_key,
                on_change=sync_count_from_slider,
                args=(die_type,),
                label_visibility="collapsed",
            )
        with input_column:
            st.number_input(
                f"Direktwert {die_type}",
                min_value=0,
                max_value=32,
                step=1,
                key=input_key,
                on_change=sync_count_from_input,
                args=(die_type,),
                label_visibility="collapsed",
            )

    total_count = sum(counts.values())
    st.markdown(
        f'<div class="roll-summary"><span>Würfel im Tower</span><strong>{total_count}</strong></div>',
        unsafe_allow_html=True,
    )
    roll_clicked = st.button(
        "Würfel rollen",
        type="primary",
        use_container_width=True,
        disabled=total_count == 0,
    )

# Wenn du auf den Würfel-Knopf drückst, würfelt die App hier.
if roll_clicked:
    result_groups = []
    for die_type, count in counts.items():
        if count == 0:
            continue
        colors = [
            st.session_state.die_colors.get(
                f"{die_type}_{die_index + 1}", PALETTE[die_index % len(PALETTE)]
            )
            for die_index in range(count)
        ]
        actions = [
            st.session_state.die_actions.get(f"{die_type}_{die_index + 1}", "Keine")
            for die_index in range(count)
        ]
        values = [random.randint(1, DICE[die_type]) for _ in range(count)]
        result_groups.append(
            {
                "type": die_type,
                "values": values,
                "colors": colors,
                "actions": actions,
                "scrambles": [
                    scramble_frames(die_face(die_type, value)) for value in values
                ],
            }
        )
    st.session_state.last_roll = {
        "groups": result_groups,
        "animation_id": uuid.uuid4().hex,
    }

# In der Mitte siehst du die Würfel und ihre Ergebnisse.
with results:
    st.subheader("Auswertung")
    if "last_roll" in st.session_state:
        result = st.session_state.last_roll
        animation_name = f"die-roll-{result['animation_id']}"
        st.markdown(
            f"""
            <style>
            @keyframes {animation_name} {{
                from {{ transform: translateY(0); }}
                to {{ transform: translateY(-{ROLL_STEPS}em); }}
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        result_summary = " + ".join(
            f"{len(group['values'])}× {group['type']}" for group in result["groups"]
        )
        st.markdown(
            f'<div class="result-heading"><div class="result-kicker">Letzter Wurf</div>'
            f'<div class="result-title">{result_summary}</div></div>',
            unsafe_allow_html=True,
        )
        result_columns = st.columns(4)
        die_index = 0
        all_values = []
        for group in result["groups"]:
            group.setdefault(
                "scrambles",
                [scramble_frames(die_face(group["type"], value)) for value in group["values"]],
            )
            for value, color, action, scramble in zip(
                group["values"], group["colors"], group["actions"], group["scrambles"]
            ):
                all_values.append(value)
                face = die_face(group["type"], value)
                die_bg = darken_color(color, 0.2)
                text_color = readable_text_color(die_bg)
                action_symbol = die_action_icon(action)
                animation_delay = min(die_index * 18, 540)
                with result_columns[die_index % len(result_columns)]:
                    st.markdown(
                        f"""
                        <div class="die" style="background:linear-gradient(135deg, rgba(255,255,255,0.18), rgba(0,0,0,0.08)), {die_bg}; color:{text_color};">
                            <span class="die-badge">{action_symbol}</span>
                            <span class="die-label">{group['type']}</span>
                            <span class="die-value" role="img" aria-label="{face}">
                                <span class="die-reel" aria-hidden="true" style="animation: {animation_name} 1300ms cubic-bezier(0.12, 0.68, 0.24, 1) {animation_delay}ms both;">
                                    {''.join(f'<span class="die-reel-face">{frame}</span>' for frame in scramble)}
                                    <span class="die-reel-face">{face}</span>
                                </span>
                            </span>
                            <span class="die-symbol">
                                <span class="die-shape" style="{die_shape_style(group['type'])};"></span>
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                die_index += 1
        st.metric("Roll", sum(all_values))
    else:
        st.info("Wähle links Würfel aus und starte deinen Wurf.")

# Rechts verwaltest du Gegner, Lebenspunkte und die Reihenfolge der Züge.
with empty_space:
    with st.container(key="boss_hp_panel"):
        title_column, add_column = st.columns([4, 1], vertical_alignment="center")
        with title_column:
            st.markdown('<div class="boss-panel-title">Gegner-HP</div>', unsafe_allow_html=True)
            st.caption(f"{len(st.session_state.bosses)} / {MAX_BOSSES} HP-Leisten")
        with add_column:
            with st.popover(
                "+",
                use_container_width=False,
                disabled=len(st.session_state.bosses) >= MAX_BOSSES,
            ):
                with st.form("add_boss_form", clear_on_submit=True):
                    new_boss_name = st.text_input("Name des Gegners", key="new_boss_name")
                    new_boss_element = st.selectbox(
                        "Element",
                        ELEMENTS,
                        key="new_boss_element",
                    )
                    new_boss_token = st.number_input(
                        "Monstertoken",
                        min_value=1,
                        max_value=25,
                        value=1,
                        step=1,
                        key="new_boss_token",
                    )
                    new_boss_hp = st.number_input(
                        "Maximale HP",
                        min_value=1,
                        max_value=1300,
                        value=100,
                        step=1,
                        key="new_boss_hp",
                    )
                    add_boss_submitted = st.form_submit_button(
                        "Gegner hinzufügen", type="primary", use_container_width=True
                    )
                if add_boss_submitted:
                    if len(st.session_state.bosses) >= MAX_BOSSES:
                        st.error(f"Es können höchstens {MAX_BOSSES} HP-Leisten angelegt werden.")
                    elif new_boss_name.strip():
                        st.session_state.bosses.append(
                            {
                                "id": uuid.uuid4().hex,
                                "name": new_boss_name.strip(),
                                "element": new_boss_element,
                                "token": new_boss_token,
                                "max_hp": new_boss_hp,
                                "current_hp": new_boss_hp,
                            }
                        )
                    else:
                        st.error("Bitte gib einen Gegnernamen ein.")

        if not st.session_state.bosses:
            st.markdown('<div class="effects-empty">Noch keine Gegner angelegt</div>', unsafe_allow_html=True)

        for boss_index, boss in enumerate(st.session_state.bosses):
            boss_id = boss["id"]
            with st.container(key=f"boss_card_{boss_id}"):
                name_column, delete_column = st.columns([4, 1.3], vertical_alignment="center")
                with name_column:
                    dead_marker = " 💀" if boss["current_hp"] == 0 else ""
                    st.markdown(f"**{boss['name']}**{dead_marker}")
                    st.caption(f"Element: {boss['element']}")
                    st.caption(f"Monstertoken: {boss['token']}")
                with delete_column:
                    st.button(
                        "🗑️",
                        key=f"delete_boss_{boss_id}",
                        on_click=remove_boss,
                        args=(boss_id,),
                    )
                st.progress(
                    boss["current_hp"] / boss["max_hp"],
                    text=f'{boss["current_hp"]} / {boss["max_hp"]} HP',
                )
                with st.popover(
                    "⚙️",
                    key=f"edit_boss_{boss_id}",
                    use_container_width=False,
                ):
                    with st.form(f"edit_boss_form_{boss_id}"):
                        edited_name = st.text_input(
                            "Name des Gegners",
                            value=boss["name"],
                            key=f"boss_name_{boss_id}",
                        )
                        edited_element = st.selectbox(
                            "Element",
                            ELEMENTS,
                            index=ELEMENTS.index(boss["element"]),
                            key=f"boss_element_{boss_id}",
                        )
                        edited_token = st.number_input(
                            "Monstertoken",
                            min_value=1,
                            max_value=25,
                            value=boss["token"],
                            step=1,
                            key=f"boss_token_{boss_id}",
                        )
                        edited_max_hp = st.number_input(
                            "Maximale HP",
                            min_value=1,
                            max_value=1300,
                            value=boss["max_hp"],
                            step=1,
                            key=f"boss_max_hp_{boss_id}",
                        )
                        edit_submitted = st.form_submit_button(
                            "Speichern", type="primary", use_container_width=True
                        )
                    if edit_submitted:
                        if edited_name.strip():
                            boss["name"] = edited_name.strip()
                            boss["element"] = edited_element
                            boss["token"] = edited_token
                            boss["max_hp"] = edited_max_hp
                            boss["current_hp"] = min(boss["current_hp"], edited_max_hp)
                            st.rerun()
                        else:
                            st.error("Der Gegnername darf nicht leer sein.")

                with st.form(f"boss_hp_change_form_{boss_id}"):
                    hp_change = st.text_input(
                        "HP ändern",
                        key=f"hp_change_{boss_id}",
                        placeholder="+ HP hinzufügen,- HP abziehen",
                    )
                    change_submitted = st.form_submit_button(
                        "Anwenden", key=f"apply_hp_change_{boss_id}", use_container_width=True
                    )
                if change_submitted:
                    try:
                        hp_delta = int(hp_change.strip())
                    except ValueError:
                        st.error("Bitte gib eine ganze Zahl ein, zum Beispiel +13 oder -13.")
                    else:
                        boss["current_hp"] = max(
                            0, min(boss["max_hp"], boss["current_hp"] + hp_delta)
                        )
                        st.rerun()

    with st.container(key="initiative_tracker"):
        st.subheader("Initiative")
        initiative_combatants = ordered_combatants(
            st.session_state.initiative_combatants
        )
        st.caption(
            f"Runde {st.session_state.initiative_round}"
            + (
                f" · Am Zug: {next((combatant['name'] for combatant in initiative_combatants if combatant['id'] == st.session_state.initiative_active_id), 'Noch nicht gestartet')}"
            )
        )
        with st.form("add_initiative_combatant_form", clear_on_submit=True):
            combatant_name = st.text_input("Name")
            add_columns = st.columns(2)
            with add_columns[0]:
                combatant_type = st.selectbox(
                    "Teilnehmer",
                    ["Spieler", "Gegner", "NSC"],
                )
            with add_columns[1]:
                initiative_modifier = st.number_input(
                    "Initiative-Modifikator",
                    min_value=-20,
                    max_value=20,
                    value=0,
                    step=1,
                    help="Wird zum W20-Ergebnis addiert.",
                )
            add_combatant_submitted = st.form_submit_button(
                "Hinzufügen & W20 würfeln",
                type="primary",
                use_container_width=True,
                disabled=len(initiative_combatants) >= 30,
            )
        if add_combatant_submitted:
            if not combatant_name.strip():
                st.error("Bitte gib einen Namen ein.")
            elif len(initiative_combatants) >= 30:
                st.error("Der Initiative-Tracker kann höchstens 30 Teilnehmer verwalten.")
            else:
                roll = roll_initiative(int(initiative_modifier))
                st.session_state.initiative_combatants.append(
                    {
                        "id": uuid.uuid4().hex,
                        "name": combatant_name.strip(),
                        "type": combatant_type,
                        "modifier": int(initiative_modifier),
                        "initiative": roll,
                        "order": max(
                            (
                                combatant["order"]
                                for combatant in st.session_state.initiative_combatants
                            ),
                            default=-1,
                        ) + 1,
                    }
                )
                st.rerun()

        turn_controls = st.columns(2)
        turn_controls[0].button(
            "Nächster Zug",
            key="initiative_next_turn",
            type="primary",
            use_container_width=True,
            disabled=not initiative_combatants,
            on_click=advance_initiative_turn,
        )
        turn_controls[1].button(
            "Runde neu starten",
            key="initiative_restart_round",
            use_container_width=True,
            disabled=not initiative_combatants,
            on_click=restart_initiative_round,
        )
        if initiative_combatants:
            for position, combatant in enumerate(initiative_combatants, start=1):
                with st.container(border=True):
                    row = st.columns([0.6, 3, 1, 0.8])
                    row[0].write(f"**{position}.**")
                    row[1].write(
                        f"{'▶️ ' if combatant['id'] == st.session_state.initiative_active_id else ''}"
                        f"{combatant['name']} · {combatant['type']}"
                    )
                    row[2].write(
                        f"**{combatant['initiative']}**"
                        f" ({combatant['modifier']:+d})"
                    )
                    row[3].button(
                        "×",
                        key=f"remove_initiative_{combatant['id']}",
                        help=f"{combatant['name']} entfernen",
                        on_click=remove_initiative_combatant,
                        args=(combatant["id"],),
                    )
            st.button(
                "Kampf zurücksetzen",
                key="initiative_reset",
                on_click=reset_initiative_tracker,
                use_container_width=True,
            )
        else:
            st.info("Füge Spieler, Gegner oder NSC hinzu, um die Zugreihenfolge zu starten.")

    # Aktive Status-Effekte verwalten.
    with st.container(key="effects_panel"):
        title_column, add_column = st.columns([4, 1], vertical_alignment="center")
        with title_column:
            st.markdown('<div class="effects-panel-title">Effekte</div>', unsafe_allow_html=True)
        with add_column:
            with st.popover("+", use_container_width=False):
                selected_effect = st.selectbox(
                    "Effekt auswählen",
                    EFFECTS,
                    key="effect_to_add",
                    label_visibility="collapsed",
                )
                st.button(
                    "Hinzufügen",
                    key="add_effect_button",
                    type="primary",
                    use_container_width=True,
                    disabled=selected_effect in st.session_state.active_effects,
                    on_click=add_effect,
                    args=(selected_effect,),
                )

        if st.session_state.active_effects:
            for effect_index, effect in enumerate(st.session_state.active_effects):
                effect_column, remove_column = st.columns([5, 1], vertical_alignment="center")
                with effect_column:
                    st.markdown(f'<span class="effect-chip">{effect}</span>', unsafe_allow_html=True)
                with remove_column:
                    st.button(
                        "×",
                        key=f"remove_effect_{effect_index}",
                        on_click=remove_effect,
                        args=(effect_index,),
                    )
        else:
            st.markdown('<div class="effects-empty">Keine Effekte aktiv</div>', unsafe_allow_html=True)