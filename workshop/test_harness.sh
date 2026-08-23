#!/usr/bin/env bash
# Test harness for "The Command Line Murders III" (SPOILER-HEAVY - workshop only!)
set -u
cd "$(dirname "$0")/.."

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "  OK   $1"; }
bad() { FAIL=$((FAIL+1)); echo "  FAIL $1"; }

META="workshop/meta.json"
[ -f "$META" ] || { echo "meta.json missing"; exit 1; }
jget() { python3 -c "import json,sys;m=json.load(open('$META'));print(eval('m'+sys.argv[1]))" "$1"; }

HASHER="$(command -v md5 || command -v md5sum)"
SHA256() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 | awk '{print $1}'; else sha256sum | awk '{print $1}'; fi; }

echo "=== 1. Solution chain ==="
MASTER="$(jget "['mastermind']")"
H=$(printf '%s' "$MASTER" | "$HASHER" | awk '{print $NF}')
grep -qi "^$H$" encoded && ok "md5('$MASTER') in encoded" || bad "md5 not in encoded"

N_ROSTER=$(grep -c "^2026-05-09,EVENING,KITCHEN," case/logs/shift-plan.csv)
[ "$N_ROSTER" = "6" ] && ok "shift plan EVENING/KITCHEN == exactly 6 badges" || bad "roster=$N_ROSTER"

PE="$(jget "['verify']['inside_entry']")"
PX="$(jget "['verify']['inside_exit']")"
grep -qF "$PE | ENTRY | KITCHEN-SERVICE | 2207" case/logs/access-log.log && ok "inside man ENTRY 20:31" || bad "entry missing"
grep -qF "$PX | EXIT | KITCHEN-SERVICE | 2207" case/logs/access-log.log && ok "inside man EXIT 21:33" || bad "exit missing"

EB_EXIT="$(jget "['verify']['elim_b_last_exit']")"
EB_ID="$(jget "['elim_b']['badge']")"
grep -qF "$EB_EXIT | EXIT | KITCHEN-SERVICE | $EB_ID" case/logs/access-log.log \
  && ! grep -E "^2026-05-09 (19:5[6-9]|2[01]:[0-5][0-9])" case/logs/access-log.log | grep -q "ENTRY.* $EB_ID$" \
  && ok "elim B left at 19:55 and never returned" || bad "elim-B logic broken"

HU="$(jget "['verify']['history_user_elim']")"
HL="$(jget "['verify']['history_logout']")"
grep -qF "# session 2026-05-09 21:02:55 user:$HU" case/logs/infirmary-history.txt && grep -qF "# logout $HL" case/logs/infirmary-history.txt \
  && ok "infirmary session of elim A overlaps window (alibi)" || bad "history session missing"
MAP=$(grep "^$HU," case/logs/terminal-users.csv | cut -d, -f2)
[ "$MAP" = "$(jget "['elim_a']['badge']")" ] && ok "terminal-users maps session to elim-A badge" || bad "terminal mapping wrong ($MAP)"

WINDOW_IDS=$(grep -E "^2026-05-09 20:(3[0-9]|[45][0-9])" case/logs/access-log.log | grep "KITCHEN-SERVICE" | grep ENTRY | awk -F' \\| ' '{print $NF}' | sort -u)
N_WIN=$(echo "$WINDOW_IDS" | wc -l | tr -d ' ')
[ "$N_WIN" = "2" ] && ok "window-entry set == exactly 2 candidates (2207+2189)" || bad "window IDs=$WINDOW_IDS ($N_WIN)"

