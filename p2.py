# p2.py
# Script: Agregar documentos / Anamnesis — usa funciones compartidas.

from colorama import init
init(autoreset=True)

import pandas as pd
import re
import time
import datetime
import sys
import os

try:
    import msvcrt
except ImportError:
    msvcrt = None

from tkinter import Tk, filedialog
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from funciones import (
    iniciar_sesion,
    esperar_loader_y_modal,
    normalize,
    norm_simple,
    is_empty,
    edad_menor_4_meses,
    detect_tipo_y_deficit,
    normalizar_tipo_excel,
    crear_driver_silencioso,
    actualizar_excel_inplace,
)

def color_text(text, color="cyan"):
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def pause_or_timeout(seconds=7):
    msg = "Presiona ENTER para continuar (auto en {}s)..."

    def print_inline(text):
        print("\r" + text + " " * 20, end="", flush=True)

    print_inline(color_text(msg.format(seconds), "yellow"))

    if msvcrt:
        start = time.time()
        last = seconds
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    print("\r" + " " * 80, end="\r")
                    print(color_text("Continuando...", "cyan"))
                    return
            elapsed = time.time() - start
            remaining = max(0, seconds - int(elapsed))
            if remaining != last:
                print_inline(color_text(msg.format(remaining), "yellow"))
                last = remaining
            if elapsed >= seconds:
                print("\r" + " " * 80, end="\r")
                print(color_text("Tiempo agotado. Continuando automáticamente...", "yellow"))
                return
            time.sleep(0.05)
    else:
        for s in range(seconds, 0, -1):
            print_inline(color_text(msg.format(s), "yellow"))
            time.sleep(1)
        print("\r" + " " * 80, end="\r")
        print(color_text("Continuando...", "cyan"))

def abrir_fecha_y_anamnesis(driver, wait, fecha_dt):
    try:
        esperar_loader_y_modal(driver, wait)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "recordTree")))
    except TimeoutException:
        return False, False, ""

    fecha_str = fecha_dt.strftime("%d-%m-%Y")
    xpath_fecha = f"//div[contains(@class,'tree-mainText') and contains(.,'{fecha_str}')]"
    try:
        fecha_elem = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath_fecha)))
    except TimeoutException:
        return False, False, ""

    try:
        span_rct_text = fecha_elem.find_element(By.XPATH, "./ancestor::span[contains(@class,'rct-text')]")
        btn_expand = span_rct_text.find_element(By.XPATH, ".//button[contains(@class,'rct-collapse')]")
        btn_expand.click()
        time.sleep(1)
    except:
        pass

    try:
        fecha_elem.click()
        time.sleep(1)
    except:
        pass

    xpath_anam = "//div[contains(@class,'tree-mainText') and normalize-space(.)='Anamnesis']"
    try:
        anam_elem = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath_anam)))
    except TimeoutException:
        return True, False, ""

    try:
        span_rct_text_anam = anam_elem.find_element(By.XPATH, "./ancestor::span[contains(@class,'rct-text')]")
        btn_expand_anam = span_rct_text_anam.find_element(By.XPATH, ".//button[contains(@class,'rct-collapse')]")
        btn_expand_anam.click()
        time.sleep(1)
    except:
        pass

    try:
        anam_elem.click()
        time.sleep(1)
    except:
        pass

    motivo = ""
    historial = ""
    try:
        textos = driver.find_elements(By.XPATH, "//div[contains(@class,'tree-secondaryText') and contains(@class,'col-sm-12')]")
        for t in textos:
            txt = (t.text or "").strip()
            up = normalize(txt)
            if up.startswith("MOTIVO DE CONSULTA"):
                motivo = txt
            if up.startswith("HISTORIAL DE LA ENFERMEDAD") or up.startswith("HISTORIA DE LA ENFERMEDAD"):
                historial = txt
    except:
        pass

    combinado = (motivo + "\n" + historial).strip()
    return True, True, combinado

# ==================== Selección de archivo ====================

Tk().withdraw()
excel_path = filedialog.askopenfilename(
    title="Selecciona tu archivo Excel",
    filetypes=[("Archivos Excel", "*.xlsx *.xls")]
)
if not excel_path:
    print("No seleccionaste ningún archivo. Saliendo.")
    sys.exit(0)

df = pd.read_excel(excel_path)
df.columns = df.columns.str.strip().str.upper()

# Asegura columnas de texto (evita FutureWarning)
for c in ["SEXO", "CONSEJERIA", "TIPO DE ATENCIÓN", "TIPO DE ATENCION", "DÉFICIT", "DEFICIT"]:
    if c in df.columns:
        df[c] = df[c].astype("object")

# Columnas que p2 puede completar (crear si no existen en df)
if "SEXO" not in df.columns:
    df["SEXO"] = None
if "CONSEJERIA" not in df.columns:
    df["CONSEJERIA"] = ""
# Mantén ambas variantes de TIPO/DÉFICIT en df para escritura canónica
if "TIPO DE ATENCIÓN" not in df.columns:
    if "TIPO DE ATENCION" in df.columns:
        df["TIPO DE ATENCIÓN"] = df["TIPO DE ATENCION"]
    else:
        df["TIPO DE ATENCIÓN"] = ""
