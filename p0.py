# p0.py
# GUI para gestionar credenciales (.env) y lanzar p1/p2

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(PROJECT_DIR, ".env")

# ------------------------ Utils .env ------------------------

def parse_env(path: str) -> dict:
    env = {}
    if not os.path.isfile(path):
        return env
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env

def quote_value(val: str) -> str:
    # Escapa comillas; si contiene espacios o caracteres raros, lo envuelve
    val = val.replace('"', '\\"')
    if any(c in val for c in [" ", "#", "=", "\t"]):
        return f'"{val}"'
    return val

def write_env(path: str, data: dict):
    lines = [
        f'RAYEN_LOCATION={quote_value(data.get("RAYEN_LOCATION", ""))}',
        f'RAYEN_USERNAME={quote_value(data.get("RAYEN_USERNAME", ""))}',
        f'RAYEN_PASSWORD={quote_value(data.get("RAYEN_PASSWORD", ""))}',
        f'HEADLESS={quote_value(data.get("HEADLESS", "false"))}',
        ""
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# ------------------------ GUI ------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sayen - Configuración y Lanzador")
        self.geometry("520x420")
        self.resizable(False, False)

        # Vars
        self.var_location = tk.StringVar()
        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_headless = tk.BooleanVar(value=False)

        self._build_ui()
        self._load_env_into_fields()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        frm = ttk.LabelFrame(self, text="Credenciales")
        frm.pack(fill="x", padx=10, pady=10)

        ttk.Label(frm, text="Ubicación (location):").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_location, width=36).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Usuario:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_username, width=36).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Contraseña:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_password, show="*", width=36).grid(row=2, column=1, sticky="w", **pad)

        ttk.Checkbutton(frm, text="Headless (sin ventana de navegador)", variable=self.var_headless).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10)
        )

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btns, text="Guardar credenciales", command=self.on_save).pack(side="left", padx=5)
        ttk.Button(btns, text="Obtener RUTS (p1)", command=self.run_p1).pack(side="left", padx=5)
        ttk.Button(btns, text="Rellenar Datos (p2)", command=self.run_p2).pack(side="left", padx=5)

        # Log area (informativo; p1 abre su propia consola)
        self.txt = ScrolledText(self, height=12, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._log("Listo. Completa y guarda tus credenciales. Luego lanza p1 o p2.")

    def _load_env_into_fields(self):
        env = parse_env(ENV_PATH)
        self.var_location.set(env.get("RAYEN_LOCATION", ""))
        self.var_username.set(env.get("RAYEN_USERNAME", ""))
        self.var_password.set(env.get("RAYEN_PASSWORD", ""))
        self.var_headless.set(env.get("HEADLESS", "false").lower() in {"1", "true", "yes"})

    def on_save(self):
        data = {
            "RAYEN_LOCATION": self.var_location.get().strip(),
            "RAYEN_USERNAME": self.var_username.get().strip(),
            "RAYEN_PASSWORD": self.var_password.get().strip(),
            "HEADLESS": "true" if self.var_headless.get() else "false",
        }
        if not data["RAYEN_LOCATION"] or not data["RAYEN_USERNAME"] or not data["RAYEN_PASSWORD"]:
            messagebox.showwarning("Faltan datos", "Completa ubicación, usuario y contraseña.")
            return
        try:
            write_env(ENV_PATH, data)
            self._log(f".env guardado en {ENV_PATH}")
            messagebox.showinfo("OK", "Credenciales guardadas en .env")
        except Exception as e:
            self._log(f"Error al guardar .env: {e}")
            messagebox.showerror("Error", f"No se pudo guardar .env:\n{e}")

    def run_p1(self):
        self._run_script("p1.py", nueva_consola=True)

    def run_p2(self):
        self._run_script("p2.py", nueva_consola=True)

    def _run_script(self, script_name: str, nueva_consola: bool = True):
        script_path = os.path.join(PROJECT_DIR, script_name)
        if not os.path.isfile(script_path):
            self._log(f"No se encontró {script_name} en {PROJECT_DIR}")
            messagebox.showerror("Error", f"No se encontró {script_name} en {PROJECT_DIR}")
            return

        python_exe = sys.executable
        cmd = [python_exe, script_path]
        kwargs = {"cwd": PROJECT_DIR}

        # En Windows, abre una nueva consola para mantener colores y permitir inputs (p1)
        if os.name == "nt" and nueva_consola:
            CREATE_NEW_CONSOLE = 0x00000010
            kwargs["creationflags"] = CREATE_NEW_CONSOLE
            try:
                subprocess.Popen(cmd, **kwargs)
                self._log(f"Ejecutando {script_name} en nueva consola...")
            except Exception as e:
                self._log(f"Error al ejecutar {script_name}: {e}")
                messagebox.showerror("Error", f"No se pudo ejecutar {script_name}:\n{e}")
        else:
            # En otros SO, lo lanzamos normal (no capturamos stdout interactivo)
            try:
                subprocess.Popen(cmd, **kwargs)
                self._log(f"Ejecutando {script_name}...")
            except Exception as e:
                self._log(f"Error al ejecutar {script_name}: {e}")
                messagebox.showerror("Error", f"No se pudo ejecutar {script_name}:\n{e}")

    def _log(self, msg: str):
        self.txt.insert("end", f"{msg}\n")
        self.txt.see("end")

if __name__ == "__main__":
    app = App()
    app.mainloop()