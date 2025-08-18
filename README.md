# Sayen · Rayen APS Automation

Automatiza dos tareas del sistema clínico Rayen APS:
- p1.py: Obtiene “Pacientes citados” en un rango de días y exporta un Excel.
- p2.py: Completa datos faltantes (SEXO, CONSEJERÍA, TIPO/DÉFICIT) leyendo un Excel existente.
- p0.py: Interfaz gráfica para guardar credenciales (.env) y lanzar p1/p2 con un click.
- funciones.py: Utilidades compartidas (login, normalización, driver silencioso, etc.).


## Requisitos

- Python 3.10 o superior
- Google Chrome y ChromeDriver compatibles (recomendado mantener Chrome actualizado)
- Paquetes Python:
  - selenium
  - pandas
  - openpyxl
  - colorama
  - python-dotenv (opcional, para cargar .env automáticamente)

Instala dependencias:
```bash
pip install -r requirements.txt
```

Sugerido (entorno virtual):
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```


## Configuración de credenciales (.env)

Crea un archivo `.env` en la raíz del proyecto con:
```dotenv
RAYEN_LOCATION=cesfamaguirre
RAYEN_USERNAME=TU_USUARIO
RAYEN_PASSWORD=TU_PASSWORD
# Opcional: HEADLESS=true para ejecutar sin ventana de navegador
HEADLESS=false
```

## Uso

### GUI (p0.py)
- Ejecuta:
  ```bash
  python p0.py
  ```
- Ingresa ubicación, usuario y contraseña.
- Marca “Headless” si quieres ocultar la ventana del navegador.
- Guarda credenciales (se crea/actualiza `.env`).
- Botón “Obtener RUTS (p1)”: lanza p1 en una consola nueva. p1 te pedirá Año/Mes/Rango de días.
- Botón “Rellenar Datos (p2)”: lanza p2 en una consola nueva. p2 te pedirá seleccionar el Excel a completar.

### p1.py (Pacientes citados)
- Ejecuta:
  ```bash
  python p1.py
  ```
- Ingresa:
  - Año (ej: 2025)
  - Mes (1–12)
  - Día inicio y fin (mismo mes)
- Exporta: `pacientes_citados_YYYY_MM_dd_dd.xlsx`
- Alterna colores en FECHA para distinguir bloques.

Columnas exportadas (orden):
- FECHA, VACIO1, VACIO2, SECTOR, NOMBRE, RUN, TIPO DE ATENCIÓN, EDAD, DÉFICIT, SEXO

Reglas claves:
- NOMBRE: se limpia removiendo cualquier “(…)”.
- TIPO DE ATENCIÓN: si el estado contiene “no se present…”, marca NSP.
- EDAD: clasifica rangos a partir de texto.
- Fines de semana: se omiten.

### p2.py (Rellenar datos desde Excel)
- Ejecuta:
  ```bash
  python p2.py
  ```
- Selecciona tu Excel. p2 lee cada fila y:
  - Completa SEXO BIOLÓGICO desde la ficha general.
  - Marca CONSEJERÍA=LME si la edad < 4 meses.
  - Si TIPO=NSP, omite Anamnesis y DÉFICIT.
  - Si no es NSP y la fila tiene FECHA:
    - Navega el árbol por fecha, abre “Anamnesis” y combina “Motivo de consulta” + “Historial/Historia…”.
    - Detecta TIPO y DÉFICIT desde ese texto.
  - Espera ENTER con cuenta regresiva (7→1) entre pacientes; si no presionas, continúa solo.

Columnas esperadas en el Excel de entrada:
- Necesarias: RUN o RUT, FECHA (si quieres navegar Anamnesis), NOMBRE (opcional)
- Opcionales (si faltan, se crean): SEXO, CONSEJERIA, TIPO DE ATENCIÓN (o TIPO DE ATENCION), DÉFICIT (o DEFICIT)

Normalizaciones:
- p2 normaliza nombres de columnas a mayúsculas y acepta variantes con/sin tildes.
- Nunca escribe “nan” al Excel (los vacíos quedan en blanco).


## Reglas de negocio (resumen)

- Limpieza de nombres: se eliminan bloques “(…)” (ASCII o full-width).
- Clasificación de edad:
  - Menor de 7 meses, 7–11, 12–17, 18–23, 24–47, 48–59, 60+ meses.
- TIPOS_MAP (mapeo sin tildes ni case):
  - ATENCION PRESENCIAL → ASISTE
  - NO SE PRESENT… → NSP
  - LLAMADO TELEFONICO EFECTIVO → LLAMADO TELEFÓNICO EFECTIVO
  - …inefectivo/efectiva/videollamada/menajería/V.D.I/egreso administrativo
- DÉFICIT:
  - Se detecta desde Anamnesis usando palabras clave: REZAGO, RIESGO, RETRASO, RBPS, NANEAS.
  - Si TIPO = NSP, no se evalúa DÉFICIT.
- CONSEJERÍA:
  - LME si edad < 4 meses (desde ficha general).


## Driver silencioso y headless

- `funciones.crear_driver_silencioso()` reduce al mínimo el ruido de logs (Chrome/Driver).
- HEADLESS=true en `.env` para ejecutar sin mostrar el navegador.


## Estructura del proyecto

```
.
├─ p0.py                # GUI: guarda .env y lanza p1/p2
├─ p1.py                # Pacientes citados → Excel
├─ p2.py                # Completar datos en Excel (Edad/Sexo/Tipo/Déficit)
├─ funciones.py         # Utilidades compartidas
├─ requirements.txt
├─ .env.example         # Modelo de credenciales
├─ .env                 # Tus credenciales (NO subir)
└─ README.md
```


## Troubleshooting

- Mensajes de Chrome/Driver (sandbox 0x5, DevTools listening, GCM): informativos. Con el driver “silencioso” se reducen. Ejecuta la terminal como administrador si persisten.
- Versión Chrome/Chromedriver: si falla la inicialización del driver, actualiza Chrome y el driver a la misma versión.
- Colores en consola: algunos entornos (PowerShell/Consolas antiguas) pueden no renderizar ANSI. VS Code Terminal funciona bien.
- Pandas FutureWarning por tipos: ya se castea a `object` al inicio para columnas de texto (SEXO, CONSEJERIA, TIPO, DÉFICIT).
- Tkinter (p0.py): viene con Python en Windows/macOS. En Linux puede requerir: `sudo apt-get install python3-tk`.
- Fecha en árbol (p2): si el formato en Rayen difiere (ej. dd/mm/yyyy), ajusta el contains en `abrir_fecha_y_anamnesis`.


## Seguridad

- `.env` está en `.gitignore`. No subas credenciales.
- Puedes usar variables de entorno del sistema en lugar de `.env`.
- Cambia las credenciales periódicamente y no las compartas.


## Licencia

Uso interno. Asegúrate de tener permisos para automatizar Rayen APS conforme a las políticas de tu organización.
