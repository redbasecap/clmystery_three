CHEATSHEET - THE COMMAND LINE MURDERS III
=========================================

NAVIGATION
----------
ls / cd / pwd              directories
less / cat / head / tail   read files          tail -n 20 file
wc -l                      count lines
find                       find files           find case -name '*letter*'

SEARCHING WITH GREP
-------------------
grep PATTERN file          matching lines
grep -i / -n / -c / -r     ignore case / numbers / count / recursive
grep -A3 -B3               include context
Example:
  grep EVENING case/logs/shift-plan.csv | grep KITCHEN

JOINING TWO FILES
-----------------
Manual with grep, or classic:
  join -t, -1 4 -2 1 file1 file2
Or simply: grep '<BADGE>' case/logs/badge-register.csv

SORT AND SLICE
--------------
sort / sort -u / uniq      sort / deduplicate
cut -d',' -f2              cut columns
tr 'a-z' 'A-Z'             translate characters
cut -c1 file               FIRST character of every line (acrostic!)

ARCHIVES (tar)
--------------
tar -tzf archive.tar.gz            LIST contents
tar -xzf archive.tar.gz -C target  EXTRACT into 'target'

ENCODING / ENCRYPTION
---------------------
openssl base64 -d -in file       base64 decode (portable)
ROT13: tr 'A-Za-z' 'N-ZA-Mn-za-m'
AES (openssl, used in this case):
  openssl enc -d -aes-256-cbc -a -pbkdf2 -iter 10000 \
    -in file.aes -pass pass:PASSWORD
MD5 FINGERPRINTS (macOS/Linux):
  md5 file ...                or   md5sum file ...

GIT FORENSICS (inside the seized repo)
--------------------------------------
sh case/repos/harborledger-shipping/start-investigation.sh
cd case/repos/harborledger-shipping
git log --oneline / --stat / -p
git show SHA:path          pull a file's content from an OLD state!
git fsck --lost-found      find lost commits
git reflog                 where did HEAD point, when?

TIPS FOR DETECTIVES
-------------------
* Log files document themselves: read the '#' lines first.
* Time windows: grep '2026-05-09 2[01]:' ...
* Never guess: every claim needs a file+line as evidence.