if "DÉFICIT" not in df.columns:
    if "DEFICIT" in df.columns:
        df["DÉFICIT"] = df["DEFICIT"]
    else:
        df["DÉFICIT"] = ""

# RUN/RUT
if "RUN" in df.columns:
    run_col = "RUN"
elif "RUT" in df.columns:
    run_col = "RUT"
else:
    print("No se encontró la columna RUN ni RUT en el archivo.")
    print("Columnas encontradas:", df.columns.tolist())
    sys.exit(0)

# ==================== Selenium (silencioso) ====================

driver = crear_driver_silencioso()
wait = WebDriverWait(driver, 20)

# Login compartido
iniciar_sesion(driver)

# Navegar: Box > Agregar documentos
esperar_loader_y_modal(driver, wait)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
wait.until(EC.element_to_be_clickable((By.ID, "navbar-main-menu"))).click()
time.sleep(1)
esperar_loader_y_modal(driver, wait)
wait.until(EC.element_to_be_clickable((By.XPATH, "//li[.//span[text()='Box']]"))).click()
time.sleep(1)
esperar_loader_y_modal(driver, wait)
wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Agregar documentos']"))).click()
time.sleep(2)

# ==================== Proceso por paciente ====================

from selenium.webdriver.common.keys import Keys

for idx, row in df.iterrows():
    run = "" if pd.isna(row.get(run_col)) else str(row.get(run_col)).strip()
    nombre = "" if pd.isna(row.get("NOMBRE")) else str(row.get("NOMBRE")).strip()
    fecha_val = row.get("FECHA")
    if not run:
        continue

    # FECHA (para árbol/Anamnesis; si falta, se omite análisis de Anamnesis)
    if isinstance(fecha_val, (pd.Timestamp, datetime.datetime)):
        fecha_dt = fecha_val
    else:
        try:
            fecha_dt = pd.to_datetime(fecha_val, dayfirst=True) if fecha_val else None
        except:
            fecha_dt = None

    # Normaliza TIPO si viene en Excel, pero NO sobreescribe si ya existe (relleno solo si vacío)
    tipo_excel = row.get("TIPO DE ATENCIÓN", "")
    tipo_norm = normalizar_tipo_excel(tipo_excel)
    if tipo_norm and is_empty(df.at[idx, "TIPO DE ATENCIÓN"]):
        df.at[idx, "TIPO DE ATENCIÓN"] = tipo_norm

    print(color_text(f"\n--- Buscando paciente ---", "yellow"))
    print(color_text(f"RUN: {run}", "cyan"))
    print(color_text(f"NOMBRE: {nombre}", "green"))
    print(color_text(f"FECHA: {(fecha_dt.strftime('%d-%m-%Y') if fecha_dt else 'sin fecha')}", "yellow"))
    if not is_empty(df.at[idx, "TIPO DE ATENCIÓN"]):
        print(color_text(f"TIPO (normalizado): {df.at[idx, 'TIPO DE ATENCIÓN']}", "cyan"))

    # Buscar RUN
    esperar_loader_y_modal(driver, wait)
    try:
        search_input = wait.until(EC.presence_of_element_located((By.ID, "patientRut")))
        search_input.clear()
        search_input.send_keys(run, Keys.ENTER)
    except:
        print(color_text(f"[{idx}] {run} → No se pudo ingresar RUN en el buscador.", "red"))
        pause_or_timeout(7)
        continue

    # Seguimiento
    try:
        pop_in = wait.until(EC.visibility_of_element_located((By.ID, "popover-input")))
        pop_in.clear()
        pop_in.send_keys("Seguimiento")
        driver.find_element(By.ID, "buttonSearch").click()
        time.sleep(2)
    except:
        print(color_text(f"[{idx}] {run} → No se pudo acceder al paciente (Seguimiento).", "red"))
        pause_or_timeout(7)
        continue

    # EDAD / SEXO (ficha general)
    esperar_loader_y_modal(driver, wait)
    try:
        tablas = driver.find_elements(By.XPATH, "//table")
        edad_str = ""
        sexo_val_actual = df.at[idx, "SEXO"]

        for tabla in tablas:
            for fila in tabla.find_elements(By.TAG_NAME, "tr"):
                ths = fila.find_elements(By.TAG_NAME, "th")
                tds = fila.find_elements(By.TAG_NAME, "td")
                if not ths or not tds:
                    continue
                header = ths[0].text.strip()
                header_norm = norm_simple(header)
                value = (tds[0].text or "").strip()

                if not edad_str and "edad" in header_norm:
                    edad_str = value

                if is_empty(sexo_val_actual) and ("sexo" in header_norm and "biologico" in header_norm):
                    vr = normalize(value)
                    if "HOMBRE" in vr or "MASCULIN" in vr:
                        sexo_val_actual = "MASCULINO"
                    elif "MUJER" in vr or "FEMENIN" in vr:
                        sexo_val_actual = "FEMENINO"

        # CONSEJERÍA = LME solo si está vacío y corresponde
        if edad_str and edad_menor_4_meses(edad_str) and is_empty(df.at[idx, "CONSEJERIA"]):
            df.at[idx, "CONSEJERIA"] = "LME"
            print(color_text(f"[{idx}] {run} → CONSEJERÍA: LME (edad: {edad_str})", "green"))
        else:
            print(color_text(f"[{idx}] {run} → Edad: {edad_str}", "cyan"))

        # SEXO: solo si estaba vacío
        if not is_empty(sexo_val_actual) and is_empty(df.at[idx, "SEXO"]):
            df.at[idx, "SEXO"] = sexo_val_actual
            print(color_text(f"[{idx}] {run} → SEXO: {sexo_val_actual}", "green"))
        elif is_empty(sexo_val_actual):
            print(color_text(f"[{idx}] {run} → SEXO no encontrado", "yellow"))

    except:
        print(color_text(f"[{idx}] {run} → No se pudo leer ficha general (edad/sexo).", "yellow"))

    # Si TIPO = NSP → omite Anamnesis y Déficit
    tipo_final_pre = df.at[idx, "TIPO DE ATENCIÓN"] if not is_empty(df.at[idx, "TIPO DE ATENCIÓN"]) else ""
    if normalize(tipo_final_pre) == "NSP":
        print(color_text(f"[{idx}] {run} → TIPO = NSP. Se omite Anamnesis y DÉFICIT.", "yellow"))
        pause_or_timeout(7)
        continue

    # Sin fecha en Excel → no intentamos Anamnesis
    if not fecha_dt:
        print(color_text(f"[{idx}] {run} → Sin fecha en Excel. Se omite Anamnesis.", "yellow"))
        print(color_text(f"[{idx}] {run} → No fue posible analizar Anamnesis para TIPO/DÉFICIT", "yellow"))
        pause_or_timeout(7)
        continue

    # Ir a fecha y Anamnesis
    from_date, from_anam, texto_anam = abrir_fecha_y_anamnesis(driver, wait, fecha_dt)
    if not from_date:
        print(color_text(f"[{idx}] {run} → Fecha {fecha_dt.strftime('%d-%m-%Y')} no disponible en el árbol. Se omite Anamnesis.", "yellow"))
        print(color_text(f"[{idx}] {run} → No fue posible analizar Anamnesis para TIPO/DÉFICIT", "yellow"))
        pause_or_timeout(7)
        continue

    if from_date and not from_anam:
        print(color_text(f"[{idx}] {run} → Sección 'Anamnesis' no disponible. Se omite análisis.", "yellow"))
        print(color_text(f"[{idx}] {run} → No fue posible analizar Anamnesis para TIPO/DÉFICIT", "yellow"))
        pause_or_timeout(7)
        continue

    if not texto_anam:
        print(color_text(f"[{idx}] {run} → Texto de Anamnesis vacío. No fue posible analizar TIPO/DÉFICIT.", "yellow"))
        pause_or_timeout(7)
        continue

    # Analiza Anamnesis → TIPO/DÉFICIT (solo si estaban vacíos)
    tipo_detect, deficit_detect = detect_tipo_y_deficit(texto_anam)

    if tipo_detect and is_empty(df.at[idx, "TIPO DE ATENCIÓN"]):
        df.at[idx, "TIPO DE ATENCIÓN"] = tipo_detect
        print(color_text(f"[{idx}] {run} → TIPO (Anamnesis): {tipo_detect}", "green"))

    if tipo_detect and normalize(tipo_detect) == "NSP":
        print(color_text(f"[{idx}] {run} → TIPO = NSP detectado en Anamnesis. Se omite DÉFICIT.", "yellow"))
    else:
        if deficit_detect and is_empty(df.at[idx, "DÉFICIT"]):
            df.at[idx, "DÉFICIT"] = deficit_detect
            print(color_text(f"[{idx}] {run} → DÉFICIT (Anamnesis): {deficit_detect}", "green"))
        else:
            print(color_text(f"[{idx}] {run} → DÉFICIT no detectado o ya estaba informado", "yellow"))

    pause_or_timeout(7)

# ==================== Escritura IN PLACE ====================

# Mapeo de columnas (canónicas -> alias aceptados en el Excel)
columnas_objetivo = {
    "SEXO": ["SEXO"],
    "CONSEJERIA": ["CONSEJERIA"],
    "TIPO DE ATENCIÓN": ["TIPO DE ATENCIÓN", "TIPO DE ATENCION"],
    "DÉFICIT": ["DÉFICIT", "DEFICIT"],
}

try:
    stats = actualizar_excel_inplace(excel_path, df, columnas_objetivo, only_if_empty=True)
    print(color_text("\nActualización IN PLACE completada:", "green"))
    for k, v in stats.items():
        print(color_text(f"- {k}: {v} celdas escritas", "cyan"))
    print(color_text(f"Archivo actualizado: {excel_path}", "green"))
except PermissionError:
    print(color_text("\nNo se pudo guardar el Excel. ¿Está abierto? Ciérralo e inténtalo de nuevo.", "red"))
except Exception as e:
    print(color_text(f"\nError al actualizar el Excel: {e}", "red"))

# Cierra navegador
driver.quit()