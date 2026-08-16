# justfile — tools
#
# Sammelrepo: mehrere eigenstaendige Werkzeuge und Agenten unter einem Dach.
# Dieses justfile bildet die Ablaeufe ab, die ueber ALLE Unterwerkzeuge gelten
# (test, lint, setup, stats). Einzelne Unterwerkzeuge sind Parameter, keine
# eigenen Rezepte — sonst spiegelt das Root-justfile nur die Unterordner.
#
# Python-Tooling: uv (nie `pip install` von Hand).
# Node-Paketmanager: pnpm (nie npm/npx).

VERCEL_DIR := "agents-vercel-sdk"

# Deckt trotz des Namens den GESAMTEN Python-Teil ab: google-adk, gradio,
# litellm, python-dotenv, requests, pydantic. Es gibt keine zweite
# Requirements-Datei fuer diagram_agent/agent_hub.
PY_REQS := "health-agent/requirements.txt"

# Python laeuft ueber `uv run --with-requirements`: kein Handinstallieren,
# keine zu aktivierende venv. `uv pip` ist bewusst nicht benutzt (Legacy).
PY := "uv run --with-requirements " + PY_REQS + " python3"

[doc('Alle Rezepte auflisten')]
default:
    @just --list --unsorted

# ---------------------------------------------------------------- run --------

# Ruft agent_hub/app.py direkt statt ueber start-agent-frontend.sh auf: das
# Skript startet ein blankes `python3` (ohne Abhaengigkeiten) und reicht seinen
# Port-Parameter nie weiter. Der Port ist in app.py fest auf 7860 verdrahtet.
[doc('Agent-Hub starten: kombiniertes Gradio-Frontend fuer Diagram + Health auf Port 7860')]
[group('run')]
hub:
    {{ PY }} agent_hub/app.py

[doc('Einzelnen Agenten starten: diagram | health | vercel (weitere Argumente werden durchgereicht)')]
[group('run')]
agent name *args:
    #!/usr/bin/env bash
    set -uo pipefail
    case "{{ name }}" in
      diagram) exec {{ PY }} -m diagram_agent {{ args }} ;;
      health)  exec {{ PY }} -m health-agent {{ args }} ;;
      vercel)  cd "{{ VERCEL_DIR }}" && exec pnpm dev {{ args }} ;;
      *)
        echo "Unbekannter Agent: '{{ name }}' — erlaubt: diagram | health | vercel" >&2
        exit 2
        ;;
    esac

# -------------------------------------------------------------- check --------

[doc('Kein Testsuite im Repo: prueft Python-Syntax (compileall) und TypeScript-Typen (tsc --noEmit)')]
[group('check')]
test:
    #!/usr/bin/env bash
    set -uo pipefail
    rc=0
    echo "==> Python: compileall"
    if ! git ls-files '*.py' | grep -v node_modules | tr '\n' '\0' \
         | xargs -0 uv run python3 -m compileall -q; then
      rc=1
    fi
    echo "==> TypeScript: tsc --noEmit ({{ VERCEL_DIR }})"
    if [ -d "{{ VERCEL_DIR }}/node_modules" ]; then
      ( cd "{{ VERCEL_DIR }}" && pnpm exec tsc --noEmit ) || rc=1
    else
      echo "    node_modules fehlt — zuerst 'just setup' ausfuehren" >&2
      rc=1
    fi
    [ "$rc" -eq 0 ] && echo "==> ok" || echo "==> fehlgeschlagen" >&2
    exit "$rc"

[doc('Python-Lint mit ruff (Style + ungenutzte Imports)')]
[group('check')]
lint:
    ruff check .

[doc('Python-Code mit ruff formatieren')]
[group('check')]
format:
    ruff format .

# -------------------------------------------------------------- build --------

[doc('TypeScript-Agenten nach dist/ kompilieren (tsc)')]
[group('build')]
build:
    cd {{ VERCEL_DIR }} && pnpm build

