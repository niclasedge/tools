#!/usr/bin/env nu
# Beispiel-Script mit Logging für Crontab-Nutzung
#
# Crontab-Eintrag:
# 0 * * * * /opt/homebrew/bin/nu /Users/niclasedge/GITHUB/tools/nushell-research/example_with_logging.nu /input /output >> /var/log/nushell.log 2>&1

# Konfiguration
const LOG_FILE = "/tmp/nushell_script.log"

# Log-Funktion mit Datei-Ausgabe
def log [level: string, message: string] {
    let timestamp = (date now | format date "%Y-%m-%d %H:%M:%S")
    let entry = $"[($timestamp)] [($level | fill -w 5)] ($message)"

    # Zu stderr (erscheint in Crontab-Log)
    print -e $entry

    # Zusätzlich in eigene Log-Datei
    $entry ++ "\n" | save --append --raw $LOG_FILE
}

def main [
    input_dir: path    # Eingabeverzeichnis
    output_dir: path   # Ausgabeverzeichnis
    --verbose (-v)     # Ausführliche Ausgabe
] {
    log "INFO" $"=== Script gestartet ==="
    log "INFO" $"Input: ($input_dir)"
    log "INFO" $"Output: ($output_dir)"

    # Prüfen ob Verzeichnisse existieren
    if not ($input_dir | path exists) {
        log "ERROR" $"Eingabeverzeichnis existiert nicht: ($input_dir)"
        exit 1
    }

    # Ausgabeverzeichnis erstellen
    if not ($output_dir | path exists) {
        mkdir $output_dir
        log "INFO" $"Ausgabeverzeichnis erstellt: ($output_dir)"
    }

    # Dateien verarbeiten
    let files = (glob $"($input_dir)/**/*" | where { ($in | path type) == "file" })
    log "INFO" $"Gefunden: ($files | length) Dateien"

    let results = ($files | each {|file|
        if $verbose {
            log "DEBUG" $"Verarbeite: ($file | path basename)"
        }

        try {
            # Beispiel-Verarbeitung: Datei kopieren
            let dest = ($output_dir | path join ($file | path basename))
            cp $file $dest
            { status: "ok", file: ($file | path basename) }
        } catch {|e|
            log "ERROR" $"Fehler bei ($file): ($e.msg)"
            { status: "error", file: ($file | path basename) }
        }
    })

    # Zusammenfassung
    let success = ($results | where status == "ok" | length)
    let errors = ($results | where status == "error" | length)

    log "INFO" $"Verarbeitet: ($success) erfolgreich, ($errors) Fehler"
    log "INFO" "=== Script beendet ==="

    # Exit-Code für Crontab
    if $errors > 0 {
        exit 1
    }
}
