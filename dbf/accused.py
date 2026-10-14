
import sqlite3
import csv
import re
import unicodedata
import tkinter as tk

from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from collections import defaultdict
from difflib import SequenceMatcher

DB_PATH = Path(r"D:\PyZar\forCompare\zear.db")
TABLE = "ctms4000"


def normalize(value):
    """Normalize names for comparison."""
    if value is None:
        return ""

    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )
    value = value.upper()
    value = re.sub(r"[^A-Z0-9 ]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def full_name(row):
    # Prefer separate name fields when available.
    parts = [
        normalize(row.get("FNAME")),
        normalize(row.get("MNAME")),
        normalize(row.get("LNAME")),
    ]

    separate = " ".join(p for p in parts if p)

    if separate:
        return separate

    # Fallback to ENAME or ANAME.
    return (
        normalize(row.get("ENAME"))
        or normalize(row.get("ANAME"))
    )


def connect():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    exists = con.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type='table' AND name=?",
        (TABLE,)
    ).fetchone()

    if not exists:
        con.close()
        raise RuntimeError(
            f"Table {TABLE} not found in {DB_PATH.name}"
        )

    return con


def get_records():
    con = connect()

    try:
        records = [
            dict(row)
            for row in con.execute(
                'SELECT * FROM "ctms4000"'
            )
        ]
    finally:
        con.close()

    return records


def compare_names(records, threshold):
    """
    Find pairs with the same or similar names.
    Each PERSONID remains visible for manual verification.
    """
    results = []

    for i in range(len(records)):
        r1 = records[i]
        n1 = full_name(r1)

        if not n1:
            continue

        for j in range(i + 1, len(records)):
            r2 = records[j]
            n2 = full_name(r2)

            if not n2:
                continue

            if r1.get("PERSONID") == r2.get("PERSONID"):
                continue

            score = SequenceMatcher(
                None, n1, n2
            ).ratio()

            if n1 == n2:
                match_type = "EXACT NAME"
                score = 1.0
            elif score >= threshold:
                match_type = "SIMILAR NAME"
            else:
                continue

            results.append({
                "Match": match_type,
                "Similarity": round(score * 100, 1),
                "PERSONID_1": r1.get("PERSONID"),
                "NAME_1": n1,
                "BIRTH_1": r1.get("DBIRTH"),
                "ADDRESS_1": r1.get("ADDRESS1"),
                "PERSONID_2": r2.get("PERSONID"),
                "NAME_2": n2,
                "BIRTH_2": r2.get("DBIRTH"),
                "ADDRESS_2": r2.get("ADDRESS1"),
                "STATUS": "FOR REVIEW",
            })

    results.sort(
        key=lambda r: (
            r["Match"] != "EXACT NAME",
            -r["Similarity"],
            str(r["NAME_1"])
        )
    )

    return results


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(
            "Zear DB - Same Accused Name Checker"
        )
        self.root.geometry("1450x750")

        self.results = []

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Label(
            top,
            text=f"Database: {DB_PATH}"
        ).pack(anchor="w")

        options = ttk.Frame(top)
        options.pack(fill="x", pady=8)

        ttk.Label(
            options,
            text="Similarity threshold (%):"
        ).pack(side="left")

        self.threshold = tk.StringVar(value="85")

        ttk.Entry(
            options,
            textvariable=self.threshold,
            width=8
        ).pack(side="left", padx=6)

        ttk.Button(
            options,
            text="Check Names",
            command=self.run_check
        ).pack(side="left", padx=6)

        ttk.Button(
            options,
            text="Export CSV",
            command=self.export_csv
        ).pack(side="left", padx=6)

        ttk.Label(
            top,
            text=(
                "Exact matches and similar names are suggestions only. "
                "Verify birth date, address, and case records before "
                "treating two entries as the same person."
            ),
            wraplength=1300
        ).pack(anchor="w")

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill="both", expand=True)

        columns = [
            "Match", "Similarity",
            "PERSONID_1", "NAME_1", "BIRTH_1", "ADDRESS_1",
            "PERSONID_2", "NAME_2", "BIRTH_2", "ADDRESS_2",
            "STATUS"
        ]

        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings"
        )

        widths = {
            "Match": 110,
            "Similarity": 85,
            "PERSONID_1": 90,
            "NAME_1": 210,
            "BIRTH_1": 100,
            "ADDRESS_1": 180,
            "PERSONID_2": 90,
            "NAME_2": 210,
            "BIRTH_2": 100,
            "ADDRESS_2": 180,
            "STATUS": 100,
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(
                col,
                width=widths.get(col, 120),
                anchor="w"
            )

        yscroll = ttk.Scrollbar(
            frame, orient="vertical",
            command=self.tree.yview
        )
        xscroll = ttk.Scrollbar(
            frame, orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.status = ttk.Label(
            root, text="Ready.", padding=10
        )
        self.status.pack(fill="x")

    def run_check(self):
        try:
            threshold = float(self.threshold.get())

            if not 0 <= threshold <= 100:
                raise ValueError(
                    "Similarity must be between 0 and 100."
                )

            records = get_records()

            self.results = compare_names(
                records, threshold / 100
            )

            self.tree.delete(
                *self.tree.get_children()
            )

            for result in self.results:
                self.tree.insert(
                    "", "end",
                    values=[
                        result["Match"],
                        result["Similarity"],
                        result["PERSONID_1"],
                        result["NAME_1"],
                        result["BIRTH_1"],
                        result["ADDRESS_1"],
                        result["PERSONID_2"],
                        result["NAME_2"],
                        result["BIRTH_2"],
                        result["ADDRESS_2"],
                        result["STATUS"],
                    ]
                )

            exact = sum(
                r["Match"] == "EXACT NAME"
                for r in self.results
            )

            similar = len(self.results) - exact

            self.status.config(
                text=(
                    f"Records scanned: {len(records)} | "
                    f"Exact-name pairs: {exact} | "
                    f"Similar-name pairs: {similar} | "
                    f"Total pairs: {len(self.results)}"
                )
            )

        except Exception as e:
            messagebox.showerror(
                "Error", str(e)
            )

    def export_csv(self):
        if not self.results:
            messagebox.showwarning(
                "No results",
                "Click Check Names first."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save name comparison report",
            initialfile="zear_same_accused_report.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        with open(
            path, "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=list(self.results[0].keys())
            )
            writer.writeheader()
            writer.writerows(self.results)

        messagebox.showinfo(
            "Export complete",
            f"Report saved:\n{path}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
