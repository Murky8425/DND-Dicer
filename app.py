import random

import streamlit as st


st.set_page_config(page_title="DND Diceroller", page_icon="🎲", layout="wide")

PALETTE = ["#E76F51", "#2A9D8F", "#E9C46A", "#6C9A8B", "#F4A261"]
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
}


def readable_text_color(hex_color: str) -> str:
    """Choose dark or light text for legible labels on a selected die color."""
    red, green, blue = (int(hex_color[index : index + 2], 16) for index in (1, 3, 5))
    luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
    return "#17211E" if luminance > 0.58 else "#FFFFFF"


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
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.62); border-left: 3px solid var(--coral);
        padding: 0.8rem 1rem; border-radius: 4px;
    }
    div[data-testid="stMetricLabel"] { color: var(--muted); }
    div[data-testid="stMetricValue"] { color: var(--forest); }
    div[data-testid="stPopover"] button {
        min-height: 2.35rem; border-color: rgba(25, 60, 50, 0.25);
        color: var(--forest); background: rgba(255, 255, 255, 0.55);
        border-radius: 5px; font-size: 0.78rem;
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
        min-height: 122px; display: flex; flex-direction: column;
        justify-content: space-between; padding: 15px 16px; border-radius: 6px;
        box-sizing: border-box; margin-bottom: 14px;
        box-shadow: 0 3px 10px rgba(27, 39, 33, 0.12);
        animation: die-arrive 320ms ease-out both;
    }
    .die-label { font-size: 0.78rem; font-weight: 700; opacity: 0.82; }
    .die-value { font-size: 2.25rem; line-height: 1; font-weight: 800; }
    .die-number { font-size: 0.78rem; opacity: 0.82; }
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
    </style>
    """,
    unsafe_allow_html=True,
)
if "die_colors" not in st.session_state:
    st.session_state.die_colors = {}


def save_die_color(color_id: str, widget_key: str) -> None:
    st.session_state.die_colors[color_id] = st.session_state[widget_key]


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

controls, results, empty_space = st.columns([1, 2, 1], gap="large")
with controls:
    st.subheader("Würfel auswählen")
    counts = {}
    for die_type in DICE:
        type_column, count_column, color_column = st.columns([0.8, 1.25, 1.2])
        with type_column:
            st.markdown(f'<div class="type-label">{die_type}</div>', unsafe_allow_html=True)
        with count_column:
            counts[die_type] = st.slider(
                f"Anzahl {die_type}",
                min_value=0,
                max_value=32,
                value=0,
                key=f"count_{die_type}",
                label_visibility="collapsed",
            )
        with color_column:
            with st.popover(
                "🎨 Farben",
                help="Farben der einzelnen Würfel festlegen",
                use_container_width=True,
            ):
                st.caption(f"Farben für {counts[die_type]}× {die_type}")
                if counts[die_type] == 0:
                    st.caption("Wähle zuerst mindestens einen Würfel dieser Art.")
                else:
                    for die_index in range(counts[die_type]):
                        color_id = f"{die_type}_{die_index + 1}"
                        widget_key = f"color_{color_id}"
                        default_color = PALETTE[die_index % len(PALETTE)]
                        if widget_key not in st.session_state:
                            st.session_state[widget_key] = st.session_state.die_colors.get(
                                color_id, default_color
                            )
                        label_column, picker_column = st.columns([1, 1.5])
                        with label_column:
                            st.write(f"Würfel {die_index + 1}")
                        with picker_column:
                            st.color_picker(
                                f"Farbe {die_type} Würfel {die_index + 1}",
                                key=widget_key,
                                on_change=save_die_color,
                                args=(color_id, widget_key),
                                label_visibility="collapsed",
                            )

    total_count = sum(counts.values())
    st.markdown(
        f'<div class="roll-summary"><span>Würfel im Becher</span><strong>{total_count}</strong></div>',
        unsafe_allow_html=True,
    )
    roll_clicked = st.button(
        "Würfel rollen",
        type="primary",
        use_container_width=True,
        disabled=total_count == 0,
    )

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
        result_groups.append(
            {
                "type": die_type,
                "values": [random.randint(1, DICE[die_type]) for _ in range(count)],
                "colors": colors,
            }
        )
    st.session_state.last_roll = {"groups": result_groups}

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
            for group_die_index, (value, color) in enumerate(
                zip(group["values"], group["colors"]), start=1
            ):
                all_values.append(value)
                face = ("X" if value == 1 else "O") if group["type"] == "D2" else str(value)
                text_color = readable_text_color(color)
                with result_columns[die_index % len(result_columns)]:
                    st.markdown(
                        f"""
                        <div class="die" style="background:{color};color:{text_color}">
                            <span class="die-label">{group['type']} · Würfel {group_die_index}</span>
                            <span class="die-value">{face}</span>
                            <span class="die-number">Ergebnis: {value}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                die_index += 1
        st.metric("Summe", sum(all_values))
    else:
        st.info("Wähle links Würfel aus und starte deinen Wurf.")