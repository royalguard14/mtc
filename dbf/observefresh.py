
import os
import tkinter as tk
from tkinter import ttk, messagebox
from dbfread import DBF

DBF_FOLDER = r"C:\CTMS\dbf"

TABLE_FILES = {
    "ctms1000": os.path.join(DBF_FOLDER, "ctms1000.DBF"),
    "ctms4000": os.path.join(DBF_FOLDER, "ctms4000.DBF"),
    "ctms4100": os.path.join(DBF_FOLDER, "ctms4100.DBF"),
}


class CTMSDBFReader:
    def __init__(self, root):
        self.root = root
        self.root.title("CTMS DBF Reader")
        self.root.geometry("1250x720")

        self.current_records = []
        self.current_columns = []
        self.current_fields = []

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Select DBF Table:").pack(side="left")

        self.table_var = tk.StringVar(value="ctms1000")

        self.table_select = ttk.Combobox(
            top,
            textvariable=self.table_var,
            values=list(TABLE_FILES.keys()),
            state="readonly",
            width=18,
        )
        self.table_select.pack(side="left", padx=8)
        self.table_select.bind(
            "<<ComboboxSelected>>",
            lambda event: self.load_table()
        )

        ttk.Button(
            top, text="Load Table",
            command=self.load_table
        ).pack(side="left")

        ttk.Button(
            top, text="View Fields",
            command=self.view_fields
        ).pack(side="left", padx=5)

        search_frame = ttk.Frame(root, padding=(10, 0, 10, 8))
        search_frame.pack(fill="x")

        ttk.Label(search_frame, text="Search:").pack(side="left")

        self.search_var = tk.StringVar()
        search = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=45,
        )
        search.pack(side="left", padx=6)
        search.bind(
            "<KeyRelease>",
            lambda event: self.show_records()
        )

        ttk.Button(
            search_frame, text="Clear",
            command=self.clear_search
        ).pack(side="left")

        self.status = ttk.Label(
            search_frame, text="No table loaded"
        )
        self.status.pack(side="right")

        table_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, show="headings")

        yscroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        xscroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.load_table()

    def load_table(self):
        table_name = self.table_var.get()
        path = TABLE_FILES[table_name]

        if not os.path.isfile(path):
            messagebox.showerror(
                "File Not Found",
                f"Hindi makita ang file:\n{path}"
            )
            return

        try:
            # Read-only DBF access.
            dbf = DBF(
                path,
                load=False,
                char_decode_errors="replace",
            )

            self.current_columns = list(dbf.field_names)
            self.current_fields = list(dbf.fields)
            self.current_records = []

            for record in dbf:
                self.current_records.append(dict(record))

            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = self.current_columns

            for col in self.current_columns:
                self.tree.heading(col, text=col)
                self.tree.column(
                    col,
                    width=140,
                    minwidth=75,
                    stretch=True,
                )

            self.search_var.set("")
            self.show_records()

        except Exception as exc:
            messagebox.showerror(
                "DBF Read Error",
                f"Hindi mabasa ang {table_name}:\n\n{exc}"
            )

    def show_records(self):
        self.tree.delete(*self.tree.get_children())

        query = self.search_var.get().strip().casefold()
        shown = 0

        for record in self.current_records:
            values = [
                record.get(col)
                for col in self.current_columns
            ]

            if query:
                searchable = " ".join(
                    "" if value is None else str(value)
                    for value in values
                ).casefold()

                if query not in searchable:
                    continue

            self.tree.insert(
                "",
                "end",
                values=[
                    "" if value is None else str(value)
                    for value in values
                ],
            )
            shown += 1

        self.status.config(
            text=(
                f"Showing {shown:,} of "
                f"{len(self.current_records):,} records"
            )
        )

    def clear_search(self):
        self.search_var.set("")
        self.show_records()

    def view_fields(self):
        if not self.current_fields:
            messagebox.showinfo(
                "No Fields", "Mag-load muna ng DBF table."
            )
            return

        window = tk.Toplevel(self.root)
        window.title(
            f"{self.table_var.get()} - Field Structure"
        )
        window.geometry("700x500")

        columns = ("name", "type", "length", "decimals")
        fields_tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings",
        )

        headings = {
            "name": ("Field Name", 240),
            "type": ("Type", 100),
            "length": ("Length", 100),
            "decimals": ("Decimals", 100),
        }

        for col, (heading, width) in headings.items():
            fields_tree.heading(col, text=heading)
            fields_tree.column(col, width=width)

        fields_tree.pack(fill="both", expand=True)

        for field in self.current_fields:
            fields_tree.insert(
                "",
                "end",
                values=(
                    field.name,
                    field.type,
                    field.length,
                    getattr(field, "decimal_count", ""),
                ),
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = CTMSDBFReader(root)
    root.mainloop()
