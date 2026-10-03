import random
import uuid

import streamlit as st


# Seitentitel und zentrale Einstellungen für Würfel, Farben und Effekte.
st.set_page_config(page_title="DND Diceroller", page_icon="🎲", layout="wide")

PALETTE = ["#E76F51", "#2A9D8F", "#E9C46A", "#6C9A8B", "#F4A261"]
MAX_BOSSES = 10
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
    "D100": 250,
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


# Gestaltung der Streamlit-Oberfläche und der gerollten Würfel.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
    :root {
        --forest: #193c32;
        --forest-light: #285c4d;
        --coral: #bd573d;
        --paper: #f3f2eb;
        --muted: #68766f;
    }
    .stApp {
        background-color: var(--paper);
        background-image: repeating-linear-gradient(
            135deg, rgba(35, 64, 54, 0.025) 0, rgba(35, 64, 54, 0.025) 1px,
            transparent 1px, transparent 12px
        );
    }
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 4rem; }
    html, body, [class*="st-"] { font-family: 'DM Sans', sans-serif; }
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
    .type-label {
        display: inline-flex; align-items: center; min-height: 2.4rem;
        color: var(--forest); font-size: 0.9rem; font-weight: 700;
    }
    .effects-panel-title { color: var(--forest); font-size: 1rem; font-weight: 700; }
    .st-key-boss_hp_panel {
        margin-bottom: 1rem; padding: 1rem;
        border: 1px solid rgba(25, 60, 50, 0.18);
        border-top: 3px solid var(--coral); border-radius: 6px;
        background: rgba(255, 255, 255, 0.72);
        box-shadow: 0 8px 18px rgba(25, 60, 50, 0.05);
    }
    .boss-panel-title { color: var(--forest); font-size: 1rem; font-weight: 700; }
    .st-key-dice_selector_heading h2,
    .st-key-dice_selector_heading h3 {
        color: #000 !important;
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
        background: rgba(243, 242, 235, 0.48);
    }
    .boss-name { color: var(--forest); font-weight: 700; }
    .st-key-boss_hp_panel [class*="st-key-boss_card_"] [data-testid="stMarkdownContainer"] p {
        color: #000 !important;
    }
    .st-key-boss_hp_panel [data-testid="stProgress"] [data-testid="stMarkdownContainer"] {
        color: #000 !important;
    }
    .st-key-boss_hp_panel [data-testid="stProgressBarTrack"] {
        background-color: #e6e6e6 !important;
    }
    .st-key-boss_hp_panel [data-testid="stProgressBarTrack"] > div {
        background-color: var(--coral) !important;
    }
    .st-key-boss_hp_panel [data-testid="stWidgetLabel"] p,
    .st-key-boss_hp_panel label {
        color: #000 !important;
    }
    .st-key-boss_hp_panel [data-testid="stCaptionContainer"] {
        color: #000 !important;
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
        background: rgba(255, 255, 255, 0.72);
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
        background: rgba(243, 242, 235, 0.55); color: var(--muted);
        font-size: 0.82rem; text-align: center;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) {
        align-items: center; gap: 0.5rem; padding: 0.35rem 0.55rem;
        margin-bottom: 0.55rem; border: 1px solid rgba(25, 60, 50, 0.16);
        border-left: 3px solid var(--coral); border-radius: 6px;
        background: rgba(255, 255, 255, 0.58);
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
        background: rgba(255, 255, 255, 0.62); border-left: 3px solid var(--coral);
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
        color: var(--forest); background: rgba(255, 255, 255, 0.55);
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
    .die {
        position: relative; width: min(100%, 112px); aspect-ratio: 1;
        display: flex; align-items: center; justify-content: center;
        padding: 12px; border-radius: 18px; box-sizing: border-box;
        margin: 0 auto 14px; border: 2px solid rgba(255,255,255,0.34);
        box-shadow: 0 12px 20px rgba(27, 39, 33, 0.16),
                    inset 0 2px 0 rgba(255,255,255,0.28),
                    inset -8px -10px 18px rgba(0,0,0,0.12);
        transform: perspective(700px) rotateX(8deg) rotateY(-8deg);
        animation: die-arrive 320ms ease-out both;
    }
    .die-label {
        position: absolute; top: 10px; left: 12px; font-size: 0.62rem;
        font-weight: 700; letter-spacing: 0.06em; opacity: 0.82;
    }
    .die-value {
        font-size: clamp(2.2rem, 2.7vw, 3.2rem); line-height: 1;
        font-weight: 800; text-align: center; text-shadow: 0 2px 8px rgba(0,0,0,0.12);
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
    @keyframes die-arrive {
        from { opacity: 0; transform: translateY(8px) rotate(-2deg); }
        to { opacity: 1; transform: translateY(0) rotate(0); }
    }
    @media (max-width: 720px) {
        .block-container { padding-top: 1.2rem; }
        .hero-title { font-size: 2.35rem; }
        .masthead { align-items: start; gap: 0.8rem; }
        .masthead-mark { font-size: 0.9rem; padding: 0.45rem 0.6rem; }
        .hero-subtitle { max-width: 26rem; }
    }
    .stApp { --text-color: #000; color: #000 !important; }
    .stApp *:not(.die):not(.die *) { color: #000 !important; }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"],
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #fff !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button {
        background: #444 !important;
        border-color: #444 !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button,
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button * {
        font-size: 0 !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button::after {
        content: "Upload";
        color: #fff !important;
        font-size: 0.9rem !important;
    }
    .stApp [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button:hover {
        background: #333 !important;
        border-color: #333 !important;
    }
    .st-key-boss_hp_panel div[data-testid="stPopover"] button,
    .st-key-effects_panel div[data-testid="stPopover"] button,
    div.stButton > button[kind="primary"] {
        background: var(--paper) !important;
        border-color: rgba(25, 60, 50, 0.25) !important;
    }
    .st-key-boss_hp_panel div[data-testid="stPopover"] button:hover,
    .st-key-effects_panel div[data-testid="stPopover"] button:hover,
    div.stButton > button[kind="primary"]:hover {
        background: #e4e9e4 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# Spielzustand initialisieren und IDs für gespeicherte Gegner ergänzen.
if "die_colors" not in st.session_state:
    st.session_state.die_colors = {}
if "die_actions" not in st.session_state:
    st.session_state.die_actions = {}
if "active_effects" not in st.session_state:
    st.session_state.active_effects = []
if "bosses" not in st.session_state:
    st.session_state.bosses = []
for boss in st.session_state.bosses:
    boss.setdefault("id", uuid.uuid4().hex)
    boss.setdefault("token", 1)
    boss.setdefault("element", ELEMENTS[0])


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


# Kopfbereich und dreispaltiges Hauptlayout der App.
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

mode = st.radio(
    "Modus",
    ["Würfel-Modus", "Bild-Modus"],
    horizontal=True,
    key="app_mode",
)

if mode == "Bild-Modus":
    st.subheader("Bild anzeigen")
    upload_column, _ = st.columns([1, 1])
    with upload_column:
        st.caption("Bild hierher ziehen oder über Upload auswählen.")
        uploaded_image = st.file_uploader(
            "Bild hochladen",
            type=["png", "jpg", "jpeg", "webp", "gif"],
            key="display_image_upload",
        )
    if uploaded_image is not None:
        st.session_state.display_image = uploaded_image.getvalue()

    if st.session_state.get("display_image") is not None:
        with st.container(key="image_mode_preview"):
            st.image(st.session_state.display_image, use_container_width=True)
    else:
        st.info("Lade ein Bild hoch, um es hier groß anzuzeigen.")
    st.stop()

# Würfel konfigurieren: Anzahl, Farbe und Aktionssymbol je Würfel festlegen.
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
                help="Farben und Aktionssymbole der einzelnen Würfel festlegen",
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

# Bei einer Aktion würfeln und das Ergebnis für spätere Reruns sichern.
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
        result_groups.append(
            {
                "type": die_type,
                "values": [random.randint(1, DICE[die_type]) for _ in range(count)],
                "colors": colors,
                "actions": actions,
            }
        )
    st.session_state.last_roll = {"groups": result_groups}

# Würfelergebnisse samt Einzelsummen und Gesamtsumme anzeigen.
with results:
    st.subheader("Auswertung")
    if "last_roll" in st.session_state:
        result = st.session_state.last_roll
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
            for group_die_index, (value, color, action) in enumerate(
                zip(group["values"], group["colors"], group["actions"]), start=1
            ):
                all_values.append(value)
                face = ("X" if value == 1 else "O") if group["type"] == "D2" else str(value)
                die_bg = darken_color(color, 0.2)
                text_color = readable_text_color(die_bg)
                action_symbol = die_action_icon(action)
                with result_columns[die_index % len(result_columns)]:
                    st.markdown(
                        f"""
                        <div class="die" style="background:linear-gradient(135deg, rgba(255,255,255,0.18), rgba(0,0,0,0.08)), {die_bg}; color:{text_color};">
                            <span class="die-badge">{action_symbol}</span>
                            <span class="die-label">{group['type']}</span>
                            <span class="die-value">{face}</span>
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

# Gegner-HP verwalten: Gegner anlegen, bearbeiten, heilen oder verletzen.
with empty_space:
    with st.container(key="boss_hp_panel"):
        title_column, add_column = st.columns([4, 1], vertical_alignment="center")
        with title_column:
            st.markdown('<div class="boss-panel-title">Gegner-HP</div>', unsafe_allow_html=True)
            st.caption(f"{len(st.session_state.bosses)} / {MAX_BOSSES} HP-Leisten")
        with add_column:
            with st.popover(
                "+",
                help="Gegner hinzufügen",
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
                        help=f'{boss["name"]} löschen',
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
                    help="Bearbeiten: Name oder maximale HP ändern",
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
                        help="Positive Zahl heilt, negative Zahl verursacht Schaden.",
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

    # Aktive Status-Effekte verwalten.
    with st.container(key="effects_panel"):
        title_column, add_column = st.columns([4, 1], vertical_alignment="center")
        with title_column:
            st.markdown('<div class="effects-panel-title">Effekte</div>', unsafe_allow_html=True)
        with add_column:
            with st.popover("+", help="Effekt hinzufügen", use_container_width=False):
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
                        help=f"{effect} entfernen",
                        on_click=remove_effect,
                        args=(effect_index,),
                    )
        else:
            st.markdown('<div class="effects-empty">Keine Effekte aktiv</div>', unsafe_allow_html=True)