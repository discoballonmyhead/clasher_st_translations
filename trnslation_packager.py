#!/usr/bin/env python3
"""
Packs a wide-format translations Excel file (.xlsx) into per-language 
zip files ready to attach to a GitHub Release, using a Tkinter GUI.
"""
from __future__ import annotations

import json
import sys
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("Error: 'openpyxl' is required to read .xlsx files.")
    print("Please install it using: pip install openpyxl")
    sys.exit(1)


def load_rows_xlsx(xlsx_path: Path) -> list[dict[str, str]]:
    """Reads the active sheet of an Excel workbook into a list of dictionaries."""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    sheet = wb.active
    
    rows = list(sheet.iter_rows(values_only=True))
    if not rows or len(rows) < 1:
        raise ValueError("Excel file is empty")

    # Extract headers and ensure they are strings
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    if not any(headers):
        raise ValueError("No headers found in the first row")

    dict_rows = []
    for row in rows[1:]:
        row_dict = {}
        for header, val in zip(headers, row):
            if header:  # Only capture columns that have a header
                row_dict[header] = str(val).strip() if val is not None else ""
        dict_rows.append(row_dict)

    return dict_rows


def build_language_maps(rows: list[dict[str, str]], key_column: str) -> dict[str, dict[str, str]]:
    if not rows:
        return {}

    lang_codes = [c for c in rows[0].keys() if c and c != key_column]
    maps: dict[str, dict[str, str]] = {code: {} for code in lang_codes}

    for row in rows:
        key = (row.get(key_column) or "").strip()
        if not key:
            continue
        for code in lang_codes:
            value = (row.get(code) or "").strip()
            if value:
                maps[code][key] = value

    return maps


def write_zip(out_dir: Path, code: str, translations: dict[str, str]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"lang_{code}.zip"
    payload = json.dumps(translations, ensure_ascii=False, indent=2)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("translations.json", payload)

    return zip_path


class TranslationPackagerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Translation Packager (.xlsx)")
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        # Variables
        self.file_path_var = tk.StringVar()
        self.out_dir_var = tk.StringVar(value=str(Path.cwd() / "dist"))
        self.key_col_var = tk.StringVar(value="key")
        self.skip_langs_var = tk.StringVar(value="en")

        self.setup_ui()

    def setup_ui(self):
        pad_options = {'padx': 10, 'pady': 5}

        # --- Input File Row ---
        frame_in = tk.Frame(self.root)
        frame_in.pack(fill=tk.X, **pad_options)
        tk.Label(frame_in, text="Input .xlsx:", width=12, anchor="w").pack(side=tk.LEFT)
        tk.Entry(frame_in, textvariable=self.file_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(frame_in, text="Browse...", command=self.browse_file).pack(side=tk.LEFT)

        # --- Output Dir Row ---
        frame_out = tk.Frame(self.root)
        frame_out.pack(fill=tk.X, **pad_options)
        tk.Label(frame_out, text="Output Dir:", width=12, anchor="w").pack(side=tk.LEFT)
        tk.Entry(frame_out, textvariable=self.out_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(frame_out, text="Browse...", command=self.browse_dir).pack(side=tk.LEFT)

        # --- Key Column Row ---
        frame_key = tk.Frame(self.root)
        frame_key.pack(fill=tk.X, **pad_options)
        tk.Label(frame_key, text="Key Column:", width=12, anchor="w").pack(side=tk.LEFT)
        tk.Entry(frame_key, textvariable=self.key_col_var, width=15).pack(side=tk.LEFT, padx=5)

        # --- Skip Languages Row ---
        frame_skip = tk.Frame(self.root)
        frame_skip.pack(fill=tk.X, **pad_options)
        tk.Label(frame_skip, text="Skip Langs:", width=12, anchor="w").pack(side=tk.LEFT)
        tk.Entry(frame_skip, textvariable=self.skip_langs_var, width=30).pack(side=tk.LEFT, padx=5)
        tk.Label(frame_skip, text="(comma or space separated)", fg="gray").pack(side=tk.LEFT)

        # --- Run Button ---
        tk.Button(self.root, text="Pack Translations", bg="#2e8b57", fg="white", 
                  font=("Arial", 11, "bold"), command=self.run_packaging).pack(pady=15, ipadx=10, ipady=5)

        # --- Output Log ---
        self.log_text = tk.Text(self.root, height=12, state=tk.DISABLED, bg="#f4f4f4")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select Translations Excel File",
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
        )
        if path:
            self.file_path_var.set(path)

    def browse_dir(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.out_dir_var.set(path)

    def log(self, message: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def run_packaging(self):
        in_path_str = self.file_path_var.get().strip()
        out_dir_str = self.out_dir_var.get().strip()
        key_col = self.key_col_var.get().strip()
        skip_str = self.skip_langs_var.get().replace(",", " ")
        skip_langs = [s.strip() for s in skip_str.split() if s.strip()]

        # Validations
        if not in_path_str:
            messagebox.showerror("Error", "Please select an input .xlsx file.")
            return
        if not out_dir_str:
            messagebox.showerror("Error", "Please select an output directory.")
            return
        if not key_col:
            messagebox.showerror("Error", "Key column cannot be empty.")
            return

        in_path = Path(in_path_str)
        out_dir = Path(out_dir_str)

        if not in_path.exists():
            messagebox.showerror("Error", f"File not found:\n{in_path}")
            return

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.log(f"Reading {in_path.name}...")

        try:
            rows = load_rows_xlsx(in_path)
            maps = build_language_maps(rows, key_col)

            if not maps:
                self.log("Error: No language columns found. Check your Key Column name.")
                return

            written = []
            for code, translations in maps.items():
                if code in skip_langs:
                    self.log(f"Skipping '{code}' (in skip list).")
                    continue
                if not translations:
                    self.log(f"Skipping '{code}': no non-empty values found.")
                    continue
                
                path = write_zip(out_dir, code, translations)
                written.append((code, path, len(translations)))

            self.log("-" * 40)
            for code, path, count in written:
                size_kb = path.stat().st_size / 1024
                self.log(f"✔ {code}: {count} strings | {size_kb:.1f} KB -> {path.name}")

            self.log("-" * 40)
            self.log(f"Success! {len(written)} language pack(s) written to:\n{out_dir}")

            messagebox.showinfo("Success", f"Successfully packed {len(written)} language(s)!")

        except Exception as e:
            self.log(f"FATAL ERROR: {str(e)}")
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app_root = tk.Tk()
    app = TranslationPackagerGUI(app_root)
    app_root.mainloop()