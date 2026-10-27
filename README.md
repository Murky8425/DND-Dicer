# DND-Dicer

Ein virtueller Würfelbecher für Dungeons & Dragons, umgesetzt mit Streamlit.
Neben dem Würfelmodus gibt es einen Map-Generator und einen Bildmodus. Der
Würfelmodus enthält außerdem einen Initiative-Tracker: Teilnehmer können mit
Initiative-Modifikator eingetragen und per W20 sortiert werden; die Zugreihenfolge,
aktuelle Runde und das Weiterzählen werden verwaltet.
Der Map-Generator erstellt acht zufällige Encounter-Karten zu einem ausgewählten Thema
oder gemischt (je zwei aus Verlies, Wald, Höhle und Ruinen). Wegeführung,
Wegbreite, zusätzliche Abzweigungen und die Zahl der Räume und Wegpunkte lassen
sich anpassen; Verliese unterstützen eckige, organische oder gemischte Raumformen.
Optional lassen sich Start, Begegnung, Gefahr und Schatz auf den Wegen und in
Verliesräumen markieren; im Baumodus können diese Punkte verschoben, umbenannt
und entfernt werden.
Karten können für die aktuelle Streamlit-Sitzung temporär gespeichert und
einzeln oder gesammelt gelöscht werden. Es bleiben höchstens acht Karten; die
Liste ist nicht dauerhaft und kann beim Neuladen der Website verschwinden.
Außerdem kann die Kartengröße in Chunks (10×10, 20×20, 25×15, 50×50 oder 75×75)
gewählt werden. 25×15 Chunks ist die empfohlene Größe. Eine Karte lässt
sich direkt im Bildmodus öffnen. Dort werden generierte Karten oder eigene
hochgeladene Bilder groß angezeigt. Im Baumodus lassen sich Verliesräume ziehen
und in der Größe ändern. Kisten, Fässer, Fackeln, Tische, Stühle, Betten,
Bücherregale und Teppiche können platziert, verschoben und in 45-Grad-Schritten
gedreht sowie über den Größen-Griff vergrößert oder verkleinert werden. Eigene
Räume entstehen durch Anklicken von vier Ecken; dabei
werden automatisch Boden und Wände ergänzt. Dekorationen lassen sich auch
innerhalb gezeichneter Räume und vorhandener Gebäude platzieren. Türen lassen sich
auf Wänden setzen oder wieder entfernen;
Treppenmarker können in Räumen und Gebäuden platziert und wieder entfernt werden.
Mit Lichtquellen und dem Dunkelheitsschalter lässt sich erkunden, wie Bereiche
einer Karte bei Dunkelheit beleuchtet werden; die Helligkeit jeder Lichtquelle
lässt sich einzeln einstellen. Gelände-Flächen für Wasser, Lava
oder Gruben lassen sich durch Setzen mehrerer Randpunkte zeichnen und abschließen;
sie sind visuelle Markierungen und ändern keine Spielregeln.
Das Kartenraster lässt sich ein- und ausblenden; auf Wunsch werden Spalten und
Zeilen zusätzlich mit Koordinaten beschriftet. Bei sehr großen Karten erscheinen
Koordinaten in Fünfer-Schritten, damit die Beschriftung lesbar bleibt. Karten
lassen sich als PNG oder druckbares PDF exportieren; der Export enthält Raster,
Koordinaten, Gelände und Licht unabhängig von den Anzeige-Schaltern.
Pins mit Beschriftungen
wie Monster, Spieler oder Gefahr lassen sich direkt im Bild platzieren,
verschieben und einzeln wieder entfernen. Namen und Löschknöpfe lassen sich bei
Bedarf ausblenden. Ein neuer Upload ersetzt das bisher angezeigte Bild und setzt
dessen Pins zurück. Im Baumodus können die letzten fünf Bearbeitungsschritte
rückgängig gemacht und wiederhergestellt werden.
Im Bildmodus kann optional ein Nebel des Krieges aktiviert und mit einem
einstellbaren Pinsel auf- oder zugedeckt werden; ganze Karte aufdecken oder
verdecken ist ebenfalls möglich.

## Starten

```bash
python -m pip install -r installme.txt
streamlit run app.py
```

Die App unterstützt D2, D4, D6, D10, D12, D20, D50, D100 und D250. Pro Wurf lassen
sich bis zu 30 Würfel in bis zu acht Gruppen kombinieren, zum Beispiel 12× D12
und 2× D100. Jeder Würfel kann eine eigene Farbe haben. Beim D2 steht X für 1
und O für 2.
