import csv
import sqlite3
import tkinter as tk

from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

DB_PATH = Path(r"D:\\PyZar\\db\\zear.db")
PERSON_ID_COLUMN = "PERSONID"
TABLE_MASTER = "ctms4000"
TABLE_REFERENCES = "ctms4100"


def connect():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found:\\n{DB_PATH}")

    con = sqlite3.connect(str(DB_PATH), timeout=30)
    con.row_factory = sqlite3.Row

    for table in (TABLE_MASTER, TABLE_REFERENCES):
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        ).fetchone()
        if not exists:
            con.close()
            raise RuntimeError(f"Table {table} was not found in {DB_PATH.name}.")

    return con


def get_columns(con, table):
    return {
        row["name"].upper(): row["name"]
        for row in con.execute(f'PRAGMA table_info("{table}")')
    }


def find_mismatches():
    """Compare distinct nonblank PERSONID values in both directions."""
    con = connect()
    try:
        cols4000 = get_columns(con, TABLE_MASTER)
        cols4100 = get_columns(con, TABLE_REFERENCES)

        for table, cols in ((TABLE_MASTER, cols4000), (TABLE_REFERENCES, cols4100)):
            if PERSON_ID_COLUMN not in cols:
                raise RuntimeError(f"{table} does not have a PERSONID column.")

        p4000 = cols4000[PERSON_ID_COLUMN]
        p4100 = cols4100[PERSON_ID_COLUMN]

        # Values are trimmed and cast to text so padding/type differences
        # do not create false mismatches.
        c4000 = f'TRIM(CAST(m."{p4000}" AS TEXT))'
        c4100 = f'TRIM(CAST(r."{p4100}" AS TEXT))'

        refs_only_sql = f'''
            SELECT
                {c4100} AS PERSONID,
                {("r." + chr(34) + cols4100["PARTYID"] + chr(34)) if "PARTYID" in cols4100 else "NULL"} AS PARTYID,
                {("r." + chr(34) + cols4100["CASEID"] + chr(34)) if "CASEID" in cols4100 else "NULL"} AS CASEID
            FROM "{TABLE_REFERENCES}" r
            WHERE {c4100} IS NOT NULL AND {c4100} <> ''
              AND NOT EXISTS (
                  SELECT 1 FROM "{TABLE_MASTER}" m
                  WHERE {c4000} = {c4100}
              )
            ORDER BY PERSONID, CASEID, PARTYID
        '''
        refs_only = [dict(row) for row in con.execute(refs_only_sql)]

        master_name_cols = [
            col for col in ("FNAME", "MNAME", "LNAME", "ENAME", "ANAME")
            if col in cols4000
        ]
        select_master = [f'm."{p4000}" AS PERSONID']
        for col in master_name_cols:
            select_master.append(f'm."{cols4000[col]}" AS "{col}"')

        master_only_sql = f'''
            SELECT {", ".join(select_master)}
            FROM "{TABLE_MASTER}" m
            WHERE {c4000} IS NOT NULL AND {c4000} <> ''
              AND NOT EXISTS (
                  SELECT 1 FROM "{TABLE_REFERENCES}" r
                  WHERE {c4100} = {c4000}
              )
            ORDER BY PERSONID
        '''
        master_only = [dict(row) for row in con.execute(master_only_sql)]

        return refs_only, master_only, len(master_name_cols)
    finally:
        con.close()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("CTMS PERSONID Mismatch Checker")
        self.root.geometry("1050x680")
        self.refs_only = []
        self.master_only = []
        self.master_name_cols = []

        header = ttk.Frame(root, padding=10)
        header.pack(fill="x")
        ttk.Label(header, text=f"Database: {DB_PATH}").pack(anchor="w")
        ttk.Label(
            header,
            text=(
                "Checks PERSONID values in both directions. "
                "This tool only reports differences; it does not modify either table."
            ),
            wraplength=1000
        ).pack(anchor="w", pady=(5, 8))

        controls = ttk.Frame(header)
        controls.pack(fill="x")
        ttk.Button(controls, text="Check Differences", command=self.run_check).pack(side="left")
        ttk.Button(controls, text="Export CSV", command=self.export_csv).pack(side="left", padx=8)

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.refs_tab = ttk.Frame(self.tabs, padding=8)
        self.master_tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(self.refs_tab, text="In ctms4100, NOT in ctms4000")
        self.tabs.add(self.master_tab, text="In ctms4000, NOT in ctms4100")

        self.refs_tree = self.make_tree(
            self.refs_tab,
            ("PERSONID", "PARTYID", "CASEID"),
            {"PERSONID": 180, "PARTYID": 180, "CASEID": 400}
        )
        self.master_tree = None

        self.status = ttk.Label(root, text="Click Check Differences to begin.", padding=10)
        self.status.pack(fill="x")

    @staticmethod
    def make_tree(parent, columns, widths):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 150), anchor="w")
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return tree

    def run_check(self):
        try:
            self.refs_only, self.master_only, _ = find_mismatches()
            self.refs_tree.delete(*self.refs_tree.get_children())
            for row in self.refs_only:
                self.refs_tree.insert(
                    "", "end",
                    values=(row.get("PERSONID"), row.get("PARTYID"), row.get("CASEID"))
                )

            if self.master_tree is not None:
                self.master_tree.destroy()

            self.master_name_cols = [
                col for col in ("FNAME", "MNAME", "LNAME", "ENAME", "ANAME")
                if any(col in row for row in self.master_only)
            ]
            master_columns = ("PERSONID", *self.master_name_cols)
            master_widths = {"PERSONID": 180, **{col: 200 for col in self.master_name_cols}}
            self.master_tree = self.make_tree(self.master_tab, master_columns, master_widths)

            for row in self.master_only:
                self.master_tree.insert(
                    "", "end",
                    values=tuple(row.get(col) for col in master_columns)
                )

            self.status.config(
                text=(
                    f"ctms4100 PERSONID not found in ctms4000: {len(self.refs_only)} row(s) | "
                    f"ctms4000 PERSONID not found in ctms4100: {len(self.master_only)} row(s)"
                )
            )
        except Exception as e:
            messagebox.showerror("Comparison failed", str(e))

    def export_csv(self):
        if not self.refs_only and not self.master_only:
            messagebox.showwarning("No results", "Click Check Differences first.")
            return

        default_name = f"ctms_personid_mismatch_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path = filedialog.asksaveasfilename(
            title="Export PERSONID mismatch report",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        fields = [
            "DIRECTION", "PERSONID", "PARTYID", "CASEID",
            "FNAME", "MNAME", "LNAME", "ENAME", "ANAME"
        ]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in self.refs_only:
                writer.writerow({"DIRECTION": "ctms4100 NOT in ctms4000", **row})
            for row in self.master_only:
                writer.writerow({"DIRECTION": "ctms4000 NOT in ctms4100", **row})

        messagebox.showinfo("Export complete", f"Report saved to:\\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
