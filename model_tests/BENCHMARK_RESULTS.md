# Ollama Modell-Benchmark: Graphviz-Code-Generierung

**Testdatum:** 2026-01-04
**Testdauer:** 336.7 Sekunden (5.6 Minuten)
**Getestete Modelle:** 19
**Erfolgsrate:** 15/19 (79%)

## Testbeschreibung

Alle Modelle wurden mit dem gleichen Prompt getestet:

```
Generate ONLY valid Graphviz DOT code for a flowchart showing a software development process:
1. Requirements -> Design -> Implementation -> Testing -> Deployment -> Maintenance
2. Add a feedback loop from Testing back to Implementation if bugs are found
3. Use proper node shapes (ellipse for start/end, box for processes, diamond for decisions)

Output ONLY the DOT code wrapped in ```dot code blocks. No explanations.
```

## Bewertungskriterien

| Kriterium | Punkte |
|-----------|--------|
| Valider DOT-Code | 30 |
| Alle 6 Knoten vorhanden | 25 |
| Node-Shapes verwendet | 15 |
| Diamond für Decision | 10 |
| Feedback-Loop implementiert | 10 |
| Styling (Farben, Stile) | 5 |
| Zeitbonus (<5s: 5, <10s: 4, <20s: 3, <30s: 2, <60s: 1) | max 5 |
| **Maximum** | **100** |

---

## Ranking

| Rang | Modell | Score | Zeit | Größe | Bewertung |
|:----:|--------|:-----:|:----:|:-----:|-----------|
| 🥇 1 | **gemma3:4b** | **100** | 5.0s | 3.1 GB | Perfekt - alle Kriterien erfüllt |
| 🥈 2 | Qwen3-Coder-30B | 97 | 21.4s | 20.2 GB | Exzellent - sehr professionell |
| 🥉 3 | gpt-oss:latest | 92 | 20.6s | 12.8 GB | Sehr gut - klare Struktur |
| 4 | qwen3:8b | 91 | 36.2s | 4.9 GB | Sehr gut - aber langsam |
| 5 | deepseek-r1:8b | 91 | 38.7s | 4.9 GB | Sehr gut - aber langsam |
| 6 | qwen2.5-coder:latest | 89 | 6.4s | 4.4 GB | Gut - schnell & solide |
| 7 | gemma3:12b | 88 | 10.6s | 7.6 GB | Gut - ausgewogen |
| 8 | gemma3:27b-it-qat | 87 | 21.1s | 16.8 GB | Gut - etwas langsam |
| 9 | gemma3:1b | 85 | 3.5s | 0.8 GB | Gut - sehr schnell! |
| 10 | qwen2.5-coder:7b | 84 | 10.0s | 4.4 GB | Gut |
| 11 | gpt-oss:20b | 83 | 12.9s | 12.8 GB | Gut |
| 12 | mistral:7b | 79 | 5.7s | 4.1 GB | OK - einfaches Layout |
| 13 | qwen2.5:7b | 74 | 7.3s | 4.4 GB | OK - keine Shapes |
| 14 | smollm2:1.7b | 70 | 2.6s | 1.7 GB | OK - minimalistisch |
| 15 | llama3.2:1b | 70 | 3.8s | 1.2 GB | OK - minimalistisch |
| ❌ 16 | qwen3:0.6b | 0 | 4.1s | 0.5 GB | Fehlgeschlagen |
| ❌ 17 | llama3.2:3b | 0 | 4.9s | 1.9 GB | Fehlgeschlagen |
| ❌ 18 | qwen3:4b | 0 | 34.6s | 2.4 GB | Fehlgeschlagen |
| ❌ 19 | phi4-reasoning | 0 | 82.9s | 10.4 GB | Fehlgeschlagen |

---

## Top 3 Analyse

### 🥇 1. Platz: gemma3:4b (Score: 100)

**Das beste Preis-Leistungs-Verhältnis!**

- ✅ Nur 3.1 GB groß
- ✅ Schnell (5.0s)
- ✅ Alle Shapes korrekt (ellipse, box, diamond)
- ✅ Feedback-Loop mit "Fix Bugs" Label
- ✅ Gestrichelte Linie für Rückpfad
- ✅ Professionelles Styling

**Generiertes Diagramm:** `gemma3_4b_output.png`

### 🥈 2. Platz: Qwen3-Coder-30B (Score: 97)

**Beste Qualität für komplexe Aufgaben**

- ✅ Sehr professionelle Ausgabe
- ✅ Diamond mit Yes/No Labels
- ✅ Klare Entscheidungslogik
- ⚠️ Groß (20.2 GB)
- ⚠️ Langsamer (21.4s)

**Generiertes Diagramm:** `danielsheep_Qwen3-Coder-30B-A3B-Instruct-1M-Unsloth_UD-Q5_K_XL_output.png`

### 🥉 3. Platz: gpt-oss:latest (Score: 92)

**Gute Balance für mittlere Hardware**

- ✅ Vertikales Layout
- ✅ Diamond für Decision
- ✅ Klare Feedback-Loop
- ⚠️ 12.8 GB groß
- ⚠️ 20.6s Generierungszeit

**Generiertes Diagramm:** `gpt-oss_latest_output.png`

---

## Effizienz-Ranking (Score / Zeit)

Für Anwendungen wo Geschwindigkeit wichtig ist:

| Modell | Score | Zeit | Effizienz (Score/s) |
|--------|:-----:|:----:|:-------------------:|
| gemma3:1b | 85 | 3.5s | **24.3** |
| smollm2:1.7b | 70 | 2.6s | **26.9** |
| gemma3:4b | 100 | 5.0s | **20.0** |
| llama3.2:1b | 70 | 3.8s | 18.4 |
| qwen2.5-coder:latest | 89 | 6.4s | 13.9 |
| mistral:7b | 79 | 5.7s | 13.9 |

---

## Größen-Effizienz (Score / GB)

Für Anwendungen mit begrenztem Speicher:

| Modell | Score | Größe | Effizienz (Score/GB) |
|--------|:-----:|:-----:|:--------------------:|
| gemma3:1b | 85 | 0.8 GB | **106.3** |
| llama3.2:1b | 70 | 1.2 GB | **58.3** |
| smollm2:1.7b | 70 | 1.7 GB | **41.2** |
| gemma3:4b | 100 | 3.1 GB | **32.3** |
| qwen2.5-coder:latest | 89 | 4.4 GB | 20.2 |

---

## Fehlgeschlagene Modelle

| Modell | Problem |
|--------|---------|
| phi4-reasoning | Generiert zu viel "Reasoning"-Text, kein valider Code |
| qwen3:4b | Kein DOT-Code in Antwort (nur Erklärungen) |
| llama3.2:3b | Syntaxfehler im generierten Code |
| qwen3:0.6b | Zu klein für komplexe Code-Generierung |

---

## Empfehlungen

### 🏆 Beste Gesamtleistung
**gemma3:4b** - Perfekter Score bei minimaler Größe und guter Geschwindigkeit.

### ⚡ Schnellste Option
**smollm2:1.7b** oder **gemma3:1b** - Unter 4 Sekunden mit akzeptabler Qualität.

### 💾 Kleinste Option
**gemma3:1b** (0.8 GB) - Höchste Qualität unter den Sub-1GB Modellen.

### 🎯 Beste Qualität (ohne Rücksicht auf Ressourcen)
**Qwen3-Coder-30B** - Professionellste Ausgabe, aber ressourcenintensiv.

### ⚖️ Beste Balance (Qualität/Geschwindigkeit/Größe)
**qwen2.5-coder:latest** - Score 89, nur 6.4s, 4.4 GB.

---

## Fazit

**Gewinner: gemma3:4b** erreicht als einziges Modell den perfekten Score von 100 Punkten und ist dabei nur 3.1 GB groß mit einer Generierungszeit von 5 Sekunden. Es ist die klare Empfehlung für Graphviz-Code-Generierung.

Für sehr ressourcenbeschränkte Umgebungen ist **gemma3:1b** mit nur 0.8 GB eine hervorragende Alternative (Score: 85).

Die **qwen3**-Modelle (außer qwen3:8b) haben Probleme mit direkter Code-Generierung, da sie standardmäßig im "Thinking Mode" arbeiten.

---

*Benchmark durchgeführt mit `graphviz_tool.py` auf macOS*
