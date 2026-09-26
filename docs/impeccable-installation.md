# Impeccable — Installation

- Offizielle Quelle: https://github.com/pbakaus/impeccable
- Git-Revision: 9d715cc4f5564a990ca8345abfdd5df6dc9b41c8
- Skill-Version laut SKILL.md: 4.4.0
- Repository-Unterordner: .agents/skills/impeccable
- Ziel: C:\Users\Timon\.codex\skills\impeccable
- Mitinstalliert: SKILL.md, reference/, agents/, scripts/ mit Launchern und Begleitdateien.
- Engine: impeccable-engine 0.1.6, Startfähigkeit erfolgreich geprüft.
- Installationsdatum: 25.09.2026

## Ausgeführte Befehle

```powershell
& 'C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\Timon\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py' --repo pbakaus/impeccable --ref 9d715cc4f5564a990ca8345abfdd5df6dc9b41c8 --path .agents/skills/impeccable
& 'C:\Users\Timon\.codex\skills\impeccable\scripts\impeccable.cmd' engine-probe
```

Beide Befehle erfolgreich. Der erstmalige context-Aufruf vor Engine-Installation konnte den Cache nicht anlegen; für diese Sitzung wurde der dokumentierte direkte Lese-Fallback verwendet. Bei der nächsten Aufgabe context einmal im Projektverzeichnis aufrufen.

## Anwendung im Projekt

Produktkontext wurde aus der bereits abgeschlossenen Nutzerabstimmung erfasst. Die vom Nutzer vorgegebenen drei Richtungen und die Bildauswahl vor Coding haben Vorrang vor zusätzlichen generischen Skill-Workflows. Kein alternatives Zufallsverfahren und keine zusätzliche Fragerunde ersetzen die vereinbarte Auswahl A/B/C. Live-Browser-Iteration und Code-Detektoren sind noch nicht angewendet, da keine Webseite implementiert ist.
