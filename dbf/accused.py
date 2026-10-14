import sqlite3
import csv
import re
import unicodedata
import tkinter as tk

from pathlib import Path
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
from difflib import SequenceMatcher

DB_PATH = Path(r"D:\PyZar\db\zear.db")
TABLE = "ctms4000"
REFERENCE_TABLE = "ctms4100"
PERSON_ID_COLUMN = "PERSONID"


def normalize(value):
    if value is None:
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.upper()
    value = re.sub(r"[^A-Z0-9 ]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def full_name(row):
    parts = [
        normalize(row.get("FNAME")),
        normalize(row.get("MNAME")),
        normalize(row.get("LNAME")),
    ]
    separate = " ".join(p for p in parts if p)
    if separate:
        return separate
    return normalize(row.get("ENAME")) or normalize(row.get("ANAME"))


def connect():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found:\n{DB_PATH}")

    con = sqlite3.connect(str(DB_PATH), timeout=30)
    con.row_factory = sqlite3.Row

    exists = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (TABLE,)
    ).fetchone()
    if not exists:
        con.close()
        raise RuntimeError(f"Table {TABLE} not found in {DB_PATH.name}")
    return con


def table_columns(con, table):
    return {
        row["name"].upper(): row["name"]
        for row in con.execute(f'PRAGMA table_info("{table}")')
    }


def get_records():
    con = connect()
    try:
        return [dict(row) for row in con.execute('SELECT * FROM "ctms4000"')]
    finally:
        con.close()


def compare_names(records, threshold):
    results = []
    for i, r1 in enumerate(records):
        n1 = full_name(r1)
        if not n1:
            continue

        for r2 in records[i + 1:]:
            n2 = full_name(r2)
            if not n2 or r1.get("PERSONID") == r2.get("PERSONID"):
                continue

            score = SequenceMatcher(None, n1, n2).ratio()
            if n1 == n2:
                match_type, score = "EXACT NAME", 1.0
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

    results.sort(key=lambda r: (
        r["Match"] != "EXACT NAME",
        -r["Similarity"],
        str(r["NAME_1"])
    ))
    return results


