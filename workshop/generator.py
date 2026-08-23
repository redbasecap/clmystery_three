#!/usr/bin/env python3
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GAME = REPO
CASE_DIR = GAME / "case"
ASSETS = Path(__file__).resolve().parent / "assets"

rng = random.Random(20260509)

VICTIM_NAME = "Rene Falkenberg"
INSIDE_MAN = "Milan Petrov"
MASTERMIND = "Regina Holthaus"
CODENAME_BOSS = "SPHINX"
CODENAME_INSIDE = "LAPWING"
BADGE_INSIDE = "TC-KITCHEN-2207"
ELIM_A = ("Tom", "Kruger", "2189", "kit-kitchen-03")
ELIM_B = ("George", "Jost", "2311")
DROP = "old Fish Warehouse Ramp 3"

FIRST_F = [
    "Anna","Bertha","Clara","Dora","Elisabeth","Frances","Greta","Hanna","Ines","Johanna",
    "Katherine","Leonie","Martina","Nadja","Ottilie","Petra","Rosa","Sabine","Tanja","Ulrike",
    "Verena","Wanda","Yvonne","Zoe","Amelie","Britta","Cecilia","Dagmar","Emilia","Frieda",
    "Gesine","Henriette","Ida","Josephine","Caroline","Louise","Mathilde","Nicole","Odalys","Pauline",
    "Ronja","Stefanie","Theresa","Uta","Valentina","Wilhelmina","Xenia","Yasmin","Zaida","Almut",
    "Regina","Serpil","Aylin","Fatima","Giulia","Noor","Selma","Leyla","Aisha","Grace",
]
FIRST_M = [
    "Aaron","Bruno","Christian","Dieter","Emil","Falk","Gustav","Heinrich","Ignatz","Jonas",
    "Klaus","Ludwig","Martin","Norbert","Otto","Paul","Reinhold","Stefan","Theodor","Uwe",
    "Vincent","Wolfgang","Xaver","Yusuf","Zacharias","Anton","Boris","Cornelius","Detlef","Emanuel",
    "Florian","George","Hendrik","Ivo","Jakob","Konrad","Lorenz","Matthias","Nicholas","Oskar",
    "Pascal","Quirin","Rasmus","Sebastian","Tobias","Ulf","Veit","Werner","Zeno","Anselm",
    "Rene","Milan","Darius","Tarik","Joost","Kenan","Ruben","Ilja","Neo","Tom",
]
LASTNAMES = [
    "Ackermann","Baumann","Brandt","Czerwinski","Dahlmann","Ehlers","Falkenberg","Gerber","Greenwood","Hartmann",
    "Ivanov","Jensen","Kowalczyk","Lindqvist","Meixner","Neumann","Ostermann","Petrov","Quandt","Richter",
    "Salomon","Schneider","Sommerfeld","Trapp","Uhlmann","Vogler","Weidner","Zabel","Adler","Bergmann",
    "Conradi","Dietrich","Engel","Fricke","Glockner","Hansen","Ibsen","Junker","Kalckreuth","Lorenzen",
    "Mohr","Nissen","Ohlsen","Pietsch","Renner","Sander","Thiel","Ufer","Visser","Wendland",
    "Yildirim","Ziervogel","Baranowski","Aydin","Duarte","Novak","Horvath","Kovacs","Larsen","Myers",
    "Berger","Hofer","Steiner","Wagner","Zimmerman","Reiter","Fox","Hunter","Wolf","Hart",
    "Kruger","Baker","Lehmann","Schulz","Fisher","Weber","Becker","Hoffman","Shepherd","Cook",
    "Farmer","Judge","Klein","Wolfe","Schrader","Newcomb","Brander","Eichhorn","Fielding","Grunert",
    "Hall","Isele","Jost","Kirchner","Laux","Moser","Nagel","Ott","Preuss","Roth",
    "Simon","Turk","Usinger","Vollmer","Wallner","Zorn","Amthor","Buck","Creutz","Deckert",
    "Ebert","Fendt","Glatz","Huber","Irmer","Jahn","Karg","Lutz","Mitchell","Noll",
]
STREETS = [
    "Finster Street","Gisser Alley","Ravenstone Place","Linden Promenade","Green Square","Harbor Line",
    "Northdock Way","Old Steg","Copper Turn","Smithy Lane","Quail Path","Thunder Hill",
    "Silver View","Mist Row","Ravenroost","Oak Wall","Mill Dam","Fish Market",
    "Lantern Wharf","Observatory Row","Kettle Brink","Darkmouth","Windhurst","Hawkfield",
    "Bruch Road","Carp Quay","Blackbird Vale","Zinnwood Promenade","Firewheel","Greystone Court",
    "Spider Lane","Tower Passage","Moorbrook","Cold Valley","Burnet Way","Steinhude Ring",
]
CLUBS = {
    "Friends_of_the_Prison_Library": 46,
    "Iron_Temple_Fitness": 380,
    "Coin_and_Relics_Society": 120,
    "Terminal_City_Library": 410,
    "Museum_of_Bash_History": 95,
    "Blue_Pier_Sailing_Club": 150,
    "Zugzwang_Chess_Club": 88,
    "The_Carp_Angling_Club": 130,
}
MAKES = ["Opel","Ford","Volkswagen","Toyota","Skoda","Fiat","Volvo","Renault","Peugeot","Seat"]
COLORS = ["Blue","Red","Green","Black","White","Silver","Gray","Yellow","Mint green","Brown"]

WITNESSES = [
    {"nr": 21045, "first": "Dietmar", "last": "Kluge", "role": "cell neighbor", "age": 58},
    {"nr": 33712, "first": "Burghard", "last": "Fink", "role": "head of kitchen", "age": 61},
    {"nr": 29864, "first": "Josefine", "last": "Peters", "role": "prison librarian", "age": 44},
]

RESERVED_LAST = {"Petrov", "Holthaus", "Falkenberg", "Kruger", "Jost", "Kluge", "Fink", "Peters"}
NAMES_TAKEN = set()
PEOPLE = []
LIBRARY_CIRCLE = []

def unique_name(gender):
    while True:
        fn = rng.choice(FIRST_M if gender == "M" else FIRST_F)
        ln = rng.choice(LASTNAMES)
        if ln in RESERVED_LAST:
            continue
        if (fn, ln) in NAMES_TAKEN:
            continue
        NAMES_TAKEN.add((fn, ln))
        return fn, ln

