#!/usr/bin/env nu
# WAV zu MP3 Konverter
#
# LIMITIERUNG: Nushell hat keine native Audio-Verarbeitung
# Es muss auf externe Tools wie ffmpeg zurückgegriffen werden

def main [
    input: path                    # Eingabe WAV-Datei oder Verzeichnis
    --output-dir (-o): path        # Ausgabeverzeichnis für MP3-Dateien
    --bitrate (-b): string = "192k" # Bitrate für MP3-Dateien
    --recursive (-r)               # Rekursiv in Unterverzeichnissen suchen
] {
    # Prüfen ob ffmpeg installiert ist
    let has_ffmpeg = (which ffmpeg | is-not-empty)
    if not $has_ffmpeg {
        print "Fehler: ffmpeg ist nicht installiert"
        print "Installation: brew install ffmpeg (macOS) oder apt install ffmpeg (Linux)"
        exit 1
    }

    # Prüfen ob Eingabepfad existiert
    if not ($input | path exists) {
        print $"Fehler: Eingabepfad '($input)' existiert nicht"
        exit 1
    }

    # Standard-Ausgabeverzeichnis setzen
    let out_dir = if ($output_dir | is-empty) {
        $input | path dirname | path join "mp3_output"
    } else {
        $output_dir
    }

    # Ausgabeverzeichnis erstellen
    if not ($out_dir | path exists) {
        mkdir $out_dir
    }

    # Einzelne Datei oder Verzeichnis verarbeiten
    if ($input | path type) == "file" {
        if not ($input | str downcase | str ends-with ".wav") {
            print $"Fehler: '($input)' ist keine WAV-Datei"
            exit 1
        }

        let output_path = (convert_single $input $out_dir $bitrate)
        print $"Konvertiert: '($input)' -> '($output_path)'"
    } else {
        # Verzeichnis verarbeiten
        let wav_files = if $recursive {
            glob $"($input)/**/*.wav"
        } else {
            glob $"($input)/*.wav"
        }

        if ($wav_files | is-empty) {
            print "Keine WAV-Dateien gefunden"
            return
        }

        let converted = ($wav_files | each {|file|
            # Bei rekursiver Suche Verzeichnisstruktur beibehalten
            let sub_dir = if $recursive {
                let rel = ($file | path dirname | path relative-to $input)
                $out_dir | path join $rel
            } else {
                $out_dir
            }

            if not ($sub_dir | path exists) {
                mkdir $sub_dir
            }

            let output_path = (convert_single $file $sub_dir $bitrate)
            print $"Konvertiert: '($file)' -> '($output_path)'"
            1
        } | math sum)

        print $"($converted) WAV-Dateien zu MP3 konvertiert"
    }
}

# Konvertiert eine einzelne WAV-Datei zu MP3
def convert_single [
    input_file: path
    output_dir: path
    bitrate: string
] {
    let name = ($input_file | path parse | get stem)
    let output_path = ($output_dir | path join $"($name).mp3")

    # ffmpeg für die Konvertierung verwenden
    ^ffmpeg -i $input_file -b:a $bitrate -y -loglevel quiet $output_path

    $output_path
}