active_in_window() {
python3 - "$1" <<'PY'
import sys,re
u=sys.argv[1]
txt=open('case/logs/infirmary-history.txt').read()
for m in re.finditer(r'# session (\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2}):(\d{2}) user:(\S+)\n(.*?)\n# logout (\d{2}):(\d{2}):(\d{2})', txt, re.S):
    _,sh,sm,ss,user,_,eh,em,es=m.groups()
    if user!=u: continue
    start=int(sh)*3600+int(sm)*60+int(ss); end=int(eh)*3600+int(em)*60+int(es)
    if start<=21*3600+20*60 and end>=21*3600+5*60:
        print("YES"); break
PY
}
REMAIN=""
for id in $WINDOW_IDS; do
  u=$(awk -F, -v id="$id" '$2==id{print $1}' case/logs/terminal-users.csv | head -1)
  [ "$(active_in_window "$u")" = "YES" ] || REMAIN="$REMAIN $id"
done
[ "$(echo $REMAIN | tr -d ' ')" = "2207" ] && ok "after alibi elimination exactly 2207 remains" || bad "remaining=[$REMAIN]"

echo "=== 2. Evidence & steganography ==="
TARGET_MD5=$(jget "['verify']['fingerprint_target_md5']")
MATCHED=""
for b in case/evidence/letter-*.txt; do
  bh=$("$HASHER" "$b" | awk '{print $NF}')
  [ "$bh" = "$TARGET_MD5" ] && MATCHED="$b"
done
[ "$(basename "${MATCHED:-x}")" = "letter-c.txt" ] && ok "exactly letter-c matches SHIPMENT-88 attachment" || bad "match=${MATCHED:-none}"

ACRO=$(cut -c1 case/evidence/letter-c.txt | tr -d '\n')
[ "$ACRO" = "$(jget "['verify']['acrostic']")" ] && ok "acrostic == $(jget "['verify']['acrostic']")" || bad "acrostic='$ACRO'"

TARLIST=$(tar -tzf case/evidence/effects-inside-man.tar.gz)
echo "$TARLIST" | grep -q "inventory.txt" && echo "$TARLIST" | grep -q "attachment-coinnote.rot13" && ok "tar archive members complete" || bad "tar contents: $TARLIST"

TMPX=$(mktemp -d)
tar -xzf case/evidence/effects-inside-man.tar.gz -C "$TMPX"
DEC=$(tr 'A-Za-z' 'N-ZA-Mn-za-m' < "$TMPX"/effects-b14/attachment-coinnote.rot13 | SHA256)
WANT_M=$(jget "['verify']['coinnote_rot13_sha256']")
[ "$DEC" = "$WANT_M" ] && ok "rot13 coinnote roundtrip" || bad "coinnote wrong ($DEC)"
rm -rf "$TMPX"

echo "=== 3. Encryption ==="
MAIL=$(openssl enc -d -aes-256-cbc -a -pbkdf2 -iter 10000 -in case/encrypted/mastermind.eml.aes -pass pass:"$(jget "['codename_mastermind']")" 2>/dev/null)
echo "$MAIL" | grep -q "$(jget "['verify']['mail_contains']")" && ok "AES email decrypts with codename" || bad "AES email broken"

EPI=$(openssl enc -d -aes-256-cbc -a -pbkdf2 -iter 10000 -in case/encrypted/epilogue.aes -pass pass:"$(jget "['codename_mastermind']")" 2>/dev/null)
echo "$EPI" | grep -qi "Case 48/III" && ok "epilogue decrypts" || bad "epilogue broken"

echo "=== 4. Git forensics ==="
REPO="case/repos/harborledger-shipping"
C_TEAM=$(jget "['git']['C_TEAM']"); C_SHIPMENT=$(jget "['git']['C_SHIPMENT']"); DANGLING=$(jget "['git']['DANGLING']")
git -C "$REPO" show "$C_TEAM:team/lapwing.txt" | grep -q "$(jget "['verify']['team_txt_contains']")" && ok "team/lapwing.txt recoverable" || bad "lapwing.txt not recoverable"
git -C "$REPO" show "$C_SHIPMENT:customers/shipment-88.csv" | grep -q "$(jget "['verify']['shipment88_contains']")" && ok "shipment-88.csv recoverable" || bad "shipment-88 not recoverable"
FSCK_OUT=$(LC_ALL=C git -C "$REPO" fsck --dangling 2>/dev/null)
echo "$FSCK_OUT" | grep -q "$DANGLING" && ok "dangling commit findable" || bad "dangling missing: $FSCK_OUT"
git -C "$REPO" show "$DANGLING:draft/directive.md" | grep -q "$(jget "['verify']['dangling_contains']")" && ok "directive contains LAPWING" || bad "directive content wrong"