# -------------------------------------------------------------- setup --------

[doc('Abhaengigkeiten holen: Python-Pakete in den uv-Cache, Node-Pakete via pnpm')]
[group('setup')]
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "==> Python: {{ PY_REQS }} in den uv-Cache aufloesen"
    {{ PY }} -c "import gradio, google.adk, litellm, dotenv, requests"
    echo "==> Node: pnpm install ({{ VERCEL_DIR }})"
    ( cd "{{ VERCEL_DIR }}" && pnpm install )
    echo "==> ok"

[doc('Toolchain pruefen und melden, was fehlt')]
[group('setup')]
doctor:
    #!/usr/bin/env bash
    set -uo pipefail
    rc=0
    for tool in just uv pnpm node ruff git dot; do
      if path=$(command -v "$tool" 2>/dev/null); then
        printf '  ok      %-6s %s\n' "$tool" "$path"
      else
        printf '  FEHLT   %-6s\n' "$tool"
        rc=1
      fi
    done
    [ -d "{{ VERCEL_DIR }}/node_modules" ] \
      && echo "  ok      node_modules" \
      || { echo "  FEHLT   node_modules — 'just setup'"; rc=1; }
    [ "$rc" -eq 0 ] || echo "==> unvollstaendig ('dot' kommt aus graphviz)" >&2
    exit "$rc"

[doc('Caches und Build-Artefakte entfernen (__pycache__, dist, ruff-Cache)')]
[group('setup')]
clean:
    #!/usr/bin/env bash
    set -uo pipefail
    find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
    rm -rf "{{ VERCEL_DIR }}/dist" .ruff_cache .pytest_cache .mypy_cache
    echo "==> aufgeraeumt"

# ------------------------------------------------------------ opsdesk --------

[doc('KPI-JSON nach opsdesk Spec 15: Agenten, Werkzeuge, Codezeilen, Tests, Commits')]
[group('opsdesk')]
stats:
    #!/usr/bin/env bash
    set -uo pipefail
    src() { git ls-files "$@" | grep -v node_modules; }

    TS_NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    # Agenten-Paket = Verzeichnis mit einem Agenten-Einstiegspunkt
    AGENTS=$( { src '*/app.py'; src '*/src/orchestrator.ts'; } \
              | cut -d/ -f1 | sort -u | grep -c . )
    # Standalone-Werkzeug = Skript/Seite im Repo-Root plus Nushell-Skripte
    TOOLS=$( { src '*.py' '*.html' | grep -v /; src '*.nu'; } | grep -c . )
    PY_LINES=$(src '*.py' | tr '\n' '\0' | xargs -0 cat 2>/dev/null | wc -l)
    TS_LINES=$(src '*.ts' | tr '\n' '\0' | xargs -0 cat 2>/dev/null | wc -l)
    TESTS=$(src . | grep -cE '(^|/)(test_[^/]*\.py|[^/]*_test\.py|[^/]*\.(test|spec)\.(ts|tsx|js|py))$')
    COMMITS=$(git log --since='30 days ago' --oneline | grep -c .)

    export TS_NOW AGENTS TOOLS PY_LINES TS_LINES TESTS COMMITS
    uv run python3 -c "import json,os; e=os.environ; t=e['TS_NOW']; s={'executor':'just','operation':'stats'}; k=lambda i,n,v,st='ok': {'schema_version':1,'id':i,'name':n,'value':int(v),'unit':'','status':st,'timestamp':t,'source':s}; tv=int(e['TESTS']); print(json.dumps([k('agents','Agenten-Pakete',e['AGENTS']),k('tools','Werkzeuge',e['TOOLS']),k('python_lines','Python-Zeilen',e['PY_LINES']),k('ts_lines','TypeScript-Zeilen',e['TS_LINES']),k('tests','Testdateien',tv,'ok' if tv else 'warn'),k('commits_30d','Commits (30 Tage)',e['COMMITS'])],indent=2))"
