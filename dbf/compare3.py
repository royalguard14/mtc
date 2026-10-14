
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from collections import defaultdict
import shutil
import json
import os
import re
import unicodedata

FOLDER = Path(r"D:\PyZar\forCompare")
DB1_DEFAULT = FOLDER / "combined.db"
DB2_DEFAULT = FOLDER / "zear.db"

TABLES = ["ctms1000", "ctms4000", "ctms4100"]


def q(name):
    return '"' + name.replace('"', '""') + '"'


def norm(value):
    if value is None:
        return ""
    value = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", " ", value).strip().casefold()


def conn(path):
    c = sqlite3.connect(str(path))
    c.row_factory = sqlite3.Row
    return c


def table_exists(c, table):
    return c.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone() is not None


def columns(c, table):
    return [
        r["name"]
        for r in c.execute(f"PRAGMA table_info({q(table)})")
    ]


def rows(c, table):
    return [
        dict(r)
        for r in c.execute(f"SELECT * FROM {q(table)}")
    ]


def case_map(c):
    if not table_exists(c, "ctms1000"):
        return {}

    result = {}
    for r in rows(c, "ctms1000"):
        casenum = norm(r.get("CASENUM"))
        if casenum:
            result[r.get("CASEID")] = casenum
    return result


def person_signature(r):
    # PERSONID is intentionally not used as the match key.
    fname = norm(r.get("FNAME"))
    lname = norm(r.get("LNAME"))
    mname = norm(r.get("MNAME"))
    birth = norm(r.get("DBIRTH"))

    if fname or lname:
        return ("NAME", fname, lname, mname, birth)

    ename = norm(r.get("ENAME"))
    if ename:
        return ("ENAME", ename, birth)

    return ("UNMATCHABLE", norm(r.get("PERSONID")))


def person_maps(c):
    if not table_exists(c, "ctms4000"):
        return {}, {}

    by_id = {}
    by_sig = defaultdict(list)

    for r in rows(c, "ctms4000"):
        pid = r.get("PERSONID")
        sig = person_signature(r)
        by_id[pid] = sig
        by_sig[sig].append(r)

    return by_id, by_sig


def make_index(c, table):
    data = rows(c, table)
    case_ids = case_map(c)
    person_ids, _ = person_maps(c)

    index = defaultdict(list)

    for r in data:
        if table == "ctms1000":
            key = ("CASE", norm(r.get("CASENUM")))

        elif table == "ctms4000":
            key = person_signature(r)

        else:
            casenum = case_ids.get(r.get("CASEID"), "")
            person_sig = person_ids.get(
                r.get("PERSONID"), ("UNKNOWN_PERSON",)
            )

            # PARTYID and CASEID alone are not used as the match key.
            key = (
                "PARTY",
                casenum,
                norm(r.get("PARTYNAME")),
                person_sig
            )

        index[key].append(r)

    return index


def value_text(value):
    if value is None:
        return "<NULL>"
    if isinstance(value, bytes):
        return "BLOB:" + value.hex()
    return str(value)


class CompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CTMS Database Compare & Merge")
        self.root.geometry("1350x760")

        self.db1 = str(DB1_DEFAULT)
        self.db2 = str(DB2_DEFAULT)

        self.data = []
        self.position = 0
        self.decisions = {}
        self.current = None

        self.top = ttk.Frame(root, padding=8)
        self.top.pack(fill="x")

        ttk.Label(
            self.top, text="DB1 (starting database):"
        ).grid(row=0, column=0, sticky="w")

        self.db1_label = ttk.Label(
            self.top, text=self.db1, width=65
        )
        self.db1_label.grid(row=0, column=1, sticky="w")

        ttk.Button(
            self.top, text="Browse DB1",
            command=lambda: self.pick_db(1)
        ).grid(row=0, column=2, padx=5)

        ttk.Label(
            self.top, text="DB2 (reference database):"
        ).grid(row=1, column=0, sticky="w")

        self.db2_label = ttk.Label(
            self.top, text=self.db2, width=65
        )
        self.db2_label.grid(row=1, column=1, sticky="w")

        ttk.Button(
            self.top, text="Browse DB2",
            command=lambda: self.pick_db(2)
        ).grid(row=1, column=2, padx=5)

        ttk.Button(
            self.top, text="Compare Tables",
            command=self.compare
        ).grid(row=0, column=3, rowspan=2, padx=12)

        self.status = ttk.Label(
            root, text="Select databases, then click Compare Tables.",
            padding=8
        )
        self.status.pack(fill="x")

        self.table_list = ttk.Frame(root, padding=(8, 0))
        self.table_list.pack(fill="x")

        ttk.Label(
            self.table_list, text="Select table:"
        ).pack(side="left")

        self.table_var = tk.StringVar(value="ctms1000")

        self.table_select = ttk.Combobox(
            self.table_list,
            textvariable=self.table_var,
            values=TABLES,
            state="readonly",
            width=16
        )
        self.table_select.pack(side="left", padx=8)
        self.table_select.bind(
            "<<ComboboxSelected>>",
            lambda e: self.show_current()
        )

        self.tree = ttk.Treeview(
            root,
            columns=(
                "Column", "DB1 Value", "DB2 Value", "Decision"
            ),
            show="headings",
            height=17
        )

        for col, width in [
            ("Column", 180),
            ("DB1 Value", 400),
            ("DB2 Value", 400),
            ("Decision", 150)
        ]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree.bind(
            "<Double-1>", self.edit_cell
        )

        self.controls = ttk.Frame(root, padding=8)
        self.controls.pack(fill="x")

        ttk.Button(
            self.controls, text="Use DB1 for this record",
            command=lambda: self.choose_record("DB1")
        ).pack(side="left", padx=4)

        ttk.Button(
            self.controls, text="Use DB2 for this record",
            command=lambda: self.choose_record("DB2")
        ).pack(side="left", padx=4)

        ttk.Button(
            self.controls, text="Skip this record",
            command=lambda: self.choose_record("SKIP")
        ).pack(side="left", padx=4)

        ttk.Button(
            self.controls, text="Previous",
            command=lambda: self.move(-1)
        ).pack(side="left", padx=20)

        ttk.Button(
            self.controls, text="Next",
            command=lambda: self.move(1)
        ).pack(side="left", padx=4)

        ttk.Button(
            self.controls, text="Save NEW .db",
            command=self.save_output
        ).pack(side="right", padx=4)

    def pick_db(self, which):
        path = filedialog.askopenfilename(
            title="Select SQLite database",
            filetypes=[
                ("SQLite databases", "*.db *.sqlite *.sqlite3"),
                ("All files", "*.*")
            ]
        )
        if not path:
            return

        if which == 1:
            self.db1 = path
            self.db1_label.config(text=path)
        else:
            self.db2 = path
            self.db2_label.config(text=path)

    def compare(self):
        if not os.path.isfile(self.db1) or not os.path.isfile(self.db2):
            messagebox.showerror(
                "Missing file", "Check both database paths."
            )
            return

        if os.path.abspath(self.db1) == os.path.abspath(self.db2):
            messagebox.showerror(
                "Invalid selection",
                "Select two different database files."
            )
            return

        self.data = []
        self.decisions = {}
        self.position = 0

        a = conn(self.db1)
        b = conn(self.db2)

        try:
            for table in TABLES:
                if not table_exists(a, table) or not table_exists(b, table):
                    self.data.append({
                        "table": table,
                        "key": ("TABLE_MISSING", table),
                        "status": "TABLE MISSING",
                        "row1": None,
                        "row2": None,
                        "columns": [],
                        "ambiguous": False
                    })
                    continue

                idx1 = make_index(a, table)
                idx2 = make_index(b, table)

                all_keys = sorted(
                    set(idx1) | set(idx2),
                    key=str
                )

                cols1 = columns(a, table)
                cols2 = columns(b, table)
                common = [x for x in cols1 if x in cols2]

                for key in all_keys:
                    left = idx1.get(key, [])
                    right = idx2.get(key, [])

                    if len(left) > 1 or len(right) > 1:
                        self.data.append({
                            "table": table,
                            "key": key,
                            "status": "AMBIGUOUS MATCH",
                            "row1": left[0] if left else None,
                            "row2": right[0] if right else None,
                            "columns": common,
                            "ambiguous": True
                        })
                        continue

                    r1 = left[0] if left else None
                    r2 = right[0] if right else None

                    if r1 is None:
                        status = "ONLY IN DB2"
                    elif r2 is None:
                        status = "ONLY IN DB1"
                    elif any(r1.get(c) != r2.get(c) for c in common):
                        status = "VALUES DIFFER"
                    else:
                        status = "SAME"

                    self.data.append({
                        "table": table,
                        "key": key,
                        "status": status,
                        "row1": r1,
                        "row2": r2,
                        "columns": common,
                        "ambiguous": False
                    })

            self.status.config(
                text=f"Comparison finished. {len(self.data)} comparison items. "
                     "SAME items default to DB1."
            )
            self.show_current()

        except Exception as e:
            messagebox.showerror("Comparison error", str(e))
        finally:
            a.close()
            b.close()

    def filtered_items(self):
        table = self.table_var.get()
        return [
            (i, item) for i, item in enumerate(self.data)
            if item["table"] == table
        ]

    def show_current(self):
        self.tree.delete(*self.tree.get_children())

        items = self.filtered_items()

        if not items:
            self.status.config(
                text=f"No comparison items for {self.table_var.get()}."
            )
            return

        # Keep position within selected table.
        self.position = max(0, min(self.position, len(items) - 1))
        global_index, item = items[self.position]
        self.current = global_index

        key_text = json.dumps(item["key"], ensure_ascii=False, default=str)
        choice = self.decisions.get(global_index, "AUTO")

        self.status.config(
            text=(
                f"{item['table']} | {item['status']} | "
                f"Key: {key_text} | "
                f"Item {self.position + 1}/{len(items)} | "
                f"Decision: {choice}"
            )
        )

        r1 = item["row1"]
        r2 = item["row2"]

        cols = list(dict.fromkeys(
            list(r1.keys() if r1 else []) +
            list(r2.keys() if r2 else [])
        ))

        if not cols:
            cols = ["Table"]

        for col in cols:
            v1 = r1.get(col) if r1 else "<NO ROW>"
            v2 = r2.get(col) if r2 else "<NO ROW>"

            self.tree.insert(
                "", "end",
                values=(
                    col,
                    value_text(v1),
                    value_text(v2),
                    self.decisions.get(
                        (global_index, col), choice
                    )
                )
            )

    def edit_cell(self, event):
        if self.current is None:
            return

        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        col = values[0]

        item = self.data[self.current]

        if item["status"] == "SAME":
            messagebox.showinfo(
                "Same record",
                "Walang difference sa record na ito."
            )
            return

        if item["ambiguous"]:
            messagebox.showwarning(
                "Ambiguous match",
                "May duplicate matching keys. Review the records manually."
            )
            return

        choice = simpledialog.askstring(
            "Choose value",
            f"Table: {item['table']}\n"
            f"Column: {col}\n\n"
            f"1 = use DB1 value\n"
            f"2 = use DB2 value\n"
            f"3 = enter your own value\n"
            f"4 = skip this record\n\n"
            f"DB1: {values[1]}\n"
            f"DB2: {values[2]}\n\n"
            "Enter 1, 2, 3 or 4:"
        )

        if choice == "1":
            self.decisions[(self.current, col)] = "DB1"
        elif choice == "2":
            self.decisions[(self.current, col)] = "DB2"
        elif choice == "3":
            current_value = values[1]
            new_value = simpledialog.askstring(
                "Manual value",
                f"Enter new value for {col}:",
                initialvalue=current_value
            )
            if new_value is not None:
                self.decisions[(self.current, col)] = ("EDIT", new_value)
        elif choice == "4":
            self.decisions[self.current] = "SKIP"

        self.show_current()

    def choose_record(self, choice):
        if self.current is None:
            return

        item = self.data[self.current]

        if item["ambiguous"]:
            messagebox.showwarning(
                "Ambiguous",
                "Duplicate keys need manual review before selection."
            )
            return

        self.decisions[self.current] = choice
        self.show_current()

    def move(self, step):
        items = self.filtered_items()
        if not items:
            return

        self.position = max(
            0, min(self.position + step, len(items) - 1)
        )
        self.show_current()

    def save_output(self):
        if not self.data:
            messagebox.showwarning(
                "No comparison",
                "Click Compare Tables first."
            )
            return

        output = filedialog.asksaveasfilename(
            title="Save merged database",
            defaultextension=".db",
            initialfile="CTMS_MERGED.db",
            filetypes=[("SQLite database", "*.db")]
        )

        if not output:
            return

        if os.path.abspath(output) in (
            os.path.abspath(self.db1),
            os.path.abspath(self.db2)
        ):
            messagebox.showerror(
                "Invalid output",
                "Do not overwrite either original database."
            )
            return

        # Do not silently write ambiguous or unresolved differences.
        unresolved = []
        for i, item in enumerate(self.data):
            if item["status"] in (
                "VALUES DIFFER", "ONLY IN DB1", "ONLY IN DB2",
                "AMBIGUOUS MATCH", "TABLE MISSING"
            ):
                if i not in self.decisions:
                    unresolved.append(item)

        if unresolved:
            proceed = messagebox.askyesno(
                "Unresolved items",
                f"{len(unresolved)} comparison items have no record-level "
                "decision. Continue using DB1 for unresolved items?\n\n"
                "Click No to return and review them."
            )
            if not proceed:
                return

        try:
            shutil.copy2(self.db1, output)
            out = conn(output)
            a = conn(self.db1)
            b = conn(self.db2)

            try:
                for table in TABLES:
                    if not table_exists(out, table):
                        continue

                    out_cols = columns(out, table)
                    items = [
                        (i, item)
                        for i, item in enumerate(self.data)
                        if item["table"] == table
                    ]

                    for global_i, item in items:
                        r1, r2 = item["row1"], item["row2"]
                        choice = self.decisions.get(global_i, "AUTO")

                        if choice == "SKIP":
                            continue

                        if choice == "DB2" and r2 is not None:
                            chosen = dict(r2)
                        elif r1 is not None:
                            chosen = dict(r1)
                        elif r2 is not None:
                            chosen = dict(r2)
                        else:
                            continue

                        # Existing matched case: preserve DB1 CASEID so
                        # linked records keep pointing to the same case.
                        if table == "ctms1000" and r1 and r2:
                            chosen["CASEID"] = r1.get("CASEID")

                        # Existing person: preserve DB1 PERSONID.
                        if table == "ctms4000" and r1 and r2:
                            chosen["PERSONID"] = r1.get("PERSONID")

                        # Existing party: preserve DB1 PARTYID/CASEID and
                        # map the person back to DB1 where possible.
                        if table == "ctms4100" and r1 and r2:
                            chosen["PARTYID"] = r1.get("PARTYID")
                            chosen["CASEID"] = r1.get("CASEID")
                            chosen["PERSONID"] = r1.get("PERSONID")

                        # Apply per-field decisions for matched rows.
                        if r1 is not None and r2 is not None:
                            for col in out_cols:
                                decision = self.decisions.get(
                                    (global_i, col), "AUTO"
                                )

                                if decision == "DB2" and col in r2:
                                    chosen[col] = r2[col]
                                elif (
                                    isinstance(decision, tuple)
                                    and decision[0] == "EDIT"
                                ):
                                    chosen[col] = decision[1]

                        key_cols = {
                            "ctms1000": ["CASENUM"],
                            "ctms4000": [
                                "FNAME", "LNAME", "MNAME", "DBIRTH"
                            ],
                            "ctms4100": [
                                "CASEID", "PARTYNAME", "PERSONID"
                            ],
                        }[table]

                        # Update existing row by its DB1 identity where possible.
                        if r1 is not None:
                            where_cols = (
                                ["CASENUM"] if table == "ctms1000"
                                else (
                                    ["PERSONID"] if table == "ctms4000"
                                    else ["PARTYID"]
                                )
                            )

                            where = " AND ".join(
                                f"{q(c)} IS ?" for c in where_cols
                            )

                            assignments = [
                                c for c in out_cols
                                if c in chosen and c not in where_cols
                            ]

                            if assignments:
                                sql = (
                                    f"UPDATE {q(table)} SET "
                                    + ", ".join(
                                        f"{q(c)}=?" for c in assignments
                                    )
                                    + f" WHERE {where}"
                                )

                                out.execute(
                                    sql,
                                    [chosen[c] for c in assignments]
                                    + [r1.get(c) for c in where_cols]
                                )

                        elif r2 is not None:
                            # For rows only in DB2, preserve the DB1 schema.
                            # Avoid inserting if any required mapping is uncertain.
                            if table == "ctms1000":
                                addrow = dict(chosen)
                                existing_ids = [
                                    x[0] for x in out.execute(
                                        "SELECT CASEID FROM ctms1000"
                                    )
                                ]
                                next_id = max(
                                    [x for x in existing_ids if isinstance(x, int)]
                                    or [0]
                                ) + 1
                                addrow["CASEID"] = next_id
                            else:
                                addrow = dict(chosen)

                            usable = [
                                c for c in out_cols if c in addrow
                            ]
                            sql = (
                                f"INSERT INTO {q(table)} "
                                f"({', '.join(q(c) for c in usable)}) "
                                f"VALUES ({', '.join('?' for c in usable)})"
                            )
                            out.execute(
                                sql, [addrow[c] for c in usable]
                            )

                out.commit()

            finally:
                out.close()
                a.close()
                b.close()

            messagebox.showinfo(
                "Saved",
                f"New database saved:\n{output}\n\n"
                "The original databases were not modified.\n"
                "Please validate linked CASEID/PERSONID references "
                "before using the output in CTMS."
            )

        except Exception as e:
            messagebox.showerror(
                "Save error",
                f"Could not create the merged database:\n\n{e}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = CompareApp(root)
    root.mainloop()