def make_person(first=None, last=None, gender=None, age=None, street=None):
    g = gender or rng.choice(["M", "F", "F", "M", "X"])
    if first is None or last is None:
        first, last = unique_name(g)
    else:
        assert (first, last) not in NAMES_TAKEN, f"Duplicate: {first} {last}"
        NAMES_TAKEN.add((first, last))
    st = street or rng.choice(STREETS)
    p = {"first": first, "last": last, "gender": g, "age": age or rng.randint(16, 90),
         "street": st, "line": rng.randint(1, 300)}
    PEOPLE.append(p)
    return p

def find_person(last, first=None):
    for p in PEOPLE:
        if p["last"] == last and (first is None or p["first"] == first):
            return p
    return None

def fmt_addr(street, line):
    return f"{street.replace('_', ' ')}, line {line}"

def load_alice():
    txt = (ASSETS / "alice_en.txt").read_text(encoding="utf-8")
    txt = re.sub(r"\s+", " ", txt)
    words = [w.strip(',.;:!?()[]"' + "'*_") for w in txt.split()]
    return [w for w in words if len(w) > 2 and not any(ch.isdigit() for ch in w)]

ALICE = load_alice()

def noise_sentence(lo=8, hi=16):
    return " ".join(rng.choice(ALICE) for _ in range(rng.randint(lo, hi))).capitalize() + "."

def noise_paragraph(lines=4):
    return "\n".join(noise_sentence() for _ in range(lines))

def ts(y=2026, mo=5, d=9, h=0, mi=0, se=0):
    return f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{se:02d}"

def norm(s):
    s = s.upper()
    s = s.replace("É", "E").replace("È", "E").replace("Ê", "E")
    return "".join(c for c in s if c.isalnum())

def sha(*variants):
    return ",".join(hashlib.sha256(norm(v).encode()).hexdigest() for v in variants)

def md5hex(s):
    return hashlib.md5(s.encode()).hexdigest()

def build_streets():
    d = CASE_DIR / "streets"
    d.mkdir(parents=True, exist_ok=True)
    for s in STREETS:
        with open(d / (s.replace(" ", "_") + ".txt"), "w", encoding="utf-8") as f:
            for _ in range(300):
                f.write(noise_sentence(9, 18) + "\n")

def build_people():
    for _ in range(6590):
        make_person()
    inside = make_person(INSIDE_MAN.split()[0], INSIDE_MAN.split()[1], "M", 26, "Fish Market")
    inside["line"] = 87
    victim = make_person(VICTIM_NAME.split()[0], VICTIM_NAME.split()[1], "M", 49, "Harbor Line")
    victim["line"] = 205
    boss = make_person(MASTERMIND.split()[0], MASTERMIND.split()[1], "F", 57, "Silver View")
    boss["line"] = 11
    ea = make_person(ELIM_A[0], ELIM_A[1], "M", 34, "Cold Valley"); ea["line"] = 66
    eb = make_person(ELIM_B[0], ELIM_B[1], "M", 41, "Moorbrook"); eb["line"] = 178
    make_person(WITNESSES[0]["first"], WITNESSES[0]["last"], "M", 58, "Cold Valley")["line"] = 39
    make_person(WITNESSES[1]["first"], WITNESSES[1]["last"], "M", 61, "Fish Market")["line"] = 4
    make_person(WITNESSES[2]["first"], WITNESSES[2]["last"], "F", 44, "Observatory Row")["line"] = 92
    pre = """***************
To get to a street where someone lives, use the file for that street
name in the 'streets' subdirectory. To knock on their door and figure
out who they are, read the line number they live on from that file.
If a line looks like gibberish, you are at the wrong house.
***************

NAME\tSEX\tAGE\tADDRESS"""
    lines = [pre]
    for p in PEOPLE:
        lines.append(f"{p['first']} {p['last']}\t{p['gender']}\t{p['age']}\t{fmt_addr(p['street'], p['line'])}")
    (CASE_DIR / "people").write_text("\n".join(lines) + "\n", encoding="utf-8")

def build_vehicles():
    lines = ["PLATE\tMAKE\tCOLOR\tYEAR\tOWNER"]
    used = set()
    def plate():
        while True:
            pl = f"TC-{rng.randint(100,999)}-{chr(rng.randint(65,90))}{chr(rng.randint(65,90))}"
            if pl not in used:
                used.add(pl); return pl
    for _ in range(2500):
        o = rng.choice(PEOPLE)
        lines.append(f"{plate()}\t{rng.choice(MAKES)}\t{rng.choice(COLORS)}\t{rng.randint(1998, 2026)}\t{o['first']} {o['last']}")
    lines.append(f"TC-{rng.randint(100,999)}-WK\tSimson\tBlack\t1992\t{INSIDE_MAN}")
    (CASE_DIR / "vehicles").write_text("\n".join(lines) + "\n", encoding="utf-8")

def build_memberships():
    d = CASE_DIR / "memberships"
    d.mkdir(parents=True, exist_ok=True)
    pool = PEOPLE[:]
    rng.shuffle(pool)
    idx = 0
    for club, size in CLUBS.items():
        members = []
        while len(members) < size and idx < len(pool):
            members.append(pool[idx]); idx += 1
        if club == "Friends_of_the_Prison_Library":
            for name in [(INSIDE_MAN.split()[0], INSIDE_MAN.split()[1]),
                         (MASTERMIND.split()[0], MASTERMIND.split()[1]),
                         (ELIM_A[0], ELIM_A[1]), (ELIM_B[0], ELIM_B[1])]:
                p = find_person(name[1], name[0])
                if p not in members:
                    members.append(p)
            CLUBS[club] = len(members)
            LIBRARY_CIRCLE.clear(); LIBRARY_CIRCLE.extend(members)
        with open(d / club, "w", encoding="utf-8") as f:
            f.write(f"Member list {club.replace('_', ' ')}\nAs of: 2026-05-01\n\n")
            for m in sorted(members, key=lambda x: x["last"]):
                f.write(f"{m['last']}, {m['first']}\n")

