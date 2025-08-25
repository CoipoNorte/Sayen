"""
Interfaz gráfica con CustomTkinter.
"""
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import subprocess
import sys

import customtkinter as ctk

from src.config.settings import settings
from src.core.logging import get_logger


logger = get_logger(__name__)


class SayenGUI(ctk.CTk):
    """Interfaz gráfica principal de Sayen."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Sayen - Configuración y Lanzador")
        self.geometry("650x550")
        self.resizable(False, False)
        
        # Configurar icono
        self._set_icon()
        
        # Configuración de tema
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Variables
        self.var_location = tk.StringVar(value=settings.RAYEN_LOCATION)
        self.var_username = tk.StringVar(value=settings.RAYEN_USERNAME)
        self.var_password = tk.StringVar(value=settings.RAYEN_PASSWORD)
        self.var_headless = tk.BooleanVar(value=settings.HEADLESS)
        self.var_showpass = tk.BooleanVar(value=False)
        self.var_theme = tk.StringVar(value="System")
        
        self._build_ui()
    
    def _set_icon(self):
        """Configura el icono de la ventana."""
        try:
            # Busca el icono en la carpeta ico
            icon_path = settings.BASE_DIR / "ico" / "sayen.ico"
            
            if icon_path.exists():
                # En Windows, CustomTkinter hereda de CTk que hereda de Tk
                self.iconbitmap(default=str(icon_path))
                logger.debug(f"Icono cargado desde: {icon_path}")
            else:
                logger.warning(f"Icono no encontrado en: {icon_path}")
                
        except Exception as e:
            logger.error(f"Error al cargar el icono: {e}")
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        # Header
        self._build_header()
        
        # Credenciales
        self._build_credentials_frame()
        
        # Botones de acción
        self._build_action_buttons()
        
        # Log
        self._build_log_area()
        
        # Mensaje inicial
        self._log("🎯 Sistema listo. Configura tus credenciales y ejecuta los scripts.")
    
    def _build_header(self):
        """Construye el encabezado."""
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=12, pady=(12, 8))
        
        # Frame para título y logo
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=10, pady=5)
        
        # Título con emojis o símbolo
        title_label = ctk.CTkLabel(
            title_frame, 
            text="🏥 Sayen · Rayen APS", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left")
        
        # Versión o subtítulo
        version_label = ctk.CTkLabel(
            title_frame,
            text="v1.0",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack(side="left", padx=(10, 0))
        
        # Selector de tema
        theme_frame = ctk.CTkFrame(header, fg_color="transparent")
        theme_frame.pack(side="right", padx=10)
        
        ctk.CTkLabel(theme_frame, text="Tema:").pack(side="left", padx=(0, 8))
        
        theme_selector = ctk.CTkSegmentedButton(
            theme_frame,
            values=["System", "Light", "Dark"],
            command=self._on_theme_change,
            variable=self.var_theme
        )
        theme_selector.pack(side="left")
    
    def _build_credentials_frame(self):
        """Construye el frame de credenciales."""
        # Frame principal con borde
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="x", padx=12, pady=8)
        
        # Título del frame
        ctk.CTkLabel(
            main_frame,
            text="⚙️ Configuración de Credenciales",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 15))
        
        # Ubicación
        ctk.CTkLabel(main_frame, text="📍 Ubicación:").grid(
            row=1, column=0, sticky="w", padx=10, pady=10
        )
        self.entry_location = ctk.CTkEntry(
            main_frame, 
            textvariable=self.var_location, 
            width=350,
            placeholder_text="Ej: cesfamaguirre"
        )
        self.entry_location.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        # Usuario
        ctk.CTkLabel(main_frame, text="👤 Usuario:").grid(
            row=2, column=0, sticky="w", padx=10, pady=10
        )
        self.entry_username = ctk.CTkEntry(
            main_frame,
            textvariable=self.var_username,
            width=350,
            placeholder_text="Ej: 194322712"
        )
        self.entry_username.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        
        # Contraseña
        ctk.CTkLabel(main_frame, text="🔐 Contraseña:").grid(
            row=3, column=0, sticky="w", padx=10, pady=10
        )
        self.entry_password = ctk.CTkEntry(
            main_frame,
            textvariable=self.var_password,
            width=350,
            show="*",
            placeholder_text="********"
        )
        self.entry_password.grid(row=3, column=1, sticky="w", padx=10, pady=10)
        
        # Checkbox mostrar contraseña
        show_pass = ctk.CTkCheckBox(
            main_frame,
            text="Mostrar",
            variable=self.var_showpass,
            command=self._toggle_password
        )
        show_pass.grid(row=3, column=2, sticky="w", padx=10, pady=10)
        
        # Switch headless
        headless_switch = ctk.CTkSwitch(
            main_frame,
            text="🖥️ Modo headless (sin ventana del navegador)",
            variable=self.var_headless
        )
        headless_switch.grid(
            row=4, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 15)
        )
        
        # Configurar expansión de columnas
        main_frame.grid_columnconfigure(1, weight=1)
    
    def _build_action_buttons(self):
        """Construye los botones de acción."""
        # Frame para botones
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.pack(fill="x", padx=12, pady=10)
        
        # Título de sección
        ctk.CTkLabel(
            buttons_frame,
            text="🚀 Acciones",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 10))
        
        # Frame para organizar botones
        btn_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        btn_container.pack(fill="x", padx=10, pady=(0, 10))
        
        # Botón guardar
        save_btn = ctk.CTkButton(
            btn_container,
            text="💾 Guardar Configuración",
            command=self._save_config,
            width=180,
            height=35
        )
        save_btn.pack(side="left", padx=5)
        
        # Botón obtener pacientes
        get_patients_btn = ctk.CTkButton(
            btn_container,
            text="📋 Obtener Pacientes",
            command=self._run_get_patients,
            width=180,
            height=35,
            fg_color="#1f8754",  # Verde
            hover_color="#146c43"
        )
        get_patients_btn.pack(side="left", padx=5)
        
        # Botón completar datos
        fill_data_btn = ctk.CTkButton(
            btn_container,
            text="✏️ Completar Datos",
            command=self._run_fill_data,
            width=180,
            height=35,
            fg_color="#fd7e14",  # Naranja
            hover_color="#e36209"
        )
        fill_data_btn.pack(side="left", padx=5)
    
    def _build_log_area(self):
        """Construye el área de log."""
        # Frame para el log
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Título del log
        ctk.CTkLabel(
            log_frame,
            text="📝 Registro de Actividad",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Área de texto para el log
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")
    
    def _on_theme_change(self, choice: str):
        """Cambia el tema de la aplicación."""
        ctk.set_appearance_mode(choice)
        self._log(f"🎨 Tema cambiado a: {choice}")
    
    def _toggle_password(self):
        """Alterna la visibilidad de la contraseña."""
        self.entry_password.configure(
            show="" if self.var_showpass.get() else "*"
        )
    
    def _save_config(self):
        """Guarda la configuración en el archivo .env."""
        data = {
            "RAYEN_LOCATION": self.var_location.get().strip(),
            "RAYEN_USERNAME": self.var_username.get().strip(),
            "RAYEN_PASSWORD": self.var_password.get().strip(),
            "HEADLESS": "true" if self.var_headless.get() else "false",
        }
        
        # Valida datos
        if not all([data["RAYEN_LOCATION"], data["RAYEN_USERNAME"], data["RAYEN_PASSWORD"]]):
            messagebox.showwarning(
                "Datos incompletos",
                "Por favor completa todos los campos de credenciales."
            )
            return
        
        try:
            settings.update_env_file(data)
            self._log("✅ Configuración guardada correctamente")
            messagebox.showinfo("Éxito", "Configuración guardada en .env")
        except Exception as e:
            self._log(f"❌ Error al guardar: {e}")
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")
    
    def _run_get_patients(self):
        """Ejecuta el script de obtener pacientes."""
        self._run_script("get_patients", "Obtener Pacientes")
    
    def _run_fill_data(self):
        """Ejecuta el script de completar datos."""
        self._run_script("fill_data", "Completar Datos")
    
    def _run_script(self, script_name: str, display_name: str):
        """
        Ejecuta un script en una nueva consola.
        
        Args:
            script_name: Nombre del módulo a ejecutar
            display_name: Nombre para mostrar en el log
        """
        try:
            self._log(f"🚀 Ejecutando {display_name}...")
            
            # Comando para ejecutar el script
            if script_name == "get_patients":
                cmd = [sys.executable, "-m", "src.scripts.get_patients"]
            elif script_name == "fill_data":
                cmd = [sys.executable, "-m", "src.scripts.fill_data"]
            else:
                self._log(f"❌ Script desconocido: {script_name}")
                return
            
            kwargs = {"cwd": str(settings.BASE_DIR)}
            
            # En Windows, abrir en nueva consola
            if sys.platform == "win32":
                import subprocess
                kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
            
            subprocess.Popen(cmd, **kwargs)
            
        except Exception as e:
            self._log(f"❌ Error al ejecutar {display_name}: {e}")
            messagebox.showerror("Error", f"No se pudo ejecutar {display_name}:\n{e}")
    
    def _log(self, message: str):
        """Agrega un mensaje al log con timestamp."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{formatted_message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


def main():
    """Punto de entrada de la GUI."""
    app = SayenGUI()
    app.mainloop()


if __name__ == "__main__":
    main()