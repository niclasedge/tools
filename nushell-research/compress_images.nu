#!/usr/bin/env nu
# Komprimiert JPG-Bilder mit ImageMagick (externes Tool erforderlich)
#
# LIMITIERUNG: Nushell hat keine native Bildverarbeitungs-Library
# Es muss auf externe Tools wie ImageMagick zurückgegriffen werden

def main [
    source_folder: path           # Quellordner mit JPG-Bildern
    --output-name: string = "optimiert"  # Name des Ausgabe-Unterordners
    --quality: int = 85           # JPG-Qualität (1-100)
] {
    # Prüfen ob Quellordner existiert
    if not ($source_folder | path exists) {
        print $"Fehler: Quellordner '($source_folder)' nicht gefunden"
        exit 1
    }

    # Prüfen ob ImageMagick installiert ist
    let has_convert = (which convert | is-not-empty)
    if not $has_convert {
        print "Fehler: ImageMagick ist nicht installiert"
        print "Installation: brew install imagemagick (macOS) oder apt install imagemagick (Linux)"
        exit 1
    }

    let output_path = ($source_folder | path join $output_name)

    # Ausgabeordner erstellen
    if not ($output_path | path exists) {
        mkdir $output_path
        print $"Ausgabeordner erstellt: '($output_path)'"
    } else {
        print $"Ausgabeordner '($output_path)' existiert bereits"
    }

    # JPG-Dateien finden
    let jpg_files = (ls $source_folder
        | where type == "file"
        | where { |f| ($f.name | str downcase | str ends-with ".jpg") or ($f.name | str downcase | str ends-with ".jpeg") }
    )

    if ($jpg_files | is-empty) {
        print "Keine JPG-Dateien gefunden"
        return
    }

    # Bilder komprimieren
    let results = ($jpg_files | each {|file|
        let filename = ($file.name | path basename)
        let output_file = ($output_path | path join $filename)

        try {
            # ImageMagick convert verwenden
            ^convert $file.name -quality $quality -strip $output_file
            print $"Komprimiert: ($filename)"
            { status: "ok", file: $filename }
        } catch {|e|
            print $"Fehler bei ($filename): ($e.msg)"
            { status: "error", file: $filename }
        }
    })

    # Zusammenfassung
    let processed = ($results | where status == "ok" | length)
    let errors = ($results | where status == "error" | length)

    print ""
    print "--- Komprimierungs-Zusammenfassung ---"
    print $"Verarbeitete Bilder: ($processed)"
    print $"Fehler: ($errors)"
    print $"Komprimierte Bilder in: '($output_path)'"
}
