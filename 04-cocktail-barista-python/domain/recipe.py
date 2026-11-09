"""Recipes loaded from the bar's Excel workbook (`data/recipes.xlsx`).

The workbook is the manager's recipe sheet: one row per pour, with the drink name repeated.
The reader uses only the standard library (``zipfile`` + XML), so the backend does not need
``openpyxl`` at run time. Edit the workbook and restart the backend to change the menu.
"""

from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

DATA = Path(__file__).resolve().parent.parent / "data" / "recipes.xlsx"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


@dataclass(frozen=True)
class Pour:
    valve: str
    millilitres: float
    seconds: float


@dataclass(frozen=True)
class Recipe:
    name: str
    pours: tuple[Pour, ...]
    shake_seconds: float
    garnish: str

    def total_ml(self) -> float:
        return sum(pour.millilitres for pour in self.pours)


def _column(ref: str) -> int:
    """The zero-based column of an A1 cell reference."""
    letters = re.match(r"[A-Z]+", ref)
    value = 0
    for letter in letters.group(0) if letters else "":
        value = value * 26 + (ord(letter) - ord("A") + 1)
    return value - 1


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.iter(f"{{{NS['m']}}}t"))
        for item in root.findall("m:si", NS)
    ]


def _rows(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        shared = _shared_strings(archive)
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in root.findall(".//m:sheetData/m:row", NS):
            cells: dict[int, str] = {}
            for cell in row.findall("m:c", NS):
                column = _column(cell.get("r", ""))
                kind = cell.get("t")
                value = cell.find("m:v", NS)
                if kind == "inlineStr":
                    text = "".join(node.text or "" for node in cell.iter(f"{{{NS['m']}}}t"))
                elif value is None:
                    text = ""
                elif kind == "s":
                    text = shared[int(value.text)]
                else:
                    text = value.text or ""
                cells[column] = text
            if cells:
                rows.append([cells.get(index, "") for index in range(max(cells) + 1)])
    return rows


def load(path: Path = DATA) -> list[Recipe]:
    """Read the workbook into recipes, in sheet order."""
    rows = _rows(path)
    if not rows:
        return []
    header = [text.strip().lower() for text in rows[0]]

    def at(row: list[str], name: str, fallback: float = 0.0) -> str:
        try:
            return row[header.index(name)]
        except (ValueError, IndexError):
            return str(fallback)

    grouped: dict[str, dict] = {}
    for row in rows[1:]:
        name = at(row, "drink").strip()
        if not name:
            continue
        entry = grouped.setdefault(name, {"pours": [], "shake": 1.0, "garnish": ""})
        valve = at(row, "valve").strip()
        if valve:
            entry["pours"].append(
                Pour(valve, float(at(row, "ml", 0) or 0), max(0.1, float(at(row, "seconds", 1) or 1)))
            )
        entry["shake"] = max(0.0, float(at(row, "shakeseconds", entry["shake"]) or 0))
        entry["garnish"] = at(row, "garnish", entry["garnish"]).strip()
    return [
        Recipe(name=name, pours=tuple(entry["pours"]), shake_seconds=entry["shake"], garnish=entry["garnish"])
        for name, entry in grouped.items()
        if entry["pours"]
    ]


RECIPES = load()
if not RECIPES:  # keep the backend importable if the workbook is missing
    RECIPES = [Recipe("Negroni", (Pour("gin", 30, 1), Pour("vermouth", 30, 1), Pour("campari", 30, 1)), 1.5, "orange peel")]
BY_NAME = {recipe.name.lower(): recipe for recipe in RECIPES}
NEGRONI = RECIPES[0]
