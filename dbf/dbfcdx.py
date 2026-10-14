
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dbfread import DBF

FOLDER = r"C:\CTMS\dbf"
DBF_FILE = os.path.join(FOLDER, "ctms1000.DBF")
CDX_FILE = os.path.join(FOLDER, "ctms1000.CDX")
BAK_FILE = os.path.join(FOLDER, "ctms1000.BAK")


def file_info(path):
    if not os.path.isfile(path):
        return {
            "name": os.path.basename(path),
            "status": "NOT FOUND",
            "size": "",
            "modified": "",
        }

    stat = os.stat(path)
    return {
        "name": os.path.basename(path),
        "status": "FOUND",
        "size": f"{stat.st_size:,} bytes",
        "modified": datetime.fromtimestamp(
            stat.st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S"),
    }


class CTMSViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("CTMS1000 DBF / CDX / BAK Viewer")
        self.root.geometry("1250x720")

        self.records = []
        self.fields = []

        top = ttk.LabelFrame(root, text="CTMS1000 Files", padding=8)
        top.pack(fill="x", padx=10, pady=8)

        self.files_tree = ttk.Treeview(
            top,
            columns=("name", "status", "size", "modified"),
            show="headings",
            height=3,
        )

        for col, title, width in [
            ("name", "File", 220),
            ("status", "Status", 100),
            ("size", "Size", 140),
            ("modified", "Last Modified", 190),
        ]:
            self.files_tree.heading(col, text=title)
            self.files_tree.column(col, width=width)

        self.files_tree.pack(fill="x")

        actions = ttk.Frame(root)
        actions.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            actions, text="Refresh Files",
            command=self.refresh_files
        ).pack(side="left")

        ttk.Button(
            actions, text="Load DBF Records",
            command=self.load_dbf
        ).pack(side="left", padx=5)

        ttk.Button(
            actions, text="View DBF Fields",
            command=self.view_fields
        ).pack(side="left")

        ttk.Button(
            actions, text="Open Folder",
            command=self.open_folder
        ).pack(side="left", padx=5)

        search_frame = ttk.Frame(root)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Search records:").pack(side="left")

        self.search_var = tk.StringVar()
        search = ttk.Entry(
            search_frame, textvariable=self.search_var, width=40
        )
        search.pack(side="left", padx=5)
        search.bind("<KeyRelease>", lambda event: self.show_records())

        ttk.Button(
            search_frame, text="Clear",
            command=self.clear_search
        ).pack(side="left")

        self.count_label = ttk.Label(search_frame, text="Records: 0")
        self.count_label.pack(side="right")

        table_frame = ttk.Frame(root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=8)

        self.table = ttk.Treeview(table_frame, show="headings")
        ybar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.table.yview
        )
        xbar = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.table.xview
        )

        self.table.configure(
            yscrollcommand=ybar.set,
            xscrollcommand=xbar.set
        )

        self.table.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.refresh_files()
        self.load_dbf()

    def refresh_files(self):
        self.files_tree.delete(*self.files_tree.get_children())

        for path in (DBF_FILE, CDX_FILE, BAK_FILE):
            info = file_info(path)
            self.files_tree.insert(
                "", "end",
                values=(
                    info["name"],
                    info["status"],
                    info["size"],
                    info["modified"],
                ),
            )

    def load_dbf(self):
        if not os.path.isfile(DBF_FILE):
            messagebox.showerror(
                "Missing DBF", f"File not found:\n{DBF_FILE}"
            )
            return

        try:
            # Read-only access; walang writes sa DBF/CDX.
            dbf = DBF(
                DBF_FILE,
                load=False,
                char_decode_errors="replace",
            )

            self.fields = list(dbf.fields)
            self.records = []

            for row in dbf:
                self.records.append(dict(row))

            columns = list(dbf.field_names)
            self.table.delete(*self.table.get_children())
            self.table["columns"] = columns

            for col in columns:
                self.table.heading(col, text=col)
                self.table.column(
                    col, width=140, minwidth=75, stretch=True
                )

            self.show_records()
            self.refresh_files()

        except Exception as exc:
            messagebox.showerror(
                "DBF Read Error",
                f"Could not read DBF:\n\n{exc}\n\n"
                "Check whether CTMS is currently using the file."
            )

    def show_records(self):
        query = self.search_var.get().strip().casefold()
        self.table.delete(*self.table.get_children())

        columns = self.table["columns"]
        shown = 0

        for row in self.records:
            values = [row.get(col) for col in columns]

            if query:
                combined = " ".join(
                    "" if v is None else str(v) for v in values
                ).casefold()

                if query not in combined:
                    continue

            self.table.insert(
                "", "end",
                values=[
                    "" if value is None else str(value)
                    for value in values
                ],
            )
            shown += 1

        self.count_label.config(
            text=f"Showing {shown:,} / {len(self.records):,} records"
        )

    def clear_search(self):
        self.search_var.set("")
        self.show_records()

    def view_fields(self):
        if not self.fields:
            messagebox.showinfo("No fields", "Load the DBF first.")
            return

        window = tk.Toplevel(self.root)
        window.title("CTMS1000 Field Structure")
        window.geometry("650x500")

        tree = ttk.Treeview(
            window,
            columns=("name", "type", "length", "decimal"),
            show="headings",
        )

        for col, title, width in [
            ("name", "Field Name", 240),
            ("type", "Type", 100),
            ("length", "Length", 100),
            ("decimal", "Decimals", 100),
        ]:
            tree.heading(col, text=title)
            tree.column(col, width=width)

        tree.pack(fill="both", expand=True)

        for field in self.fields:
            tree.insert(
                "", "end",
                values=(
                    field.name,
                    field.type,
                    field.length,
                    getattr(field, "decimal_count", ""),
                ),
            )

    def open_folder(self):
        if os.path.isdir(FOLDER):
            os.startfile(FOLDER)
        else:
            messagebox.showerror(
                "Folder not found", FOLDER
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = CTMSViewer(root)
    root.mainloop()