def build_interviews():
    d = CASE_DIR / "interviews"
    d.mkdir(parents=True, exist_ok=True)
    stmts = [
        "I saw nothing. I was up all night with my book.",
        "Who? Me? At that hour I was asleep. Ask my lawyer.",
        "I only heard a cat. Or was it a moped?",
        "The tea here is awful. Nobody drinks it willingly.",
        "Books are rare in here. Donated ones even rarer.",
        "My neighbor had visitors. I will say no more without a lawyer.",
        "I started on Monday. I know nothing about anything.",
        "Bitter almond? You smell that instantly. I smelled nothing.",
    ]
    for _ in range(500):
        nr = rng.randint(10000, 99999)
        while (d / f"interview-{nr}").exists():
            nr = rng.randint(10000, 99999)
        body = noise_paragraph(3) + "\n\n" + rng.choice(stmts) + "\n\n" + noise_paragraph(2) + "\n"
        (d / f"interview-{nr}").write_text(body, encoding="utf-8")

    z = WITNESSES
    (d / f"interview-{z[0]['nr']}").write_text(
        f"STATEMENT {z[0]['first']} {z[0]['last']}, {z[0]['role']}, {z[0]['age']} (cell B-15):\n\n"
        "  |=|  |=|  |=|  |=|\n"
        "  |=|  |=|  |=|  |=|   <- bars between B-14 and B-15\n\n"
        "Rene was in good spirits because his testimony was coming up. In the evening the\n"
        "kitchen brought tea as always around 21:00. I never touch mine. He drank his;\n"
        "shortly after 21:12 he went strangely quiet. I called for help at once. He\n"
        "smelled... odd. Like BITTER ALMONDS. For weeks he had read only one book: a\n"
        "donated one, sticker from the MUSEUM OF BASH HISTORY.\n", encoding="utf-8")

    (d / f"interview-{z[1]['nr']}").write_text(
        f"STATEMENT {z[1]['first']} {z[1]['last']}, {z[1]['role']}, {z[1]['age']}:\n\n"
        "My people take the tea to the blocks at 21:00 sharp. Who drove is in the SHIFT\n"
        "PLAN. I myself was at goods reception until 20:30, then the office. Odd detail:\n"
        "for months someone keeps donating books to the prison library, always shipped\n"
        "via GREENFLASH CATERING. Donation slips carry different names but always the\n"
        "same address.\n", encoding="utf-8")

    (d / f"interview-{z[2]['nr']}").write_text(
        f"STATEMENT {z[2]['first']} {z[2]['last']}, {z[2]['role']}, {z[2]['age']}:\n\n"
        "The book from B-14 came with the latest book donation. The donor circle calls\n"
        "itself 'Friends of the Prison Library' - see our member list. And inside the\n"
        "book was an unsigned LETTER, filed with his personal effects. The deceased\n"
        "loved reciting the FIRST LETTERS of each line like a poem, always grinning.\n", encoding="utf-8")

GIT_ENV_BASE = {
    "GIT_AUTHOR_NAME": "dispatch-harborledger",
    "GIT_AUTHOR_EMAIL": "dispatch@harborledger.example",
    "GIT_COMMITTER_NAME": "dispatch-harborledger",
    "GIT_COMMITTER_EMAIL": "dispatch@harborledger.example",
}

def git_run(repo, *args, date=None):
    env = dict(os.environ); env.update(GIT_ENV_BASE)
    if date:
        iso = date.strftime("%Y-%m-%dT%H:%M:%S +0100")
        env["GIT_AUTHOR_DATE"] = iso; env["GIT_COMMITTER_DATE"] = iso
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env=env)

def git_out(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True, env=dict(os.environ, **GIT_ENV_BASE)).stdout

SHIPMENT88_CSV = """# SHIPMENT 88 - INTERNAL
# Format: KEY: VALUE
DATE: 2026-05-08
RECIPIENT: STEINBERG PENITENTIARY - KITCHEN (ACCOMPANIES THE BOOK DONATION)
CONTENTS: 1 NON-FICTION BOOK + 1 POUCH OF CULINARY HERBS ('TEA HERBS')
HANDOVER: OLD FISH WAREHOUSE, RAMP 3 - MAY 22, 23:00
CUSTOMER(CODE): R.H.
DRIVER(CODENAME): LAPWING
"""

LAPWING_TXT = """TEAM FILE (INTERNAL)
Codename : LAPWING
Area     : KITCHEN, STEINBERG PENITENTIARY
Badge-No : TC-KITCHEN-2207
Terminal : kit-kitchen-01
Contact codename: SPHINX
Status   : active
Note     : The badge doubles as a terminal ID in the infirmary.
"""

GECKO_TXT = """TEAM FILE (INTERNAL)
Codename : GECKO
Area     : LAUNDRY
Badge-No : TC-LAUNDRY-3311
Terminal : la-laundry-02
Contact codename: SPHINX
Status   : on vacation
"""

DIRECTIVE_MD = """# DIRECTIVE (AFTER SHIPMENT 88)
Switch channels. LAPWING stays silent forever now.
Next payment as usual, Moneros. - S.
"""

