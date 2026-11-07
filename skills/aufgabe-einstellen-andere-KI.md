Du hilfst mir, eine Aufgabe für den Teamlimit-Aufgabenpool vorzubereiten. Kollegen mit freiem Claude-Budget übernehmen Aufgaben aus diesem Pool und führen sie in Claude aus, ohne mich vorher zu fragen. Sie kennen weder den Hintergrund noch meine Dateien noch meine Erwartungen. Alles Nötige muss deshalb im Prompt stehen.

Vorgehen:

1. Stelle mir die folgenden Fragen einzeln. Warte jeweils auf meine Antwort und frag nach, solange etwas unklar ist. Überspringe Fragen, die schon beantwortet sind. Schlage zu jeder Frage eine sinnvolle Antwort vor.
   1. Ziel: Was soll am Ende konkret vorliegen, wofür wird es gebraucht?
   2. Ausgangsmaterial: Welche Dateien, Daten, Links oder Systeme braucht die Aufgabe, und wo genau liegen sie?
   3. Claude-Projekt und Modus: In welchem Claude-Projekt soll die Aufgabe laufen? Reicht ein Chat, oder braucht sie Cowork (Dateien, Ordner) oder Claude Code (Repository)?
   4. Ergebnisform: Format, Sprache, Umfang, Ton?
   5. Ablage: Wo soll das Ergebnis landen?
   6. Fertig, wenn: 2–5 prüfbare Kriterien.
   7. Grenzen: Was darf auf keinen Fall passieren, was gehört nicht zur Aufgabe?
   8. Rahmen: Priorität, fällig bis, benötigte Zugriffe, nur für ein bestimmtes Claude Team?

2. Schätze den Aufwand und begründe ihn in einem Satz: S = bis etwa ein Viertel eines 5-Stunden-Fensters von Claude, M = bis etwa die Hälfte, L = ein volles Fenster.

3. Schreibe den Prompt an Claude (nicht an den Kollegen) mit genau diesen Abschnitten: Kontext, Aufgabe, Material, Ergebnis, Ablage, Fertig, wenn (Liste), Nicht tun (Liste). Prüfe ihn danach: Ersetze alle Begriffe, Abkürzungen und Verweise, die ein Außenstehender nicht versteht.

4. Gib zum Schluss ausschließlich diesen Block in einem Codeblock aus, damit ich ihn kopieren kann. Felder, die leer bleiben, schreibst du mit leerem Wert:

=== TEAMLIMIT-AUFGABE ===
Titel: <höchstens 8 Wörter>
Priorität: <Hoch | Mittel | Niedrig>
Aufwand: <S | M | L>
Fällig bis: <TT.MM.JJJJ>
Starten in: <Chat | Cowork | Claude Code>
Claude-Projekt: <Name>
Projekt-Link: <https://claude.ai/project/… oder leer>
Voraussetzungen: <benötigte Connectoren, Dateien, Zugriffe>
Claude Team: <Name oder leer>
--- PROMPT ---
<der vollständige Prompt>
=== ENDE ===
