"""
Interfaz de usuario para consola.
"""
import sys
import os
import getpass
from typing import Optional, Tuple
from datetime import date

from src.domain.models import RangoFechas
from src.config.settings import settings
from src.core.utils import is_empty

# Habilitar colores ANSI en Windows
if os.name == 'nt':
    try:
        from colorama import init, Fore, Style
        init(autoreset=True)
        USE_COLORAMA = True
    except ImportError:
        USE_COLORAMA = False
else:
    USE_COLORAMA = False


class ConsoleUI:
    """Interfaz de usuario para línea de comandos."""
    
    if USE_COLORAMA:
        # Usar colorama en Windows
        COLORS = {
            'cyan': Fore.CYAN,
            'green': Fore.GREEN,
            'yellow': Fore.YELLOW,
            'red': Fore.RED,
            'reset': Style.RESET_ALL
        }
    else:
        # Códigos ANSI estándar
        COLORS = {
            'cyan': '\033[96m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'reset': '\033[0m'
        }
    
    def print_colored(self, text: str, color: str = 'reset', end: str = '\n') -> None:
        """
        Imprime texto con color.
        
        Args:
            text: Texto a imprimir
            color: Color a usar
            end: Carácter de fin de línea
        """
        if os.name == 'nt' and not USE_COLORAMA:
            # En Windows sin colorama, imprimir sin colores
            print(text, end=end, flush=True)
        else:
            color_code = self.COLORS.get(color, self.COLORS['reset'])
            print(f"{color_code}{text}{self.COLORS['reset']}", end=end, flush=True)
        
    def print_info(self, text: str) -> None:
        """Imprime mensaje informativo."""
        self.print_colored(text, 'cyan')
    
    def print_success(self, text: str) -> None:
        """Imprime mensaje de éxito."""
        self.print_colored(text, 'green')
    
    def print_warning(self, text: str) -> None:
        """Imprime mensaje de advertencia."""
        self.print_colored(text, 'yellow')
    
    def print_error(self, text: str) -> None:
        """Imprime mensaje de error."""
        self.print_colored(text, 'red')
    
    def print_header(self, text: str) -> None:
        """Imprime un encabezado."""
        separator = "=" * len(text)
        self.print_colored(f"\n{separator}", 'cyan')
        self.print_colored(text, 'cyan')
        self.print_colored(separator, 'cyan')
    
    def input_colored(self, prompt: str, color: str = 'cyan') -> str:
        """
        Solicita input con prompt coloreado.
        
        Args:
            prompt: Texto del prompt
            color: Color del prompt
            
        Returns:
            Input del usuario
        """
        if os.name == 'nt' and not USE_COLORAMA:
            return input(prompt)
        else:
            color_code = self.COLORS.get(color, self.COLORS['reset'])
            return input(f"{color_code}{prompt}{self.COLORS['reset']}")
    
    def request_date_range(self) -> RangoFechas:
        """
        Solicita un rango de fechas al usuario.
        
        Returns:
            RangoFechas validado
        """
        self.print_header("Configuración de rango de fechas")
        
        while True:
            try:
                anio = int(self.input_colored("Año (ej: 2025): "))
                mes = int(self.input_colored("Mes (1-12): "))
                dia_inicio = int(self.input_colored("Día de inicio: "))
                dia_fin = int(self.input_colored("Día de fin: "))
                
                rango = RangoFechas(anio, mes, dia_inicio, dia_fin)
                
                # Muestra resumen
                self.print_success(f"\nRango seleccionado: {dia_inicio}/{mes}/{anio} - {dia_fin}/{mes}/{anio}")
                
                confirm = self.input_colored("¿Es correcto? (s/n): ").lower()
                if confirm == 's':
                    return rango
                    
            except ValueError as e:
                self.print_error(f"Error: {e}")
                self.print_warning("Por favor, intenta nuevamente.\n")
    
    def get_credentials(self) -> Tuple[str, str, str]:
        """
        Obtiene las credenciales del usuario.
        
        Returns:
            Tupla con (location, username, password)
        """
        # Intenta usar credenciales del entorno
        location = settings.RAYEN_LOCATION
        username = settings.RAYEN_USERNAME
        password = settings.RAYEN_PASSWORD
        
        # Si faltan, las solicita
        if not location:
            location = self.input_colored("Ubicación (RAYEN_LOCATION): ")
        
        if not username:
            username = self.input_colored("Usuario (RAYEN_USERNAME): ")
        
        if not password:
            if os.name == 'nt' and not USE_COLORAMA:
                password = getpass.getpass("Contraseña (RAYEN_PASSWORD): ")
            else:
                password = getpass.getpass(
                    f"{self.COLORS['cyan']}Contraseña (RAYEN_PASSWORD): {self.COLORS['reset']}"
                )
        
        return location.strip(), username.strip(), password.strip()
    
    def pause_or_timeout(self, seconds: int = 7) -> None:
        """
        Pausa con opción de continuar o timeout.
        
        Args:
            seconds: Segundos de timeout
        """
        import time
        
        if os.name == 'nt':
            try:
                import msvcrt
                
                msg = "Presiona ENTER para continuar (auto en {}s)..."
                
                start = time.time()
                last_printed = seconds
                
                while True:
                    elapsed = time.time() - start
                    remaining = max(0, seconds - int(elapsed))
                    
                    # Actualiza el mensaje solo cuando cambia el segundo
                    if remaining != last_printed:
                        # Limpia la línea y muestra el nuevo mensaje
                        print('\r' + ' ' * 80, end='\r')
                        self.print_colored(msg.format(remaining), 'yellow', end='\r')
                        last_printed = remaining
                    
                    # Verifica si se presionó ENTER
                    if msvcrt.kbhit():
                        if msvcrt.getwch() in ("\r", "\n"):
                            print('\r' + ' ' * 80, end='\r')
                            self.print_info("Continuando...")
                            return
                    
                    # Timeout
                    if elapsed >= seconds:
                        print('\r' + ' ' * 80, end='\r')
                        self.print_info("Continuando automáticamente...")
                        return
                    
                    time.sleep(0.1)
                    
            except ImportError:
                # Si msvcrt no está disponible
                for i in range(seconds, 0, -1):
                    print('\r' + ' ' * 80, end='\r')
                    self.print_colored(f"Continuando en {i} segundos...", 'yellow', end='\r')
                    time.sleep(1)
                print('\r' + ' ' * 80, end='\r')
                self.print_info("Continuando...")
        else:
            # En sistemas no-Windows
            for i in range(seconds, 0, -1):
                print('\r' + ' ' * 80, end='\r')
                self.print_colored(f"Continuando en {i} segundos...", 'yellow', end='\r')
                time.sleep(1)
            print('\r' + ' ' * 80, end='\r')
            self.print_info("Continuando...")