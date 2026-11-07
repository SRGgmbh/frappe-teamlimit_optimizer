---
name: aufgabe-einstellen
description: Formuliert gemeinsam mit dem Nutzer eine Aufgabe für den Teamlimit-Aufgabenpool so, dass ein Kollege sie ohne Rückfrage in Claude ausführen kann. Nutzen, wenn der Nutzer eine Aufgabe „in den Pool stellen“, „für den Aufgabenpool vorbereiten“ oder „an jemanden mit Budget abgeben“ will.
---

# Aufgabe für den Aufgabenpool einstellen

Ziel ist ein Prompt, den ein Kollege mit freiem Claude-Budget **ohne jede Rückfrage** starten kann. Der Kollege kennt weder den Hintergrund noch die Dateien noch die Erwartungen des Auftraggebers. Alles, was er braucht, muss im Prompt stehen.

## Einstellungen der Organisation

- Frappe-Adresse: `https://ihre-frappe-instanz.example` (vor dem Verteilen auf die eigene Instanz ändern)

## Ablauf

### 1. Interview

Stelle die Fragen **einzeln**, warte jeweils die Antwort ab und frage nach, solange etwas unklar ist. Überspringe Fragen, die schon beantwortet sind. Schlage zu jeder Frage eine sinnvolle Antwort vor, die der Nutzer nur bestätigen muss.

1. **Ziel:** Was soll am Ende konkret vorliegen? Wofür wird es gebraucht?
2. **Ausgangsmaterial:** Welche Dateien, Daten, Links oder Systeme braucht die Aufgabe, und wo genau liegen sie (Claude-Projekt, Ordner, Connector)?
3. **Claude-Projekt und Modus:** In welchem Organisationsprojekt soll die Aufgabe laufen? Reicht ein Chat, oder braucht sie Cowork (Dateien, Ordner) oder Claude Code (Repository)?
4. **Ergebnisform:** Welches Format (Doc, Tabelle, Datei, Code, Text), welche Sprache, welcher Umfang, welcher Ton?
5. **Ablage:** Wo soll das Ergebnis landen, damit der Auftraggeber es findet?
6. **Fertig, wenn:** Woran erkennt man, dass die Aufgabe vollständig erledigt ist? Formuliere 2–5 prüfbare Kriterien.
7. **Grenzen:** Was darf auf keinen Fall passieren (z. B. Preise ändern, E-Mails versenden, Daten löschen)? Was ist ausdrücklich nicht Teil der Aufgabe?
8. **Rahmen:** Priorität, fällig bis, benötigte Zugriffe, und ob nur ein bestimmtes Claude Team die Aufgabe übernehmen soll (z. B. wegen vertraulicher Daten).

Schätze am Ende den **Aufwand** und begründe ihn in einem Satz:
- **S** – bis etwa ein Viertel eines 5-Stunden-Fensters (kurzer Text, kleine Prüfung)
- **M** – bis etwa die Hälfte (mehrere Dateien, mittlere Ausarbeitung)
- **L** – ein volles Fenster (umfangreiche Analyse, viel Code, viele Dateien)

### 2. Prompt schreiben

Schreibe den Prompt in der zweiten Person an Claude, nicht an den Kollegen. Aufbau:

```
Kontext: <2–3 Sätze Hintergrund, wofür das Ergebnis gebraucht wird>

Aufgabe: <was genau zu tun ist>

Material: <wo die Eingaben liegen, mit genauen Namen>

Ergebnis: <Format, Sprache, Umfang, Ton>

Ablage: <wo das Ergebnis gespeichert oder geteilt wird>

Fertig, wenn:
- <Kriterium 1>
- <Kriterium 2>

Nicht tun:
- <Grenze 1>
```

Prüfe den Prompt danach selbst: Gibt es Begriffe, Abkürzungen oder Verweise („die Datei von letzter Woche“), die ein Außenstehender nicht versteht? Ersetze sie.

### 3. Übergabe

Gib dem Nutzer zum Schluss:

1. **Titel** (höchstens 8 Wörter)
2. Den **Prompt** in einem Codeblock
3. **Metadaten:** Claude-Projekt, Projekt-Link falls bekannt, Starten in (Chat / Cowork / Claude Code), Aufwand, Priorität, fällig bis, Voraussetzungen, Claude Team
4. Einen **Link zum Anlegen** der Aufgabe in Frappe, mit URL-kodierten Werten:

   `<Frappe-Adresse>/app/claude-task/new?title=<Titel>&prompt=<Prompt>&priority=<High|Medium|Low>&mode=<Chat|Cowork|Claude Code>&claude_project=<Projektname>&prerequisites=<Voraussetzungen>`

   `priority` erwartet die englischen Werte High, Medium oder Low. `claude_project` muss genau dem Namen in der Projektliste des Teamlimit Optimizers entsprechen.

   Ist der Link länger als etwa 6.000 Zeichen, lass `prompt` weg und sage dem Nutzer, dass er den Prompt aus dem Codeblock ins Feld kopiert.

5. Zusätzlich den Übergabe-Block, falls der Link nicht funktioniert. Er lässt sich in Frappe über **Aus KI-Text übernehmen** einfügen:

````
=== TEAMLIMIT-AUFGABE ===
Titel: <Titel>
Priorität: <Hoch | Mittel | Niedrig>
Aufwand: <S | M | L>
Fällig bis: <TT.MM.JJJJ>
Starten in: <Chat | Cowork | Claude Code>
Claude-Projekt: <Name>
Projekt-Link: <Link oder leer>
Voraussetzungen: <…>
Claude Team: <Name oder leer>
--- PROMPT ---
<Prompt>
=== ENDE ===
````

Der Nutzer prüft die Aufgabe in Frappe und speichert sie. Erst dann steht sie im Pool.
