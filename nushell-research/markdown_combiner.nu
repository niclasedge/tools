#!/usr/bin/env nu
# Kombiniert alle Markdown-Dateien in einem Verzeichnis zu einer Datei

# Hauptfunktion
def main [
    input_dir: path    # Eingabeverzeichnis mit Markdown-Dateien
    output_file: path  # Ausgabedatei
] {
    # Prüfen ob Verzeichnis existiert
    if not ($input_dir | path exists) {
        print $"Fehler: Verzeichnis ($input_dir) existiert nicht"
        exit 1
    }

    # Alle Markdown-Dateien finden und sortieren
    let md_files = (glob $"($input_dir)/**/*.md" | sort)

    if ($md_files | is-empty) {
        print $"Warnung: Keine Markdown-Dateien in ($input_dir) gefunden"
        "" | save -f $output_file
        return
    }

    print $"Gefunden: ($md_files | length) Markdown-Dateien"

    # Ausgabeverzeichnis erstellen falls nötig
    let output_parent = ($output_file | path dirname)
    if not ($output_parent | path exists) {
        mkdir $output_parent
    }

    # Dateien kombinieren
    let total = ($md_files | length)
    let combined = ($md_files | enumerate | each {|entry|
        let file = $entry.item
        let index = $entry.index + 1

        # Ausgabedatei überspringen falls im Eingabeverzeichnis
        if ($file | path expand) == ($output_file | path expand) {
            return ""
        }

        print $"Verarbeite Datei ($index)/($total): ($file | path basename)"

        let content = (open $file)

        # Header hinzufügen falls Inhalt nicht mit # beginnt
        let with_header = if ($content | str trim | str starts-with "#") {
            $content
        } else {
            let name = ($file | path parse | get stem)
            $"\n# ($name)\n\n($content)"
        }

        # Trennlinie hinzufügen außer bei letzter Datei
        if $index < $total {
            $"($with_header)\n\n---\n\n"
        } else {
            $with_header
        }
    } | str join "")

    # Speichern
    $combined | save -f $output_file
    print $"Kombinierte Markdown-Datei erstellt: ($output_file)"
}
