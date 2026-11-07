---
name: aufgabe-abschliessen
description: Schließt eine Aufgabe aus dem Teamlimit-Aufgabenpool sauber ab – prüft die Fertig-Kriterien, sorgt für ein geteiltes Ergebnis und erstellt die Ergebnis-Zusammenfassung für Frappe. Nutzen, wenn ein Chat mit „[Teamlimit-Aufgabe …]“ begonnen hat und der Nutzer die Aufgabe abschließen will oder sagt, sie sei fertig.
---

# Aufgabe aus dem Aufgabenpool abschließen

Der Chat hat mit einer Kopfzeile `[Teamlimit-Aufgabe <Nummer>: <Titel>]` und einem Link „Aufgabe im Pool“ begonnen. Der Auftraggeber wird über Frappe benachrichtigt, sobald die Aufgabe als erledigt markiert ist, und liest dann die Zusammenfassung.

## Ablauf

1. **Fertig-Kriterien prüfen.** Suche im ersten Prompt den Abschnitt „Fertig, wenn“. Gehe jedes Kriterium durch und sage ehrlich, ob es erfüllt ist. Ist etwas offen, frage den Nutzer, ob er es noch erledigen oder als offenen Punkt melden will.
2. **Ergebnis teilbar machen.** Der Auftraggeber kann diesen Chat nicht sehen. Kläre mit dem Nutzer, wie das Ergebnis zu ihm kommt:
   - Chat teilen (Teilen-Schaltfläche oben, Link kopieren)
   - Artefakt bzw. Doc teilen
   - Datei im vereinbarten Ordner oder Projekt ablegen
   Bitte den Nutzer um den Link oder den Ablageort.
3. **Zusammenfassung schreiben**, höchstens 8 Zeilen, ohne Einleitung:
   - Was wurde erledigt (1–3 Sätze, mit Zahlen wo möglich)
   - Wo liegt das Ergebnis
   - Offene Punkte oder Annahmen, falls vorhanden
   - Was der Auftraggeber als Nächstes prüfen sollte
4. **Übergabe an den Nutzer:**
   - Die Zusammenfassung in einem Codeblock zum Kopieren
   - Der Ergebnis-Link
   - Der Link „Aufgabe im Pool“ aus der Kopfzeile, mit dem Hinweis: dort **Erledigt** klicken, Ergebnis-Link und Zusammenfassung einfügen

Markiere die Aufgabe nicht selbst als erledigt und behaupte das auch nicht. Das macht der Nutzer in Frappe.