def create_database_backup():
    """Create a consistent SQLite backup before any merge is attempted."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_name(
        f"{DB_PATH.stem}_before_merge_{stamp}.db"
    )
    source = sqlite3.connect(str(DB_PATH), timeout=30)
    destination = sqlite3.connect(str(backup_path))
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    return backup_path


def merge_person(keep_id, delete_id):
    """Repoint ctms4100 references, then delete duplicate, atomically."""
    if str(keep_id) == str(delete_id):
        raise ValueError("The KEEP and DELETE PERSONID values must be different.")

    con = connect()
    try:
        cols4000 = table_columns(con, TABLE)
        cols4100 = table_columns(con, REFERENCE_TABLE)

        if PERSON_ID_COLUMN not in cols4000:
            raise RuntimeError(f"{TABLE} has no {PERSON_ID_COLUMN} column.")
        if PERSON_ID_COLUMN not in cols4100:
            raise RuntimeError(
                f"{REFERENCE_TABLE} has no {PERSON_ID_COLUMN} column. "
                "No changes were made."
            )

        id_col4000 = cols4000[PERSON_ID_COLUMN]
        id_col4100 = cols4100[PERSON_ID_COLUMN]

        keep_row = con.execute(
            f'SELECT "{id_col4000}" FROM "{TABLE}" WHERE "{id_col4000}"=?',
            (keep_id,)
        ).fetchone()
        delete_row = con.execute(
            f'SELECT "{id_col4000}" FROM "{TABLE}" WHERE "{id_col4000}"=?',
            (delete_id,)
        ).fetchone()

        if keep_row is None:
            raise RuntimeError(f"KEEP PERSONID {keep_id} was not found in {TABLE}.")
        if delete_row is None:
            raise RuntimeError(f"DELETE PERSONID {delete_id} was not found in {TABLE}.")

        # Back up the database before starting the write transaction.
        backup_path = create_database_backup()

        con.execute("BEGIN IMMEDIATE")
        reference_count = con.execute(
            f'SELECT COUNT(*) FROM "{REFERENCE_TABLE}" WHERE "{id_col4100}"=?',
            (delete_id,)
        ).fetchone()[0]

        con.execute(
            f'UPDATE "{REFERENCE_TABLE}" SET "{id_col4100}"=? '
            f'WHERE "{id_col4100}"=?',
            (keep_id, delete_id)
        )
        updated_count = con.execute("SELECT changes()").fetchone()[0]

        remaining = con.execute(
            f'SELECT COUNT(*) FROM "{REFERENCE_TABLE}" WHERE "{id_col4100}"=?',
            (delete_id,)
        ).fetchone()[0]
        if remaining:
            raise RuntimeError(
                f"{remaining} reference(s) still point to PERSONID {delete_id}; "
                "merge cancelled."
            )

        con.execute(
            f'DELETE FROM "{TABLE}" WHERE "{id_col4000}"=?',
            (delete_id,)
        )
        deleted_count = con.execute("SELECT changes()").fetchone()[0]
        if deleted_count != 1:
            raise RuntimeError(
                f"Expected to delete exactly one row from {TABLE}, "
                f"but deleted {deleted_count}. Merge cancelled."
            )

        con.commit()
        return backup_path, reference_count, updated_count
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Zear DB - Same Accused Name Checker")
        self.root.geometry("1450x750")
        self.results = []

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=f"Database: {DB_PATH}").pack(anchor="w")

        options = ttk.Frame(top)
        options.pack(fill="x", pady=8)

        ttk.Label(options, text="Similarity threshold (%):").pack(side="left")
        self.threshold = tk.StringVar(value="85")
        ttk.Entry(options, textvariable=self.threshold, width=8).pack(side="left", padx=6)

        ttk.Button(options, text="Check Names", command=self.run_check).pack(side="left", padx=6)
        ttk.Button(
            options, text="Merge Selected Accused", command=self.merge_selected
        ).pack(side="left", padx=6)
        ttk.Button(options, text="Export CSV", command=self.export_csv).pack(side="left", padx=6)

        ttk.Label(
            top,
            text=(
                "Select one comparison row, then click Merge Selected Accused. "
                "You will choose which PERSONID to keep. Similar names are suggestions only; "
                "verify birth date, address, and case records first."
            ),
            wraplength=1300
        ).pack(anchor="w")

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill="both", expand=True)

        self.columns = [
            "Match", "Similarity",
            "PERSONID_1", "NAME_1", "BIRTH_1", "ADDRESS_1",
            "PERSONID_2", "NAME_2", "BIRTH_2", "ADDRESS_2",
            "STATUS"
        ]
        self.tree = ttk.Treeview(
            frame, columns=self.columns, show="headings", selectmode="browse"
        )

        widths = {
            "Match": 110, "Similarity": 85,
            "PERSONID_1": 90, "NAME_1": 210, "BIRTH_1": 100, "ADDRESS_1": 180,
            "PERSONID_2": 90, "NAME_2": 210, "BIRTH_2": 100, "ADDRESS_2": 180,
            "STATUS": 100,
        }
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths.get(col, 120), anchor="w")

        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.status = ttk.Label(root, text="Ready.", padding=10)
        self.status.pack(fill="x")

    def run_check(self):
        try:
            threshold = float(self.threshold.get())
            if not 0 <= threshold <= 100:
                raise ValueError("Similarity must be between 0 and 100.")

            records = get_records()
            self.results = compare_names(records, threshold / 100)
            self.tree.delete(*self.tree.get_children())

            for result in self.results:
                self.tree.insert("", "end", values=[result[col] for col in self.columns])

            exact = sum(r["Match"] == "EXACT NAME" for r in self.results)
            similar = len(self.results) - exact
            self.status.config(
                text=f"Records scanned: {len(records)} | Exact-name pairs: {exact} | "
                     f"Similar-name pairs: {similar} | Total pairs: {len(self.results)}"
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def merge_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "Select a pair first",
                "Pumili muna ng isang row sa listahan ng posibleng duplicate."
            )
            return

        values = self.tree.item(selection[0], "values")
        try:
            id1, name1 = values[2], values[3]
            id2, name2 = values[6], values[7]

            choice = messagebox.askyesnocancel(
                "Choose which PERSONID to KEEP",
                f"PAIR SELECTED:\n\n"
                f"PERSONID {id1}\n{name1}\n\n"
                f"PERSONID {id2}\n{name2}\n\n"
                f"YES = KEEP PERSONID {id1} and delete {id2}\n"
                f"NO = KEEP PERSONID {id2} and delete {id1}\n"
                f"CANCEL = Do nothing\n\n"
                f"Check birth date, address, and case records before choosing."
            )
            if choice is None:
                return

            if choice:
                keep_id, keep_name = id1, name1
                delete_id, delete_name = id2, name2
            else:
                keep_id, keep_name = id2, name2
                delete_id, delete_name = id1, name1

            if not messagebox.askokcancel(
                "Final confirmation",
                f"KEEP:\nPERSONID {keep_id} — {keep_name}\n\n"
                f"DELETE:\nPERSONID {delete_id} — {delete_name}\n\n"
                f"The program will update references in {REFERENCE_TABLE}, "
                f"then delete PERSONID {delete_id} from {TABLE}.\n\n"
                f"A database backup will be created first.\n\nProceed?"
            ):
                return

            backup_path, reference_count, updated_count = merge_person(keep_id, delete_id)
            messagebox.showinfo(
                "Merge successful",
                f"Merge completed.\n\n"
                f"Kept PERSONID: {keep_id}\n"
                f"Deleted PERSONID: {delete_id}\n"
                f"References found in {REFERENCE_TABLE}: {reference_count}\n"
                f"References updated: {updated_count}\n\n"
                f"Backup created at:\n{backup_path}"
            )
            self.run_check()
        except Exception as e:
            messagebox.showerror(
                "Merge failed — no partial changes kept",
                f"{e}\n\nIf an error occurred during the transaction, changes were rolled back."
            )

    def export_csv(self):
        if not self.results:
            messagebox.showwarning("No results", "Click Check Names first.")
            return

        path = filedialog.asksaveasfilename(
            title="Save name comparison report",
            initialfile="zear_same_accused_report.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.results[0].keys()))
            writer.writeheader()
            writer.writerows(self.results)

        messagebox.showinfo("Export complete", f"Report saved:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