VOR=$(grep -F "$(jget "['verify']['board_contains']")" case/company_registry/harborbank-board.csv)
[ -n "$VOR" ] && ok "board register contains anchor" || bad "board anchor missing"

echo "=== 5. Structure & counts ==="
P_ROWS=$(tail -n +9 case/people | wc -l | tr -d ' ')
WANT_P=$(jget "['counts']['people']")
[ "$P_ROWS" = "$WANT_P" ] && ok "people rows == $WANT_P" || bad "people rows=$P_ROWS expected $WANT_P"

I_CNT=$(ls case/interviews | wc -l | tr -d ' ')
WANT_I=$(jget "['counts']['interviews']")
[ "$I_CNT" = "$WANT_I" ] && ok "interviews == $WANT_I" || bad "interviews=$I_CNT"

for nr in $(jget "['witnesses']" | tr -d "[]" | tr "," "\n" | tr -d " "); do
  [ -f "case/interviews/interview-$nr" ] && ok "witness interview $nr exists" || bad "interview-$nr missing"
done

STREET_BAD=0
for f in case/streets/*.txt; do
  lc=$(wc -l < "$f" | tr -d ' '); [ "$lc" = "300" ] || STREET_BAD=$((STREET_BAD+1))
done
[ "$STREET_BAD" = "0" ] && ok "all street files have 300 lines" || bad "$STREET_BAD street files off"

ADDR_BAD=0
while IFS=$'\t' read -r name gender age address; do
  street=$(echo "$address" | sed -E 's/, line [0-9]+$//'); line=$(echo "$address" | grep -oE '[0-9]+$')
  fname="case/streets/${street// /_}.txt"
  if [ -f "$fname" ]; then
    lc=$(wc -l < "$fname" | tr -d ' ')
    [ "$line" -le "$lc" ] || ADDR_BAD=$((ADDR_BAD+1))
  else
    ADDR_BAD=$((ADDR_BAD+1))
  fi
done < <(tail -n +9 case/people)
[ "$ADDR_BAD" = "0" ] && ok "all addresses within street file bounds" || bad "$ADDR_BAD addresses out-of-range"

echo "=== 6. Checker consistency ==="
for stage in victim inside code master place; do
  HASHES=$(jget "['hashes']['${stage}_sha256']" | tr -d "[]'" | tr ',' '\n' | sed 's/ //g' | grep -v '^$')
  FOUND=0
  for h in $HASHES; do grep -q "$h" checker.sh && FOUND=1; done
  [ "$FOUND" = "1" ] && ok "checker stage '$stage' hash covered" || bad "checker stage '$stage' missing"
done

echo "=== 7. Spoiler sweep ==="
SPOIL_OK=1
for pat in "Petrov" "Holthaus" "Regina" "SPHINX" "LAPWING" "[Ff]ish warehouse"; do
  HITS=$(grep -rlE "$pat" instructions cheatsheet.md README.md LICENSE.md solution hint* checker.sh encoded case/crimescene 2>/dev/null | wc -l | tr -d ' ')
  [ "$HITS" != "0" ] && { SPOIL_OK=0; bad "spoiler '$pat' in narrative files"; }
done
[ "$SPOIL_OK" = "1" ] && ok "no solutions in plaintext narrative"

echo ""
echo "=== SUMMARY: $PASS passed, $FAIL failed ==="
[ "$FAIL" = "0" ]
