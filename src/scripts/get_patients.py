"""
Script principal para obtener pacientes citados (p1).
"""
import sys
import re
import time
from datetime import date, datetime
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.domain.models import Paciente, RangoFechas
from src.services.scraper_service import WebScraperService
from src.services.patient_service import PatientService
from src.services.excel_service import ExcelService
from src.ui.console import ConsoleUI
from src.config.settings import settings
from src.config.constants import MESES_ES
from src.core.logging import get_logger
from src.core.utils import format_rut, clean_name


logger = get_logger(__name__)


class GetPatientsScript:
    """Script para obtener pacientes citados."""
    
    def __init__(self):
        self.ui = ConsoleUI()
        self.patient_service = PatientService()
        self.excel_service = ExcelService()
    
    def run(self) -> None:
        """Ejecuta el script principal."""
        try:
            # Solicita rango de fechas
            rango = self.ui.request_date_range()
            
            # Obtiene credenciales
            location, username, password = self.ui.get_credentials()
            
            # Inicia scraping
            self.ui.print_info("Iniciando proceso de extracción...")
            patients = self._scrape_patients(rango, location, username, password)
            
            if not patients:
                self.ui.print_warning("No se encontraron pacientes en el rango especificado")
                return
            
            # Guarda resultados
            filename = f"pacientes_citados_{rango.anio}_{rango.mes:02d}_{rango.dia_inicio:02d}_{rango.dia_fin:02d}.xlsx"
            filepath = self.excel_service.save_patients(patients, filename)
            
            self.ui.print_success(f"Proceso completado. {len(patients)} pacientes guardados en {filepath}")
            
        except KeyboardInterrupt:
            self.ui.print_warning("\nProceso interrumpido por el usuario")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error en script: {e}", exc_info=True)
            self.ui.print_error(f"Error: {e}")
            sys.exit(1)
    
    def _scrape_patients(
        self, 
        rango: RangoFechas,
        location: str,
        username: str,
        password: str
    ) -> List[Paciente]:
        """
        Realiza el scraping de pacientes.
        
        Args:
            rango: Rango de fechas
            location: Ubicación
            username: Usuario
            password: Contraseña
            
        Returns:
            Lista de pacientes encontrados
        """
        patients = []
        
        with WebScraperService(headless=settings.HEADLESS) as scraper:
            # Login
            scraper.login(location, username, password)
            
            # Navega a pacientes citados
            scraper.navigate_to_menu("Box", "Pacientes citados")
            
            # Procesa cada fecha
            for fecha in rango.get_dates():
                self.ui.print_info(f"Procesando {fecha.strftime('%d-%m-%Y')}...")
                
                try:
                    # Selecciona la fecha
                    if self._select_date(scraper, fecha):
                        # Extrae pacientes del día
                        day_patients = self._extract_day_patients(scraper, fecha)
                        patients.extend(day_patients)
                        self.ui.print_success(f"  → {len(day_patients)} pacientes encontrados")
                    else:
                        self.ui.print_warning(f"  → Fecha no disponible")
                except Exception as e:
                    logger.error(f"Error procesando fecha {fecha}: {e}")
                    self.ui.print_error(f"  → Error: {e}")
        
        return patients
    
    def _select_date(self, scraper: WebScraperService, fecha: date) -> bool:
        """
        Selecciona una fecha en el calendario.
        
        Args:
            scraper: Servicio de scraping
            fecha: Fecha a seleccionar
            
        Returns:
            True si se pudo seleccionar la fecha
        """
        try:
            # Abre el datepicker
            datepicker = scraper.wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    ".patient-calendar .react-datepicker__input-container span"
                ))
            )
            datepicker.click()
            
            # Espera que aparezca el calendario
            scraper.wait.until(
                EC.visibility_of_element_located((By.CLASS_NAME, "react-datepicker__month"))
            )
            
            # Ajusta mes y año
            self._adjust_month_year(scraper, fecha.year, fecha.month)
            
            # Selecciona el día
            day_xpath = (
                f"//div[contains(@class, 'react-datepicker__day') "
                f"and not(contains(@class, 'react-datepicker__day--outside-month')) "
                f"and text()='{fecha.day}']"
            )
            
            day_element = scraper.wait.until(
                EC.element_to_be_clickable((By.XPATH, day_xpath))
            )
            day_element.click()
            
            time.sleep(2)  # Espera carga de datos
            return True
            
        except TimeoutException:
            logger.debug(f"No se pudo seleccionar la fecha {fecha}")
            return False
    
    def _adjust_month_year(self, scraper: WebScraperService, year: int, month: int):
        """
        Ajusta el mes y año en el datepicker.
        
        Args:
            scraper: Servicio de scraping
            year: Año objetivo
            month: Mes objetivo (1-12)
        """
        month_name = MESES_ES[month - 1]
        
        while True:
            # Lee mes y año actual
            current_month = scraper.driver.find_element(
                By.CLASS_NAME, "react-datepicker__current-month"
            ).text.lower()
            
            current_year = scraper.driver.find_element(
                By.CLASS_NAME, "react-datepicker__year-read-view--selected-year"
            ).text.strip()
            
            # Verifica si ya está en el mes/año correcto
            if current_month.startswith(month_name) and current_year == str(year):
                break
            
            # Ajusta año si es necesario
            if current_year != str(year):
                year_selector = scraper.driver.find_element(
                    By.CLASS_NAME, "react-datepicker__year-read-view"
                )
                year_selector.click()
                time.sleep(0.5)
                
                year_option = scraper.driver.find_element(
                    By.XPATH,
                    f"//div[contains(@class, 'react-datepicker__year-option') and text()='{year}']"
                )
                year_option.click()
                time.sleep(0.5)
            
            # Ajusta mes
            else:
                month_selector = scraper.driver.find_element(
                    By.CLASS_NAME, "react-datepicker__month-read-view"
                )
                month_selector.click()
                time.sleep(0.5)
                
                month_option = scraper.driver.find_element(
                    By.XPATH,
                    f"//div[contains(@class, 'react-datepicker__month-option') and text()='{month_name}']"
                )
                month_option.click()
                time.sleep(0.5)
    
    def _extract_day_patients(self, scraper: WebScraperService, fecha: date) -> List[Paciente]:
        """
        Extrae pacientes de un día específico.
        
        Args:
            scraper: Servicio de scraping
            fecha: Fecha a procesar
            
        Returns:
            Lista de pacientes del día
        """
        patients = []
        
        try:
            # Obtiene la fecha mostrada en la página
            fecha_str = scraper.driver.find_element(By.XPATH, "//strong").text
            
            # Busca todas las filas de la tabla
            rows = scraper.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'rt-tr') and @role='row']"
            )
            
            for idx, row in enumerate(rows):
                try:
                    # Extrae celdas
                    cells = row.find_elements(By.XPATH, ".//div[contains(@class, 'rt-td')]")
                    
                    if len(cells) < 3:
                        continue
                    
                    # Extrae nombre de la tercera celda
                    nombre = clean_name(cells[2].text)
                    if not nombre:
                        continue
                    
                    # Verifica estado (NSP)
                    estado = cells[1].text.strip().lower()
                    tipo_atencion = "NSP" if "no se present" in estado else "ASISTE"
                    
                    # Click en la fila para abrir popover
                    row.click()
                    
                    # Espera el popover
                    scraper.wait.until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "popover-body"))
                    )
                    
                    # Extrae información del popover
                    popover_text = scraper.driver.find_element(By.CLASS_NAME, "popover-body").text
                    
                    # Extrae RUN
                    run = self._extract_run(popover_text)
                    
                    # Extrae sector
                    sector = self._extract_sector(popover_text)
                    
                    # Extrae edad
                    edad_rango = self._extract_age_range(popover_text)
                    
                    # Crea el paciente
                    paciente = Paciente(
                        run=run,
                        nombre=nombre,
                        fecha=fecha,
                        sector=sector,
                        edad_rango=edad_rango,
                        tipo_atencion=self.patient_service.detect_attention_type(tipo_atencion)
                    )
                    
                    patients.append(paciente)
                    
                except Exception as e:
                    logger.debug(f"Error procesando fila {idx}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extrayendo pacientes del día: {e}")
        
        return patients
    
    def _extract_run(self, text: str) -> str:
        """Extrae el RUN del texto del popover."""
        # Busca formato con guión
        match = re.search(r"RUN\s*:?\s*([\d\.]+-[\dkK])", text)
        if match:
            return match.group(1).upper()
        
        # Busca solo números
        match = re.search(r"RUN\s*:?\s*(\d+)", text)
        if match:
            return format_rut(match.group(1))
        
        return ""
    
    def _extract_sector(self, text: str) -> str:
        """Extrae el sector del texto del popover."""
        match = re.search(r"sector:\s*(\w+)", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return ""
    
    def _extract_age_range(self, text: str) -> str:
        """Extrae el rango de edad del texto del popover."""
        match = re.search(r"Paciente de:\s*(.+)", text)
        if match:
            return self.patient_service.extract_age_range(match.group(1))
        return ""


def main():
    """Punto de entrada del script."""
    script = GetPatientsScript()
    script.run()


if __name__ == "__main__":
    main()