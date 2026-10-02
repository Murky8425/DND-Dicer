# DND-Dicer

Ein virtueller Würfelbecher für Dungeons & Dragons, umgesetzt mit Streamlit.
Neben dem Würfelmodus gibt es einen Bildmodus, in dem ein hochgeladenes Bild groß
angezeigt wird. Ein neuer Upload ersetzt das bisher angezeigte Bild.

## Starten

```bash
python -m pip install -r installme.txt
streamlit run app.py
```

Die App unterstützt D2, D4, D6, D10, D12, D20, D50 und D100. Pro Wurf lassen
sich bis zu 30 Würfel in bis zu acht Gruppen kombinieren, zum Beispiel 12× D12
und 2× D100. Jeder Würfel kann eine eigene Farbe haben. Beim D2 steht X für 1
und O für 2.