def build_logs():
    d = CASE_DIR / "logs"
    d.mkdir(parents=True, exist_ok=True)

    staff_ids = {
        "2207": (INSIDE_MAN.split()[1], INSIDE_MAN.split()[0]),
        ELIM_A[2]: (ELIM_A[1], ELIM_A[0]),
        ELIM_B[2]: (ELIM_B[1], ELIM_B[0]),
        "2154": None, "2078": None, "2301": None,
    }
    pool = [p for p in PEOPLE if p not in LIBRARY_CIRCLE]
    for aid in ["2154", "2078", "2301"]:
        p = pool[rng.randrange(len(pool))]
        staff_ids[aid] = (p["last"], p["first"])

    plan = ["# SHIFT PLAN STEINBERG PENITENTIARY - MAY 9, 2026",
            "# Format: DATE,SHIFT,AREA,BADGE-NO",
            "# Badge to name mapping: badge-register.csv"]
    for aid in staff_ids:
        plan.append(f"2026-05-09,EVENING,KITCHEN,{aid}")
    for _ in range(80):
        area = rng.choice(["GATE", "WORKSHOP", "LAUNDRY", "LIBRARY", "YARD"])
        plan.append(f"2026-05-{rng.randint(1, 9):02d},{rng.choice(['EARLY','LATE','EVENING','NIGHT'])},{area},{rng.randint(2000, 2400)}")
    (d / "shift-plan.csv").write_text("\n".join(plan) + "\n", encoding="utf-8")

    reg = ["# BADGE REGISTER OF STEINBERG PENITENTIARY", "# Format: BADGE-NO,LASTNAME,FIRSTNAME"]
    for aid, name in staff_ids.items():
        if name:
            reg.append(f"{aid},{name[0]},{name[1]}")
    for _ in range(280):
        p = PEOPLE[rng.randrange(len(PEOPLE))]
        reg.append(f"{rng.randint(2000, 2400)},{p['last']},{p['first']}")
    (d / "badge-register.csv").write_text("\n".join(reg) + "\n", encoding="utf-8")

    access = ["# ACCESS LOG KITCHEN SERVICE DOOR - MAY 9, 2026",
              "# Format: TIMESTAMP | DIRECTION | DOOR | BADGE-NO"]
    def acc(ts_, direction, aid):
        access.append(f"{ts_} | {direction} | KITCHEN-SERVICE | {aid}")
    acc(ts(h=18, mi=58), "ENTRY", ELIM_B[2]); acc(ts(h=19, mi=55), "EXIT", ELIM_B[2])
    acc(ts(h=20, mi=31), "ENTRY", "2207");     acc(ts(h=21, mi=33), "EXIT", "2207")
    acc(ts(h=20, mi=34), "ENTRY", ELIM_A[2]); acc(ts(h=21, mi=47), "EXIT", ELIM_A[2])
    acc(ts(h=20, mi=26), "ENTRY", "2154");    acc(ts(h=21, mi=59), "EXIT", "2154")
    acc(ts(h=17, mi=41), "ENTRY", "2078");    acc(ts(h=18, mi=2), "EXIT", "2078")
    acc(ts(h=22, mi=14), "ENTRY", "2301");    acc(ts(h=23, mi=5), "EXIT", "2301")
    for _ in range(50):
        day = rng.choice([7, 8, 10])
        access.append(ts(d=day, h=rng.randint(6, 22), mi=rng.randint(0, 59), se=rng.randint(0, 59)) +
                      f" | {rng.choice(['ENTRY','EXIT'])} | {rng.choice(['KITCHEN-SERVICE','MAIN GATE','YARD'])} | {rng.randint(2000, 2400)}")
    access.sort(key=lambda ln: ln.split(" | ")[0])
    (d / "access-log.log").write_text("\n".join(access) + "\n", encoding="utf-8")

    hist = [
        "# TERMINAL HISTORY INFIRMARY (PHARMACY) - EXCERPT MAY 9, 2026",
        "# Format: '# session <TIME> user:<ID>' followed by commands",
        "# ID to badge mapping: terminal-users.csv",
        "# session 2026-05-09 19:40:11 user:physician-lead",
        "grep -i headache dosage-forms.csv",
        "# logout 19:52:03",
        "",
        "# session 2026-05-09 21:02:55 user:" + ELIM_A[3],
        "less tea-inventory.csv",
        "grep -i 'bitter almond' substances-reference.csv",
        "man curl",
        "# logout 21:24:40",
        "",
        "# session 2026-05-09 21:41:07 user:kit-kitchen-01",
        "tail -n 3 deliveries-today.log",
        "# logout 21:48:59",
        "",
        "# session 2026-05-09 22:10:41 user:nursing-night",
        "echo 'Quiet shift' >> logbook.txt",
        "# logout 22:15:12",
    ]
    (d / "infirmary-history.txt").write_text("\n".join(hist) + "\n", encoding="utf-8")

    tnut = ["# TERMINAL IDS OF THE INFIRMARY", "# Format: ID,BADGE-NO",
            "kit-kitchen-01,2207", ELIM_A[3] + "," + ELIM_A[2],
            "la-laundry-02,3311", "physician-lead,1901", "nursing-night,1966"]
    for _ in range(30):
        tnut.append(f"user-{rng.randint(100,999)},{rng.randint(2000,2400)}")
    (d / "terminal-users.csv").write_text("\n".join(tnut) + "\n", encoding="utf-8")

LETTER_C = """Sweet summer greetings from the coast;
Pentecost is coming and the ferries haul
Herring sand aboard while gulls quarrel.
Indecisive as ever, the weather lingers;
Next door's cat sleeps all day in my chair.
Xanthippe is her name now. Until soon!
"""

FINGER_TARGET = hashlib.md5(LETTER_C.encode()).hexdigest()

def build_evidence():
    d = CASE_DIR / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    for name, body in [("letter-a.txt", noise_paragraph(6)),
                       ("letter-b.txt", noise_paragraph(7)),
                       ("letter-c.txt", LETTER_C),
                       ("letter-d.txt", noise_paragraph(6)),
                       ("letter-e.txt", noise_paragraph(7))]:
        (d / name).write_text(body + ("" if body.endswith("\n") else "\n"), encoding="utf-8")

    coin_plain = ("Coin pouch: 1 physical Monero pendant, engraved inside:\n"
                  "fish warehouse, Ramp 3. Never go there alone. - K.\n")
    rot = coin_plain.translate(str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))
    inventory = ("INVENTORY OF PERSONAL EFFECTS - CELL B-14 (FALKENBERG, R.)\n"
                 "==========================================================\n"
                 "1  wristwatch, broken\n"
                 "1  paperback 'The Art of the Command Line'\n"
                 "     - inside: 1 unsigned letter (see separate evidence item)\n"
                 "1  coin pouch with 1 metal coin (pendant)\n"
                 "1  pouch of herbs, label 'TEA HERBS'\n"
                 "1  handwritten note, ROT13-scrambled:\n"
                 "     >>> see attachment-coinnote.rot13 <<<\n")
    tmpd = d / "_tar_tmp"
    tmpd.mkdir()
    (tmpd / "inventory.txt").write_text(inventory, encoding="utf-8")
    (tmpd / "attachment-coinnote.rot13").write_text(rot, encoding="utf-8")
    with tarfile.open(d / "effects-inside-man.tar.gz", "w:gz") as tf:
        tf.add(tmpd / "inventory.txt", arcname="effects-b14/inventory.txt")
        tf.add(tmpd / "attachment-coinnote.rot13", arcname="effects-b14/attachment-coinnote.rot13")
    shutil.rmtree(tmpd)

