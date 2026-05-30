"""Generate face_map code block from face_map.csv + athletes.csv.
Usage: python gen_face_map.py
Outputs code ready to paste into ZMROBO-3.0.
"""

import csv, os

FACE_MAP_CSV = "face_map.csv"
ATHLETES_CSV = "athletes.csv"

# 项目 → 圈数
LAPS = {
    "800米": 3,
    "1000米": 4,
    "400米": 1,
    "1500米": 4,
}


def load_face_map(path):
    face_map = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                face_map[row["face_id"].strip()] = row["bib"].strip()
    return face_map


def load_athletes(path):
    athletes = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                bib = row["bib"].strip()
                athletes[bib] = {
                    "name": row["name"].strip(),
                    "project": row["project"].strip(),
                }
    return athletes


def main():
    face_map = load_face_map(FACE_MAP_CSV)
    athletes = load_athletes(ATHLETES_CSV)

    if not face_map:
        print("[ERROR] face_map.csv is empty. Run face_register.py first.")
        return
    if not athletes:
        print("[ERROR] athletes.csv not found.")
        return

    print("# ============================================================")
    print("# 复制以下代码粘贴到 ZMROBO-3.0 的 face_map 位置")
    print("# 共 {} 人".format(len(face_map)))
    print("# ============================================================")
    print("face_map = {")

    for face_id in sorted(face_map.keys(), key=int):
        bib = face_map[face_id]
        info = athletes.get(bib, {})
        name = info.get("name", "?")
        project = info.get("project", "800米")
        laps = LAPS.get(project, 3)

        print("    {}: ({}, \"{}\", {}),  # {}".format(
            face_id, bib, project, laps, name
        ))

    print("}")


if __name__ == "__main__":
    main()
