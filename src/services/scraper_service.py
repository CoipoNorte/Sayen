"""
Servicio de web scraping con Selenium.
"""
import os
import time
from typing import Optional, Tuple
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.core.logging import get_logger
from src.core.exceptions import ScrapingError, AuthenticationError
from src.config.settings import settings


logger = get_logger(__name__)


class WebScraperService:
    """Servicio para automatización web con Selenium."""
    
    def __init__(self, headless: Optional[bool] = None):
        """
        Inicializa el servicio.
        
        Args:
            headless: Si ejecutar sin interfaz gráfica
        """
        self.headless = headless if headless is not None else settings.HEADLESS
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
    
    def __enter__(self):
        """Entrada del context manager."""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager."""
        self.cleanup()
        return False
    
    def setup_driver(self) -> None:
        """Configura e inicializa el driver de Chrome."""
        try:
            # Silencia logs de Chrome en Windows
            if os.name == "nt":
                os.environ["CHROME_LOG_FILE"] = "NUL"
            else:
                os.environ["CHROME_LOG_FILE"] = "/dev/null"
            
            options = Options()
            
            if self.headless:
                options.add_argument("--headless=new")
                options.add_argument("--window-size=1920,1080")
            
            # Opciones para reducir ruido y mejorar estabilidad
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # Configurar Service según la versión de Selenium
            try:
                service = Service(log_output=os.devnull)
            except:
                service = Service()
            
            self.driver = webdriver.Chrome(options=options, service=service)
            self.wait = WebDriverWait(self.driver, settings.SELENIUM_TIMEOUT)
            
            logger.info("Driver de Chrome inicializado correctamente")
            
        except WebDriverException as e:
            logger.error(f"Error al inicializar el driver: {e}")
            raise ScrapingError(f"No se pudo inicializar el navegador: {e}")
    
    def cleanup(self) -> None:
        """Limpia recursos del driver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver cerrado correctamente")
            except Exception as e:
                logger.error(f"Error al cerrar el driver: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def login(self, location: str, username: str, password: str) -> None:
        """
        Realiza el login en Rayen APS.
        
        Args:
            location: Ubicación/centro
            username: Nombre de usuario
            password: Contraseña
            
        Raises:
            AuthenticationError: Si falla el login
        """
        try:
            logger.info(f"Iniciando sesión para usuario {username} en {location}")
            
            self.driver.get(settings.BASE_URL)
            
            # Espera y completa el formulario
            self.wait.until(EC.presence_of_element_located((By.ID, "location")))
            
            self.driver.find_element(By.ID, "location").send_keys(location)
            self.driver.find_element(By.ID, "username").send_keys(username)
            self.driver.find_element(By.ID, "password").send_keys(password)
            
            # Click en botón de login
            login_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Ingresar') and not(@disabled)]")
                )
            )
            login_btn.click()
            
            time.sleep(5)  # Espera para carga completa
            
            # Verifica que el login fue exitoso
            if "login" in self.driver.current_url.lower():
                raise AuthenticationError("Login falló - verificar credenciales")
            
            logger.info("Login exitoso")
            
        except TimeoutException:
            logger.error("Timeout durante el login")
            raise AuthenticationError("Timeout durante el login")
        except Exception as e:
            logger.error(f"Error durante el login: {e}")
            raise AuthenticationError(f"Error durante el login: {e}")
    
    def wait_for_loader(self) -> None:
        """Espera a que desaparezca el loader de carga."""
        try:
            self.wait.until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "cache-loading"))
            )
        except TimeoutException:
            logger.debug("Loader no encontrado o ya desapareció")
    
    def close_modal_if_present(self) -> None:
        """Cierra modal si está presente."""
        try:
            modal = self.driver.find_element(
                By.XPATH, 
                "//div[contains(@class,'modal') and contains(@class,'show')]"
            )
            for btn in modal.find_elements(By.XPATH, ".//button"):
                if btn.is_displayed():
                    btn.click()
                    time.sleep(1)
                    logger.debug("Modal cerrado")
                    break
        except:
            pass
    
    def navigate_to_menu(self, *menu_items: str) -> None:
        """
        Navega por el menú usando los textos especificados.
        
        Args:
            menu_items: Secuencia de textos del menú a clickear
        """
        # Primero abre el menú principal si es necesario
        try:
            navbar_menu = self.wait.until(
                EC.element_to_be_clickable((By.ID, "navbar-main-menu"))
            )
            navbar_menu.click()
            time.sleep(1)
        except:
            logger.debug("No se encontró navbar-main-menu o ya está abierto")
        
        for item in menu_items:
            try:
                self.wait_for_loader()
                self.close_modal_if_present()
                
                # Intenta diferentes selectores
                selectors = [
                    f"//li[.//span[text()='{item}']]",
                    f"//span[normalize-space(text())='{item}']",
                    f"//a[.//span[contains(text(),'{item}')]]",
                    f"//a[contains(., '{item}')]"
                ]
                
                clicked = False
                for selector in selectors:
                    try:
                        element = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        element.click()
                        clicked = True
                        logger.debug(f"Click en menú: {item}")
                        time.sleep(2)
                        break
                    except:
                        continue
                
                if not clicked:
                    raise ScrapingError(f"No se pudo encontrar el elemento del menú: {item}")
                    
            except Exception as e:
                logger.error(f"Error navegando al menú {item}: {e}")
                raise
    
    def get_element_text(self, selector: str, by: By = By.XPATH, timeout: int = 10) -> str:
        """
        Obtiene el texto de un elemento.
        
        Args:
            selector: Selector del elemento
            by: Tipo de selector
            timeout: Tiempo máximo de espera
            
        Returns:
            Texto del elemento o cadena vacía si no se encuentra
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element.text.strip()
        except TimeoutException:
            logger.debug(f"Elemento no encontrado: {selector}")
            return ""