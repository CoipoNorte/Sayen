"""
Script para completar datos faltantes en Excel (p2).
"""
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict
from tkinter import Tk, filedialog

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.domain.models import Paciente, TipoAtencion, Sexo
from src.services.scraper_service import WebScraperService
from src.services.patient_service import PatientService
from src.services.excel_service import ExcelService
from src.ui.console import ConsoleUI
from src.config.settings import settings
from src.core.logging import get_logger
from src.core.utils import is_empty, normalize_text, parse_age_to_months


logger = get_logger(__name__)


class FillDataScript:
    """Script para completar datos faltantes en Excel."""
    
    def __init__(self):
        self.ui = ConsoleUI()
        self.patient_service = PatientService()
        self.excel_service = ExcelService()
    
    def run(self) -> None:
        """Ejecuta el script principal."""
        try:
            # Selecciona archivo Excel
            excel_path = self._select_excel_file()
            if not excel_path:
                self.ui.print_warning("No se seleccionó ningún archivo")
                return
            
            self.ui.print_info(f"Archivo seleccionado: {excel_path}")
            
            # Carga el Excel
            df = self.excel_service.load_patients(excel_path)
            self.ui.print_info(f"Total de registros: {len(df)}")
            
            # Prepara columnas necesarias
            df = self._prepare_dataframe(df)
            
            # Obtiene credenciales
            location, username, password = self.ui.get_credentials()
            
            # Procesa pacientes
            self.ui.print_info("Iniciando proceso de completado de datos...")
            df_updated = self._process_patients(df, location, username, password)
            
            # Actualiza el Excel
            self._update_excel(excel_path, df_updated)
            
            self.ui.print_success("Proceso completado exitosamente")
            
        except KeyboardInterrupt:
            self.ui.print_warning("\nProceso interrumpido por el usuario")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error en script: {e}", exc_info=True)
            self.ui.print_error(f"Error: {e}")
            sys.exit(1)
    
    def _select_excel_file(self) -> Optional[str]:
        """
        Abre diálogo para seleccionar archivo Excel.
        
        Returns:
            Ruta del archivo seleccionado o None
        """
        root = Tk()
        root.withdraw()  # Oculta la ventana principal
        
        file_path = filedialog.askopenfilename(
            title="Selecciona el archivo Excel a procesar",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")],
            initialdir=str(settings.BASE_DIR)
        )
        
        root.destroy()
        return file_path if file_path else None
    
    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara el DataFrame con las columnas necesarias.
        
        Args:
            df: DataFrame original
            
        Returns:
            DataFrame preparado
        """
        # Normaliza nombres de columnas
        df.columns = df.columns.str.strip().str.upper()
        
        # Asegura columnas de texto
        for col in ["SEXO", "CONSEJERIA", "TIPO DE ATENCIÓN", "DÉFICIT"]:
            if col not in df.columns:
                df[col] = None
            else:
                df[col] = df[col].astype("object")
        
        # Maneja variantes de nombres de columnas
        if "TIPO DE ATENCIÓN" not in df.columns and "TIPO DE ATENCION" in df.columns:
            df["TIPO DE ATENCIÓN"] = df["TIPO DE ATENCION"]
        
        if "DÉFICIT" not in df.columns and "DEFICIT" in df.columns:
            df["DÉFICIT"] = df["DEFICIT"]
        
        return df
    
    def _process_patients(
        self, 
        df: pd.DataFrame,
        location: str,
        username: str,
        password: str
    ) -> pd.DataFrame:
        """
        Procesa cada paciente para completar datos faltantes.
        
        Args:
            df: DataFrame con pacientes
            location: Ubicación
            username: Usuario
            password: Contraseña
            
        Returns:
            DataFrame actualizado
        """
        # Identifica columna de RUN
        run_col = None
        for col_name in ["RUN", "RUT"]:
            if col_name in df.columns:
                run_col = col_name
                break
        
        if not run_col:
            raise ValueError("No se encontró columna RUN o RUT en el archivo")
        
        with WebScraperService(headless=settings.HEADLESS) as scraper:
            # Login
            scraper.login(location, username, password)
            
            # Navega a agregar documentos
            scraper.navigate_to_menu("Box", "Agregar documentos")
            
            # Procesa cada paciente
            total = len(df)
            for idx, row in df.iterrows():
                run = str(row.get(run_col, "")).strip() if not pd.isna(row.get(run_col)) else ""
                nombre = str(row.get("NOMBRE", "")).strip() if not pd.isna(row.get("NOMBRE")) else ""
                
                if not run:
                    continue
                
                # Muestra progreso
                self.ui.print_header(f"Paciente {idx + 1}/{total}")
                self.ui.print_info(f"RUN: {run}")
                self.ui.print_info(f"Nombre: {nombre}")
                
                # Verifica si ya es NSP para saltar anamnesis
                tipo_actual = row.get("TIPO DE ATENCIÓN", "")
                if not is_empty(tipo_actual) and normalize_text(tipo_actual) == "NSP":
                    self.ui.print_warning("Tipo = NSP, omitiendo análisis de anamnesis")
                    self.ui.pause_or_timeout(3)
                    continue
                
                try:
                    # Busca el paciente
                    if not self._search_patient(scraper, run):
                        self.ui.print_warning("Paciente no encontrado")
                        self.ui.pause_or_timeout(3)
                        continue
                    
                    # Extrae información general (SEXO, CONSEJERIA)
                    patient_data = self._extract_patient_data(scraper, row)
                    
                    # Actualiza DataFrame con datos generales
                    for key, value in patient_data.items():
                        if key in df.columns and not is_empty(value):
                            if is_empty(df.at[idx, key]):
                                df.at[idx, key] = value
                                self.ui.print_success(f"  → {key}: {value}")
                    
                    # Procesa anamnesis para TIPO DE ATENCIÓN y DÉFICIT
                    fecha = row.get("FECHA")
                    if fecha and not is_empty(fecha):
                        # Intenta obtener anamnesis con timeout corto
                        anamnesis_data = self._process_anamnesis_quick(scraper, fecha)
                        
                        if anamnesis_data:
                            # Actualiza TIPO DE ATENCIÓN
                            if "TIPO DE ATENCIÓN" in anamnesis_data:
                                if is_empty(df.at[idx, "TIPO DE ATENCIÓN"]):
                                    df.at[idx, "TIPO DE ATENCIÓN"] = anamnesis_data["TIPO DE ATENCIÓN"]
                                    self.ui.print_success(f"  → TIPO DE ATENCIÓN: {anamnesis_data['TIPO DE ATENCIÓN']}")
                            
                            # Actualiza DÉFICIT (solo si no es NSP)
                            if "DÉFICIT" in anamnesis_data:
                                if is_empty(df.at[idx, "DÉFICIT"]):
                                    df.at[idx, "DÉFICIT"] = anamnesis_data["DÉFICIT"]
                                    self.ui.print_success(f"  → DÉFICIT: {anamnesis_data['DÉFICIT']}")
                        else:
                            self.ui.print_warning("  → No se pudo analizar anamnesis (no disponible)")
                    else:
                        self.ui.print_warning("  → Sin fecha, omitiendo análisis de anamnesis")
                    
                except Exception as e:
                    logger.error(f"Error procesando paciente {run}: {e}")
                    self.ui.print_error(f"Error: {e}")
                
                # Pausa entre pacientes
                self.ui.pause_or_timeout(5)
        
        return df
    
    def _search_patient(self, scraper: WebScraperService, run: str) -> bool:
        """
        Busca un paciente por RUN.
        
        Args:
            scraper: Servicio de scraping
            run: RUN del paciente
            
        Returns:
            True si se encontró el paciente
        """
        try:
            # Espera y limpia loader/modal
            scraper.wait_for_loader()
            scraper.close_modal_if_present()
            
            # Busca el campo de RUT
            search_input = scraper.wait.until(
                EC.presence_of_element_located((By.ID, "patientRut"))
            )
            search_input.clear()
            search_input.send_keys(run, Keys.ENTER)
            
            time.sleep(2)
            
            # Busca "Seguimiento"
            popover_input = scraper.wait.until(
                EC.visibility_of_element_located((By.ID, "popover-input"))
            )
            popover_input.clear()
            popover_input.send_keys("Seguimiento")
            
            search_button = scraper.driver.find_element(By.ID, "buttonSearch")
            search_button.click()
            
            time.sleep(2)
            return True
            
        except TimeoutException:
            return False
    
    def _extract_patient_data(
        self, 
        scraper: WebScraperService, 
        row: pd.Series
    ) -> dict:
        """
        Extrae datos del paciente desde la ficha.
        
        Args:
            scraper: Servicio de scraping
            row: Fila del DataFrame con datos del paciente
            
        Returns:
            Diccionario con datos extraídos
        """
        data = {}
        
        try:
            # Busca todas las tablas en la página
            tables = scraper.driver.find_elements(By.XPATH, "//table")
            
            edad_str = ""
            for table in tables:
                for table_row in table.find_elements(By.TAG_NAME, "tr"):
                    ths = table_row.find_elements(By.TAG_NAME, "th")
                    tds = table_row.find_elements(By.TAG_NAME, "td")
                    
                    if not ths or not tds:
                        continue
                    
                    header = ths[0].text.strip().lower()
                    value = tds[0].text.strip()
                    
                    # Extrae edad
                    if "edad" in header and not edad_str:
                        edad_str = value
                    
                    # Extrae sexo
                    if "sexo" in header and "biológico" in header:
                        sexo = self.patient_service.parse_sex(value)
                        if sexo:
                            data["SEXO"] = sexo.value
            
            # Determina consejería LME si corresponde
            if edad_str and self.patient_service.should_assign_lme(edad_str):
                data["CONSEJERIA"] = "LME"
            
        except Exception as e:
            logger.error(f"Error extrayendo datos del paciente: {e}")
        
        return data
    
    def _process_anamnesis_quick(self, scraper: WebScraperService, fecha) -> Dict[str, str]:
        """
        Procesa la sección de anamnesis con timeout reducido.
        
        Args:
            scraper: Servicio de scraping
            fecha: Fecha del registro
            
        Returns:
            Diccionario con tipo de atención y déficit detectados
        """
        data = {}
        
        try:
            # Convierte fecha si es necesario
            if isinstance(fecha, str):
                fecha_dt = pd.to_datetime(fecha, dayfirst=True)
            else:
                fecha_dt = fecha
            
            fecha_str = fecha_dt.strftime("%d-%m-%Y")
            
            # Busca el nodo de la fecha en el árbol (timeout corto)
            scraper.wait_for_loader()
            
            # Intenta encontrar la fecha con timeout reducido
            from selenium.webdriver.support.ui import WebDriverWait
            wait_short = WebDriverWait(scraper.driver, 3)  # 3 segundos máximo
            
            fecha_xpath = f"//div[contains(@class,'tree-mainText') and contains(.,'{fecha_str}')]"
            
            try:
                fecha_elem = wait_short.until(
                    EC.presence_of_element_located((By.XPATH, fecha_xpath))
                )
            except TimeoutException:
                logger.debug(f"Fecha {fecha_str} no encontrada en el árbol")
                return data
            
            # Expande si es necesario
            try:
                parent_span = fecha_elem.find_element(
                    By.XPATH, "./ancestor::span[contains(@class,'rct-text')]"
                )
                expand_btn = parent_span.find_element(
                    By.XPATH, ".//button[contains(@class,'rct-collapse')]"
                )
                expand_btn.click()
                time.sleep(0.5)
            except:
                pass
            
            # Click en la fecha
            fecha_elem.click()
            time.sleep(0.5)
            
            # Busca Anamnesis (timeout corto)
            anamnesis_xpath = "//div[contains(@class,'tree-mainText') and normalize-space(.)='Anamnesis']"
            
            try:
                anamnesis_elem = wait_short.until(
                    EC.presence_of_element_located((By.XPATH, anamnesis_xpath))
                )
            except TimeoutException:
                logger.debug("Anamnesis no encontrada")
                return data
            
            # Expande anamnesis si es necesario
            try:
                parent_span_anam = anamnesis_elem.find_element(
                    By.XPATH, "./ancestor::span[contains(@class,'rct-text')]"
                )
                expand_btn_anam = parent_span_anam.find_element(
                    By.XPATH, ".//button[contains(@class,'rct-collapse')]"
                )
                expand_btn_anam.click()
                time.sleep(0.5)
            except:
                pass
            
            # Click en Anamnesis
            anamnesis_elem.click()
            time.sleep(0.5)
            
            # Extrae textos de anamnesis
            text_elements = scraper.driver.find_elements(
                By.XPATH, 
                "//div[contains(@class,'tree-secondaryText') and contains(@class,'col-sm-12')]"
            )
            
            motivo_consulta = ""
            historial = ""
            
            for elem in text_elements:
                text = elem.text.strip()
                if text:
                    text_upper = normalize_text(text)
                    if text_upper.startswith("MOTIVO DE CONSULTA"):
                        motivo_consulta = text
                    elif text_upper.startswith("HISTORIAL DE LA ENFERMEDAD") or text_upper.startswith("HISTORIA DE LA ENFERMEDAD"):
                        historial = text
            
            # Combina textos
            combined_text = f"{motivo_consulta}\n{historial}".strip()
            
            # Analiza el texto para detectar TIPO y DÉFICIT
            if combined_text:
                tipo, deficit = self.patient_service.analyze_anamnesis(combined_text)
                
                if tipo:
                    data["TIPO DE ATENCIÓN"] = tipo.value
                
                # Solo añade déficit si el tipo no es NSP
                if deficit and tipo != TipoAtencion.NSP:
                    data["DÉFICIT"] = deficit
            
        except Exception as e:
            logger.error(f"Error procesando anamnesis: {e}")
        
        return data
    
    def _update_excel(self, excel_path: str, df: pd.DataFrame) -> None:
        """
        Actualiza el archivo Excel con los datos completados.
        
        Args:
            excel_path: Ruta del archivo Excel
            df: DataFrame actualizado
        """
        try:
            # Define columnas a actualizar
            column_mapping = {
                "SEXO": ["SEXO"],
                "CONSEJERIA": ["CONSEJERIA", "CONSEJERÍA"],
                "TIPO DE ATENCIÓN": ["TIPO DE ATENCIÓN", "TIPO DE ATENCION"],
                "DÉFICIT": ["DÉFICIT", "DEFICIT"]
            }
            
            # Actualiza el Excel in-place
            stats = self.excel_service.update_excel_inplace(
                excel_path, 
                df, 
                column_mapping,
                only_empty=True
            )
            
            self.ui.print_success("\nResumen de actualización:")
            for col, count in stats.items():
                self.ui.print_info(f"  {col}: {count} celdas actualizadas")
            
            self.ui.print_success(f"\nArchivo actualizado: {excel_path}")
            
        except PermissionError:
            self.ui.print_error("No se pudo guardar el Excel. ¿Está abierto? Ciérralo e inténtalo de nuevo.")
        except Exception as e:
            self.ui.print_error(f"Error actualizando Excel: {e}")
            raise


def main():
    """Punto de entrada del script."""
    script = FillDataScript()
    script.run()


if __name__ == "__main__":
    main()