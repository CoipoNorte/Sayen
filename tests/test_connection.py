"""
Script de prueba para verificar la conexión y login.
"""
from src.services.scraper_service import WebScraperService
from src.ui.console import ConsoleUI
from src.config.settings import settings


def main():
    ui = ConsoleUI()
    
    ui.print_header("Prueba de conexión a Rayen APS")
    
    # Obtener credenciales
    location, username, password = ui.get_credentials()
    
    ui.print_info("Iniciando navegador...")
    
    # Probar conexión
    try:
        with WebScraperService(headless=False) as scraper:
            ui.print_info("Navegador iniciado correctamente")
            
            ui.print_info("Intentando login...")
            scraper.login(location, username, password)
            
            ui.print_success("✅ Login exitoso!")
            
            ui.print_info("Navegando al menú Box...")
            scraper.navigate_to_menu("Box", "Pacientes citados")
            
            ui.print_success("✅ Navegación exitosa!")
            
            ui.pause_or_timeout(5)
            
    except Exception as e:
        ui.print_error(f"❌ Error: {e}")
        return 1
    
    ui.print_success("Prueba completada exitosamente")
    return 0


if __name__ == "__main__":
    exit(main())