def build_fingerprints():
    d = CASE_DIR / "logs"
    fp = ["# FINGERPRINTS OF INTERCEPTED WRITINGS (INTERNAL LIST)",
          "# Format: MD5,ITEM",
          "# From surveillance of the parcel route. Exactly ONE of the letters",
          "# seized from B-14 must appear here."]
    fp.append(f"{FINGER_TARGET},SHIPMENT-88-ATTACHMENT")
    for obj in ["NEWSPAPER-CLIPPING-MAY", "KITCHEN-ORDER-WEEK19",
                "LIBRARY-RECEIPT-0413", "CANTINE-CREDIT-B14"]:
        fp.append(f"{hashlib.md5((obj + str(rng.random())).encode()).hexdigest()},{obj}")
    (d / "fingerprints.txt").write_text("\n".join(fp) + "\n", encoding="utf-8")

MAIL_PLAIN = (
    "From: unknown@relay.harborledger.example\n"
    "To: LAPWING\n"
    "Subject: Shipment 88\n\n"
    "The witness goes quiet by Thursday. Your reward waits at the old\n"
    "fish warehouse, Ramp 3, as agreed. Radio silence afterwards.\n"
    "Burn after reading. - S.\n")

EPILOGUE_PLAIN = """EPILOGUE - SEALED TCPD REPORT
=============================
On Friday, May 22, at 23:00, the TCPD arrested the courier at the old
fish warehouse, Ramp 3 - and got a surprise: the rider was M. Kowalczyk,
earning her freedom. Her statement led straight to the chairwoman of
the Harbor Bank. Case 48/III: CLOSED. The Harbor Ledger is history.
"""

ROT13 = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm")

def build_encrypted():
    d = CASE_DIR / "encrypted"
    d.mkdir(parents=True, exist_ok=True)
    src = d / "_mail.tmp"
    src.write_text(MAIL_PLAIN, encoding="utf-8")
    enc = d / "mastermind.eml.aes"
    subprocess.run(["openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2", "-iter", "10000",
                    "-a", "-in", str(src), "-out", str(enc), "-pass", "pass:" + CODENAME_BOSS],
                   check=True, capture_output=True)
    chk = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-a", "-pbkdf2",
                          "-iter", "10000", "-in", str(enc), "-pass", "pass:" + CODENAME_BOSS],
                         check=True, capture_output=True)
    assert chk.stdout.decode() == MAIL_PLAIN, "AES roundtrip failed"
    src.unlink()

def build_git_repo():
    repo = CASE_DIR / "repos" / "harborledger-shipping"
    if repo.exists():
        shutil.rmtree(repo)
    repo.mkdir(parents=True)
    git_run(repo, "init", "-b", "main", date=datetime(2026, 3, 1, 9, 0, 0))
    (repo / "README.md").write_text("# Harbor Ledger Shipping - internal tour planning\nDiscreet. Always.\n", encoding="utf-8")
    (repo / "config").mkdir()
    (repo / "config" / "warehouse.txt").write_text(noise_paragraph(6) + "\n", encoding="utf-8")
    git_run(repo, "add", "-A"); git_run(repo, "commit", "-m", "Initial depot tours",
                                        date=datetime(2026, 3, 1, 9, 12, 0))
    (repo / "customers").mkdir()
    (repo / "customers" / "shipment-71.csv").write_text("# SHIPMENT 71\nRECIPIENT: KETTLE BRINK 4\nCONTENTS: PALLETS\n", encoding="utf-8")
    git_run(repo, "add", "-A"); git_run(repo, "commit", "-m", "Record shipment 71",
                                        date=datetime(2026, 3, 18, 15, 40, 0))
    (repo / "team").mkdir()
    (repo / "team" / "lapwing.txt").write_text(LAPWING_TXT, encoding="utf-8")
    (repo / "team" / "gecko.txt").write_text(GECKO_TXT, encoding="utf-8")
    git_run(repo, "add", "-A"); git_run(repo, "commit", "-m", "Add team files",
                                        date=datetime(2026, 4, 28, 17, 5, 0))
    C_TEAM = git_out(repo, "rev-parse", "HEAD").strip()
    (repo / "customers" / "shipment-88.csv").write_text(SHIPMENT88_CSV, encoding="utf-8")
    git_run(repo, "add", "-A"); git_run(repo, "commit", "-m", "Set up shipment 88",
                                        date=datetime(2026, 5, 8, 22, 15, 0))
    C_SHIPMENT = git_out(repo, "rev-parse", "HEAD").strip()
    (repo / "draft").mkdir()
    (repo / "draft" / "directive.md").write_text(DIRECTIVE_MD, encoding="utf-8")
    git_run(repo, "add", "-A"); git_run(repo, "commit", "-m", "Draft directive (internal)",
                                        date=datetime(2026, 5, 9, 23, 48, 0))
    DANGLING = git_out(repo, "rev-parse", "HEAD").strip()
    git_run(repo, "reset", "--hard", "HEAD~1")
    (repo / "team" / "lapwing.txt").unlink()
    (repo / "team" / "gecko.txt").unlink()
    git_run(repo, "add", "-A"); git_run(repo, "commit", "-m", "Audit: remove sensitive team files",
                                        date=datetime(2026, 5, 10, 6, 2, 0))
    (repo / "customers" / "shipment-88.csv").unlink()
    git_run(repo, "add", "-A"); git_run(repo, "commit", "-m", "Archive cleanup: shipment 88 removed",
                                        date=datetime(2026, 5, 10, 6, 5, 0))
    if (repo / "team").is_dir() and not any((repo / "team").iterdir()):
        (repo / "team").rmdir()
    subprocess.run(["git", "reflog", "expire", "--expire-unreachable=now", "--all"],
                   cwd=repo, check=True, capture_output=True, env=dict(os.environ, **GIT_ENV_BASE))
    fsck = subprocess.run(["git", "fsck", "--dangling"], cwd=repo, capture_output=True,
                          text=True, env=dict(os.environ, **GIT_ENV_BASE)).stdout
    assert DANGLING in fsck, f"dangling commit missing: {fsck!r}"
    archiv = repo / ".gitarchiv"
    if archiv.exists():
        shutil.rmtree(archiv)
    shutil.copytree(repo / ".git", archiv)
    starter = repo / "start-investigation.sh"
    starter.write_text(
        "#!/bin/sh\n"
        "# Restore the seized server image of the shipping firm:\n"
        "set -e\n"
        'DIR="$(cd "$(dirname "$0")" && pwd)"\n'
        'rm -rf "$DIR/.git"\n'
        'cp -R "$DIR/.gitarchiv" "$DIR/.git"\n'
        'echo "Image restored. From now on: cd into this directory and use git."\n',
        encoding="utf-8")
    os.chmod(starter, 0o755)
    return {"C_TEAM": C_TEAM, "C_SHIPMENT": C_SHIPMENT, "DANGLING": DANGLING}

