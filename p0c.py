# p0.py
# GUI (CustomTkinter) para gestionar credenciales (.env) y lanzar p1/p2

import os
import sys
import subprocess
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sayen - Configuración y Lanzador")
        self.geometry("600x520")
        self.resizable(False, False)

        # Tema/Colores
        ctk.set_appearance_mode("System")   # "System" | "Light" | "Dark"
        ctk.set_default_color_theme("blue") # "blue" | "green" | "dark-blue"

        # Vars
        self.var_location = tk.StringVar()
        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_headless = tk.BooleanVar(value=False)
        self.var_showpass = tk.BooleanVar(value=False)
        self.var_theme = tk.StringVar(value="System")  # System/Light/Dark

        self._build_ui()
        self._load_env_into_fields()

    def _build_ui(self):
        # Header: título + selector de tema
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=12, pady=(12, 8))

        title = ctk.CTkLabel(header, text="Sayen · Rayen APS", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(side="left", padx=8, pady=8)

        theme_frame = ctk.CTkFrame(header, fg_color="transparent")
        theme_frame.pack(side="right", padx=8)
        ctk.CTkLabel(theme_frame, text="Tema:").pack(side="left", padx=(0,6))
        theme_selector = ctk.CTkSegmentedButton(
            theme_frame, values=["System", "Light", "Dark"], command=self._on_theme_change,
            variable=self.var_theme
        )
        theme_selector.pack(side="left")

        # Credenciales
        frm = ctk.CTkFrame(self)
        frm.pack(fill="x", padx=12, pady=8)

        # Ubicación
        ctk.CTkLabel(frm, text="Ubicación (location):").grid(row=0, column=0, sticky="w", padx=10, pady=8)
        self.entry_location = ctk.CTkEntry(frm, textvariable=self.var_location, width=320, placeholder_text="cesfamaguirre")
        self.entry_location.grid(row=0, column=1, sticky="w", padx=10, pady=8)

        # Usuario
        ctk.CTkLabel(frm, text="Usuario:").grid(row=1, column=0, sticky="w", padx=10, pady=8)
        self.entry_username = ctk.CTkEntry(frm, textvariable=self.var_username, width=320, placeholder_text="194322712")
        self.entry_username.grid(row=1, column=1, sticky="w", padx=10, pady=8)

        # Contraseña + mostrar
        ctk.CTkLabel(frm, text="Contraseña:").grid(row=2, column=0, sticky="w", padx=10, pady=8)
        self.entry_password = ctk.CTkEntry(frm, textvariable=self.var_password, width=320, show="*", placeholder_text="********")
        self.entry_password.grid(row=2, column=1, sticky="w", padx=10, pady=8)

        showpass = ctk.CTkCheckBox(frm, text="Mostrar contraseña", variable=self.var_showpass, command=self._toggle_password)
        showpass.grid(row=2, column=2, sticky="w", padx=10, pady=8)

        # Headless
        headless_switch = ctk.CTkSwitch(frm, text="Headless (sin ventana de navegador)", variable=self.var_headless)
        headless_switch.grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 10))

        # Botones de acción
        btns = ctk.CTkFrame(self)
        btns.pack(fill="x", padx=12, pady=(0, 10))

        save_btn = ctk.CTkButton(btns, text="Guardar credenciales", command=self.on_save)
        save_btn.pack(side="left", padx=6)

        run_p1_btn = ctk.CTkButton(btns, text="Obtener RUTS (p1)", command=self.run_p1)
        run_p1_btn.pack(side="left", padx=6)

        run_p2_btn = ctk.CTkButton(btns, text="Rellenar Datos (p2)", command=self.run_p2)
        run_p2_btn.pack(side="left", padx=6)

        # Log (read-only)
        self.txt = ctk.CTkTextbox(self, height=220)
        self.txt.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.txt.configure(state="disabled")
        self._log("Listo. Completa y guarda tus credenciales. Luego lanza p1 o p2.")

        # Grid expand
        frm.grid_columnconfigure(1, weight=1)

    # ------------------------ Eventos UI ------------------------

    def _on_theme_change(self, choice: str):
        ctk.set_appearance_mode(choice)

    def _toggle_password(self):
        self.entry_password.configure(show="" if self.var_showpass.get() else "*")

    # ------------------------ Env helpers ------------------------

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

    # ------------------------ Lanzadores ------------------------

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

        # En Windows, abrir en una nueva consola para mantener colores e inputs
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
            try:
                subprocess.Popen(cmd, **kwargs)
                self._log(f"Ejecutando {script_name}...")
            except Exception as e:
                self._log(f"Error al ejecutar {script_name}: {e}")
                messagebox.showerror("Error", f"No se pudo ejecutar {script_name}:\n{e}")

    # ------------------------ Log ------------------------

    def _log(self, msg: str):
        self.txt.configure(state="normal")
        self.txt.insert("end", f"{msg}\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()