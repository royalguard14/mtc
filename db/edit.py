
import tkinter as tk
from tkinter import ttk, messagebox
import dbf
from datetime import datetime

# =========================
# CONFIG
# =========================
dbf_path = r"C:\CTMS\dbf\ctms4000.DBF"

# =========================
# LOAD DBF
# =========================
table = dbf.Table(dbf_path)
table.open(dbf.READ_WRITE)

fields = table.field_names
records = list(table)

# =========================
# GET FIELD TYPES (FIXED)
# =========================
field_types = {}

for field_def in table.structure():
    parts = field_def.split()
    name = parts[0]
    type_char = parts[1][0]  # C, N, D, T, etc.
    field_types[name] = type_char

# =========================
# GUI
# =========================
root = tk.Tk()
root.title("DBF Editor")

tree = ttk.Treeview(root, columns=fields, show="headings")

scroll_y = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scroll_y.set)

tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

# Columns
for field in fields:
    tree.heading(field, text=field)
    tree.column(field, width=120)

# Insert data
for i, record in enumerate(records):
    values = []
    for f in fields:
        v = getattr(record, f)
        values.append("" if v is None else str(v))
    tree.insert("", "end", iid=i, values=values)

# =========================
# EDIT FUNCTION
# =========================
def edit_record():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a row first")
        return

    index = int(selected[0])
    record = records[index]

    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Record")
    edit_window.geometry("500x400")

    # Scrollable frame
    canvas = tk.Canvas(edit_window)
    scrollbar = ttk.Scrollbar(edit_window, orient="vertical", command=canvas.yview)
    frame = ttk.Frame(canvas)

    frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    entries = {}

    # Form
    for i, field in enumerate(fields):
        tk.Label(frame, text=field).grid(row=i, column=0, sticky="w", padx=5, pady=2)

        entry = tk.Entry(frame, width=40)
        entry.grid(row=i, column=1, padx=5, pady=2)

        value = getattr(record, field)
        if value is None:
            value = ""

        entry.insert(0, str(value))
        entries[field] = entry

    # =========================
    # SAVE FUNCTION
    # =========================
    def save_changes():
        try:
            with record:  # REQUIRED by dbf
                for field in fields:
                    value = entries[field].get()
                    field_type = field_types.get(field, 'C')

                    if value.strip() == "":
                        value = None

                    else:
                        try:
                            # INTEGER
                            if value.isdigit():
                                value = int(value)

                            # FLOAT
                            elif '.' in value and field_type != 'T':
                                value = float(value)

                            # DATE (YYYY-MM-DD)
                            elif field_type == 'D':
                                value = datetime.strptime(value, "%Y-%m-%d").date()

                            # DATETIME (handles your format)
                            elif field_type == 'T':
                                try:
                                    value = datetime.fromisoformat(value)
                                except:
                                    try:
                                        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                                    except:
                                        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

                        except:
                            pass  # fallback to string

                    setattr(record, field, value)

            # Update treeview
            updated_values = [
                "" if getattr(record, f) is None else str(getattr(record, f))
                for f in fields
            ]
            tree.item(selected, values=updated_values)

            messagebox.showinfo("Success", "Record updated!")
            edit_window.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Save button
    tk.Button(frame, text="Save", command=save_changes)\
        .grid(row=len(fields), column=0, columnspan=2, pady=10)

# =========================
# BUTTON
# =========================
tk.Button(root, text="Edit Selected", command=edit_record).pack(pady=10)

# =========================
# RUN
# =========================
root.mainloop()

table.close()