def build_company_registry():
    d = CASE_DIR / "company_registry"
    d.mkdir(parents=True, exist_ok=True)
    rows = ["# HARBOR BANK TERMINAL CITY - BOARD (PUBLIC REGISTER)",
            "# Format: LASTNAME,FIRSTNAME,CODE,ROLE",
            "Holthaus,Regina,RH,Chairwoman"]
    for k in ["TW","MB","FK","LS"]:
        p = PEOPLE[rng.randrange(len(PEOPLE))]
        rows.append(f"{p['last']},{p['first']},{k},Board member")
    (d / "harborbank-board.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

CRIME_SCENE = """CASE FILE 48/III - THE SILENT WITNESS
=====================================

      _______________________________
     |  S T E I N B E R G   P E N    |
     |                               |
     |  |=|=|=|=|=|=|=|=|=|=|=|=|=|  |
     |  |=|  B - 1 4          |=|=|  |   CELL B-14
     |  |=|=|=|=|=|=|=|=|=|=|=|=|=|  |
     |         ___                   |
     |        (   )  <- TEA CUP      |   CRIME NIGHT: MAY 9/10, 2026
     |         \\_/      BITTER ALMOND|
     |_______________________________|

INCIDENT REPORT
---------------
Rene FALKENBERG (49), defendant in the 'Harbor Ledger' case, was due to
testify as key witness on Thursday. On the evening of May 9 he was found
dead in cell B-14 - poisoned with CYANIDE in his evening tea (21:12,
classic BITTER ALMOND smell).

No break-in. The tea arrived through the regular kitchen route. For
weeks Falkenberg had read only one book - a DONATION to the prison
library, sticker 'MUSEUM OF BASH HISTORY'. Inside the book: an unsigned
letter. The guards heard him reciting the FIRST LETTERS of each line,
'like a poem'.

Background (Case 47/II): Falkenberg's courier is now a protected
prosecution witness - she cooperates. Her network, the 'Harbor Ledger',
wants to make sure Falkenberg never testifies.

Evidence
--------
* Personal effects from B-14 (packed as an archive):
      case/evidence/effects-inside-man.tar.gz
* Five unsigned letters seized from the cell:
      case/evidence/letter-a.txt ... letter-e.txt
* Fingerprint list from the intercepted parcel route:
      case/logs/fingerprints.txt
* An encrypted email from the kitchen management server:
      case/encrypted/mastermind.eml.aes
* The seized tour system of the shipping arm 'Harbor Ledger':
      case/repos/harborledger-shipping   (a real Git repository!)
* Logs of the day (shift plan, access, infirmary terminal):
      case/logs/

Witnesses (video statements, note the numbers!)
-----------------------------------------------
STATEMENT #%(z0)s - %(z0v)s %(z0n)s, cell neighbor:
   smelled BITTER ALMOND on the tea; the book and his 'poem' habit.
   Details: case/interviews/interview-%(z0)s

STATEMENT #%(z1)s - %(z1v)s %(z1n)s, head of kitchen:
   the tea route follows the SHIFT PLAN; books keep arriving via
   GREENFLASH CATERING.
   Details: case/interviews/interview-%(z1)s

STATEMENT #%(z2)s - %(z2v)s %(z2n)s, prison librarian:
   the letter was INSIDE the book; the deceased loved spelling out
   the FIRST LETTERS of each line.
   Details: case/interviews/interview-%(z2)s

The TCPD needs your report: WHO brewed the tea - and WHO ordered it?
Check your progress anytime with ./checker.sh
"""

INSTRUCTIONS = """INSTRUCTIONS - THE COMMAND LINE MURDERS III
===========================================

Terminal City, a few weeks later: a key witness dies in his cell -
poisoned, precise, ordered. This time the trail leads through shift
plans, access logs, a terminal history, a tar archive, a letter with a
hidden code and the tour system of the 'Harbor Ledger'.

RULES
-----
1. Use the terminal only. No text editor or GUI tools to view files
   inside the 'case/' folder.
2. Allowed: 'cat', 'less', 'head', 'tail', 'grep', 'find', 'sort',
   'uniq', 'cut', 'tr', 'tar', 'openssl', 'git', 'md5' (or 'md5sum')
   and anything listed in the CHEATSHEET.
3. Everything you need is hidden INSIDE the case folder. You do not
   need the internet while playing.
4. Stuck? The files 'hint1' through 'hint10' help - but read them in
   order and only when you are truly stuck.

GETTING STARTED
---------------
    cat instructions       <- this file
    cat cheatsheet.md      <- command line reference
    ls case/
    less case/crimescene   <- your first real lead!

TOOLS
-----
    ./checker.sh           <- validates your progress (optional, fun)

GOAL
----
Find out WHO brewed the tea, WHO ordered it - and under which codename
the order came in. The closing procedure is in 'solution'.

Good luck, detective.
"""

HINTS = [
"""HINT 1
======
Start with:  less case/crimescene
Note down: victim, poison time (21:12), the BOOK, the LETTER and the
three STATEMENT numbers of the witnesses.""",

"""HINT 2
=======
The three witness details live here:
    ls case/interviews
    cat case/interviews/interview-<NUMBER>
Important: the tea route runs through the KITCHEN, the book donation,
and the hint about the FIRST LETTERS of the letter.""",

"""HINT 3
=======
Who could hand over the tea? Two files belong together:
    case/logs/shift-plan.csv        (who was EVENING/KITCHEN?)
    case/logs/access-log.log        (who entered/left, when?)
Resolve the badge numbers with:
    case/logs/badge-register.csv""",

"""HINT 4
=======
Filter kitchen staff with door access between roughly 20:30 and 21:35.
Then eliminate:
* One person had an ACTIVE SESSION at the infirmary terminal during
  that time (other wing): see infirmary-history.txt and
  terminal-users.csv.
* One person left the door at 19:55 already and never returned.
Exactly ONE badge number remains.""",

"""HINT 5
=======
That remaining person is your inside man. His belongings were packed:
    tar -tzf case/evidence/effects-inside-man.tar.gz
    tar -xzf case/evidence/effects-inside-man.tar.gz -C /tmp/effects
The inventory lists: one unsigned letter - and one ROT13 note.""",

"""HINT 6
=======
Which of the five letters from B-14 was smuggled? Surveillance lists
fingerprints (MD5):
    case/logs/fingerprints.txt
Check every letter:
    md5 case/evidence/letter-*.txt     (Linux: md5sum)
Exactly ONE matches 'SHIPMENT-88-ATTACHMENT'.""",

"""HINT 7
=======
The real letter carries a hidden code: take the FIRST CHARACTER of
every line:
    cut -c1 case/evidence/letter-c.txt | tr -d '\\n'
What you read is the CONTACT CODENAME of the mastermind - six letters,
a mythical creature. Remember it! You need it as a password (hint 8)
and as an answer for the checker.""",

"""HINT 8
=======
The kitchen email is AES-encrypted:
    openssl enc -d -aes-256-cbc -a -pbkdf2 -iter 10000 \\
      -in case/encrypted/mastermind.eml.aes -pass pass:PASSWORD
PASSWORD = the codename from hint 7 (UPPERCASE).""",

"""HINT 9
=======
Who hides behind the code 'R.H.'? Two routes:
* Git forensics in the seized shipping repo:
    sh case/repos/harborledger-shipping/start-investigation.sh
    cd case/repos/harborledger-shipping
  You want: 'team/lapwing.txt' and 'customers/shipment-88.csv' from OLD
  commits (git show COMMIT:PATH) - plus one LOST commit
  (git fsck --lost-found) containing a directive.
* The public register:
    case/company_registry/harborbank-board.csv
  There the CODE column reveals the full name.""",

"""HINT 10
========
Once you have the full name of the mastermind:
    echo -n 'FIRSTNAME LASTNAME' | md5
    grep -if <YOUR-HASH> encoded
How to submit your report is described in 'solution'.""",
]

CHEATSHEET = """CHEATSHEET - THE COMMAND LINE MURDERS III
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
  openssl enc -d -aes-256-cbc -a -pbkdf2 -iter 10000 \\
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
"""

SOLUTION_TEXT = """SOLUTION - HOW TO CLOSE THE CASE
================================

When you are sure you know the full name of the mastermind, verify it
like this (macOS):

    echo -n 'Firstname Lastname' | md5
    grep -if '<YOUR-HASH>' encoded

On Linux it is 'md5sum' instead of 'md5'. If grep finds the hash in the
'encoded' file: congratulations, detective.

Afterwards a sealed EPILOGUE waits for you (you know the password - six
letters, a mythical creature):

    openssl enc -d -aes-256-cbc -a -pbkdf2 -iter 10000 \\
      -in case/encrypted/epilogue.aes -pass pass:PASSWORD

And './checker.sh' will grade your final report.
"""

README = """THE COMMAND LINE MURDERS III
============================

      .______________________________________.
      |  ____  ____  ____  ____  ____  ____   |
      | ||T ||||E ||||R ||||M ||||I ||||N ||  |
      | ||__||||__||||__||||__||||__||||__||  |
      | |/==\\||/==\\||/==\\||/==\\||/==\\||/==\\|  |
      |  CITY III - THE SILENT WITNESS        |
      |______________________________________|

A key witness dies in his cell - poisoned, precise, ordered. This time
the trail leads through shift plans, access logs, a terminal history,
a tar archive, a letter with a hidden code and the Git system of the
'Harbor Ledger'.

Quick start
-----------
    git clone <this-repo>
    cd <repo-name>
    cat instructions
    less case/crimescene

All you need is a terminal (macOS or Linux) with `git`, `openssl`,
`tar` and `base64`. No installs, no sign-up, no internet while playing.

For beginners: `cat cheatsheet.md`
Check progress: `./checker.sh`

About this project
------------------
Part III of the series following "The Command Line Murders" by Noah
Veltman (github.com/veltman/clmystery). All characters and events are
fictional. The filler text is drawn from "Alice's Adventures in
Wonderland" by Lewis Carroll (Public Domain, Project Gutenberg #11).

License: MIT - see LICENSE.md
"""

LICENSE = """MIT License

Copyright (c) 2026 The Command Line Murders III Authors
Concept tradition: "The Command Line Murders" (c) Noah Veltman, MIT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

CHECKER_TEMPLATE = """#!/usr/bin/env bash
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
  printf '\\n== CHECK %s ==\\n%s\\n> ' "$nr" "$question"
  read -r answer
  h="$(printf '%s' "$(norm "$answer")" | SHA256)"
  ok=0
  for ALT in ${correct//,/ }; do
    [ "$h" = "$ALT" ] && ok=1
  done
  if [ "$ok" = "1" ]; then
    echo "  >> CORRECT. +$points points"
    grep -q "^$nr " "$PROGRESS" 2>/dev/null || printf '%s %s\\n' "$nr" "$points" >> "$PROGRESS"
  else
    echo "  >> Not quite. (The case stays open.)"
  fi
}

ART='
 ____________________
|  T E R M I N A L   |
|  C I T Y   I I I   |
|____________________|
   \\^~~^/  TCPD
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

ask 1 "What was the full name of the victim?" "@H_VICTIM@" 20
ask 2 "Who brewed the tea? (full name of the inside man)" "@H_INSIDE@" 20
ask 3 "Under which codename did the order come in?" "@H_CODE@" 20
ask 4 "What is the full name of the mastermind?" "@H_MASTER@" 20
ask 5 "Where was the handover supposed to take place? (location)" "@H_PLACE@" 20

TOTAL=$(awk '{s+=$2} END{print s+0}' "$PROGRESS" 2>/dev/null)
TOTAL=${TOTAL:-0}
echo
echo "== SCORE: $TOTAL / 100 points =="

if [ "$TOTAL" = "100" ]; then
cat <<'EOF'

      _____
     |A .  |-----.
     | /.\\ |c)   |   CASE 48/III SOLVED!
     |(_._)| /\\/ |
     |  |  |-----'
     |___V_|
