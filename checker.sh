#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"

PROGRESS=".checker-progress"
SHA256() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 | awk '{print $1}'; else sha256sum | awk '{print $1}'; fi; }

norm() {
  local s="${1^^}"
  s="${s//Ä/AE}"; s="${s//Ö/OE}"; s="${s//Ü/UE}"; s="${s//ß/SS}"
  s="${s//É/E}"; s="${s//È/E}"; s="${s//Ê/E}"
  local out="" ch i
  for (( i=0; i<${#s}; i++ )); do
    ch="${s:i:1}"
    [[ "$ch" =~ [A-Z0-9] ]] && out="$out$ch"
  done
  printf '%s' "$out"
}

ask() {
  local nr="$1" question="$2" correct="$3" points="$4" answer h ok ALT
  printf '\n== CHECK %s ==\n%s\n> ' "$nr" "$question"
  read -r answer
  h="$(printf '%s' "$(norm "$answer")" | SHA256)"
  ok=0
  for ALT in ${correct//,/ }; do
    [ "$h" = "$ALT" ] && ok=1
  done
  if [ "$ok" = "1" ]; then
    echo "  >> CORRECT. +$points points"
    grep -q "^$nr " "$PROGRESS" 2>/dev/null || printf '%s %s\n' "$nr" "$points" >> "$PROGRESS"
  else
    echo "  >> Not quite. (The case stays open.)"
  fi
}

ART='
 ____________________
|  T E R M I N A L   |
|  C I T Y   I I I   |
|____________________|
   \^~~^/  TCPD
'

case "${1:-}" in
  --status)
    echo "== Progress =="; cat "$PROGRESS" 2>/dev/null || echo "(no checks yet)"
    exit 0 ;;
  --reset)
    rm -f "$PROGRESS"; echo "Progress reset."; exit 0 ;;
esac

echo "$ART"
echo "TCPD CHECKER - CASE FILE 48/III"
echo "(Answers: normal spelling, case does not matter)"
echo

[ "${2:-}" = "--force" ] && rm -f "$PROGRESS"

ask 1 "What was the full name of the victim?" "7c3b9d584cf7a0f721419764f66151300f8a0be42959bf25fdbeeb61893c1618,7c3b9d584cf7a0f721419764f66151300f8a0be42959bf25fdbeeb61893c1618" 20
ask 2 "Who brewed the tea? (full name of the inside man)" "8411c139ecb3e617b470c82a6281181ee834b7c2c0a0e8f1f94a2f6a102f9567" 20
ask 3 "Under which codename did the order come in?" "f8c2c556e154d27fe5df5fd77599abfaad1a6ac572667ceb710351c3caf26982" 20
ask 4 "What is the full name of the mastermind?" "613bfcfdcb27f5552db77177413db3deba8136c6c541ea7b586324c5028d4084,c30452fd2aa03fae0fed6d5af6b0c1be232119e7121cea72ca5a6907669ab63e" 20
ask 5 "Where was the handover supposed to take place? (location)" "38d68a37b9f1066b6f4a9ec7eafa6d0119551cfd0ee53d10c6fc4919ab3e1596,a97800a912abba0368c32070bbbc1816cf4238aef984d86feb13d7a71eff9414,4d7944b54cc5f127b15a207ab8ee441c871ec5914bfd9aba2df029476ab5b3f6,569c57f51fe0f4736067039ad0f056b2f0f1d4312c64e1c7c92e50d83e1700d1" 20

TOTAL=$(awk '{s+=$2} END{print s+0}' "$PROGRESS" 2>/dev/null)
TOTAL=${TOTAL:-0}
echo
echo "== SCORE: $TOTAL / 100 points =="

if [ "$TOTAL" = "100" ]; then
cat <<'EOF'

      _____
     |A .  |-----.
     | /.\ |c)   |   CASE 48/III SOLVED!
     |(_._)| /\/ |
     |  |  |-----'
     |___V_|
EOF
echo "Well done, detective. Submit your report as described in 'solution'."
fi
exit 0