EOF
echo "Well done, detective. Submit your report as described in 'solution'."
fi
exit 0
"""


def main():
    if CASE_DIR.exists():
        shutil.rmtree(CASE_DIR)
    CASE_DIR.mkdir(parents=True)
    for name in ["encoded", "instructions", "cheatsheet.md", "solution", "README.md", "LICENSE.md"]:
        p = GAME / name
        if p.exists():
            p.unlink()
    for i in range(1, 11):
        p = GAME / f"hint{i}"
        if p.exists():
            p.unlink()

    build_streets()
    build_people()
    build_vehicles()
    build_memberships()
    build_interviews()
    build_logs()
    build_evidence()
    build_fingerprints()
    build_encrypted()
    gitmeta = build_git_repo()
    build_company_registry()

    hashes_out, seen = [], set()
    fillers = ["Alicia Vogt","Benno Krause","Cem Aydin","Dorothea Peters","Emily Brandt",
               "Fenna Holm","Gustav Lehmann","Helga Ruf","Ingolf Bade","Jana Krebs",
               "Carl Petersen","Lena Maak","Morten Siewert","Nadine Kolb","Otto Walker",
               "Pia Dahms","Quinn Harper","Rita Heyer","Sven Frahm","Telse Kruse",
               "Alparslan","Vitus Frech","Wanja Slawik","Xenia Marschner","Yilmaz",
               "Ziska Riemann","Anselm Grunert","Berta Ohlsen","Clemens Usinger","Dagmar Vollmer"]
    for name in fillers + [MASTERMIND]:
        for v in (name, name.lower()):
            h = md5hex(v)
            if h not in seen:
                seen.add(h); hashes_out.append(h)
    rng.shuffle(hashes_out)
    (GAME / "encoded").write_text("\n".join(hashes_out) + "\n", encoding="utf-8")

    d = CASE_DIR / "encrypted"
    src = d / "_epilogue.tmp"
    src.write_text(EPILOGUE_PLAIN, encoding="utf-8")
    subprocess.run(["openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2",
                    "-iter", "10000", "-a", "-in", str(src),
                    "-out", str(d / "epilogue.aes"), "-pass", "pass:" + CODENAME_BOSS],
                   check=True, capture_output=True)
    src.unlink()

    z = WITNESSES
    (CASE_DIR / "crimescene").write_text(CRIME_SCENE % {
        "z0": z[0]["nr"], "z0v": z[0]["first"], "z0n": z[0]["last"],
        "z1": z[1]["nr"], "z1v": z[1]["first"], "z1n": z[1]["last"],
        "z2": z[2]["nr"], "z2v": z[2]["first"], "z2n": z[2]["last"],
    }, encoding="utf-8")
    (GAME / "instructions").write_text(INSTRUCTIONS, encoding="utf-8")
    (GAME / "cheatsheet.md").write_text(CHEATSHEET, encoding="utf-8")
    (GAME / "solution").write_text(SOLUTION_TEXT, encoding="utf-8")
    (GAME / "README.md").write_text(README, encoding="utf-8")
    (GAME / "LICENSE.md").write_text(LICENSE, encoding="utf-8")
    for i, h in enumerate(HINTS, start=1):
        (GAME / f"hint{i}").write_text(h, encoding="utf-8")

    checker = (CHECKER_TEMPLATE
        .replace("@H_VICTIM@", sha(VICTIM_NAME, VICTIM_NAME.replace("é", "e")))
        .replace("@H_INSIDE@", sha(INSIDE_MAN))
        .replace("@H_CODE@", sha(CODENAME_BOSS))
        .replace("@H_MASTER@", sha(MASTERMIND, " ".join(MASTERMIND.split()[::-1])))
        .replace("@H_PLACE@", sha(DROP, DROP.replace("old ", ""),
                                  DROP + ", May 22, 23:00",
                                  DROP.replace("old ", "") + ", May 22, 23:00")))
    cp = GAME / "checker.sh"
    cp.write_text(checker, encoding="utf-8")
    os.chmod(cp, 0o755)

    acrostic = "".join(ln.strip()[0] for ln in LETTER_C.strip().splitlines() if ln.strip()).upper()
    meta = {
        "victim": VICTIM_NAME, "inside_man": INSIDE_MAN, "mastermind": MASTERMIND,
        "codename_mastermind": CODENAME_BOSS, "codename_inside": CODENAME_INSIDE,
        "badge_inside": BADGE_INSIDE, "drop": DROP,
        "elim_a": {"name": f"{ELIM_A[0]} {ELIM_A[1]}", "badge": ELIM_A[2], "terminal": ELIM_A[3]},
        "elim_b": {"name": f"{ELIM_B[0]} {ELIM_B[1]}", "badge": ELIM_B[2]},
        "witnesses": [w["nr"] for w in z],
        "hashes": {
            "victim_sha256": sha(VICTIM_NAME, VICTIM_NAME.replace("é", "e")).split(","),
            "inside_sha256": [sha(INSIDE_MAN)],
            "code_sha256": [sha(CODENAME_BOSS)],
            "master_sha256": sha(MASTERMIND, " ".join(MASTERMIND.split()[::-1])).split(","),
            "place_sha256": sha(DROP, DROP.replace("old ", ""),
                                DROP + ", May 22, 23:00",
                                DROP.replace("old ", "") + ", May 22, 23:00").split(","),
            "master_md5": md5hex(MASTERMIND),
        },
        "counts": {
            "people": len(PEOPLE),
            "library_club_size": CLUBS["Friends_of_the_Prison_Library"],
            "interviews": len(list((CASE_DIR / "interviews").iterdir())),
            "streets": len(STREETS),
        },
        "git": gitmeta,
        "verify": {
            "coinnote_rot13_sha256": hashlib.sha256(
                ("Coin pouch: 1 physical Monero pendant, engraved inside:\n"
                 "fish warehouse, Ramp 3. Never go there alone. - K.\n").encode()).hexdigest(),
            "acrostic": "SPHINX",
            "fingerprint_target_md5": FINGER_TARGET,
            "history_user_elim": ELIM_A[3],
            "history_logout": "21:24:40",
            "inside_entry": ts(h=20, mi=31),
            "inside_exit": ts(h=21, mi=33),
            "elim_b_last_exit": ts(h=19, mi=55),
            "shipment88_contains": "FISH WAREHOUSE",
            "team_txt_contains": BADGE_INSIDE,
            "dangling_contains": "LAPWING",
            "board_contains": "Holthaus,Regina,RH",
            "mail_contains": "fish warehouse",
        },
    }
    (Path(__file__).resolve().parent / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("OK generated:", GAME)
    print("Acrostic:", acrostic)
    print("Library club:", CLUBS["Friends_of_the_Prison_Library"])

if __name__ == "__main__":
    main()
