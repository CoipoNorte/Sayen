# 🏥 Sayen - Automatización Rayen APS

<div align="center">
  <img src="ico/sayen.ico" alt="Sayen Logo" width="128">
  
  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
  [![Selenium](https://img.shields.io/badge/Selenium-4.20%2B-green.svg)](https://www.selenium.dev/)
  [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
</div>

## 📝 Descripción

**Sayen** es una herramienta de automatización para el sistema clínico Rayen APS que optimiza el proceso de gestión de pacientes citados y el completado de datos faltantes en registros médicos.

### 🎯 Principales Características

- **📋 Extracción Automatizada**: Obtiene información de pacientes citados en rangos de fechas específicos
- **✏️ Completado Inteligente**: Rellena automáticamente campos faltantes (SEXO, CONSEJERÍA, TIPO DE ATENCIÓN, DÉFICIT)
- **🖥️ Interfaz Gráfica Intuitiva**: GUI moderna con CustomTkinter para configuración fácil
- **📊 Exportación a Excel**: Genera archivos Excel formateados con colores por fecha
- **🔐 Gestión Segura**: Credenciales almacenadas localmente en archivo .env
- **🚀 Modo Headless**: Opción de ejecutar sin ventana del navegador

## 🔧 Requisitos del Sistema

### Software Necesario
- **Python** 3.10 o superior
- **Google Chrome** (última versión)
- **ChromeDriver** (se descarga automáticamente con selenium-manager)
- **Sistema Operativo**: Windows 10/11 (optimizado para Windows)

### Dependencias Python
```bash
selenium>=4.20.0
pandas>=2.2.0
openpyxl>=3.1.2
colorama>=0.4.6
customtkinter>=5.2.2
python-dotenv>=1.0.1
```

## 📦 Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/sayen.git
cd sayen
```

### 2. Crear Entorno Virtual (Recomendado)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Credenciales
Crea un archivo `.env` en la raíz del proyecto:
```env
RAYEN_LOCATION=tu_centro_salud
RAYEN_USERNAME=tu_usuario
RAYEN_PASSWORD=tu_contraseña
HEADLESS=false
```

## 🚀 Uso

### Interfaz Gráfica (Recomendado)

1. **Iniciar la aplicación**:
```bash
python main.py
```

2. **Configurar credenciales** en la interfaz
3. **Guardar configuración** con el botón 💾
4. **Ejecutar scripts**:
   - 📋 **Obtener Pacientes**: Extrae pacientes citados
   - ✏️ **Completar Datos**: Rellena información faltante

### Línea de Comandos

#### Obtener Pacientes Citados
```bash
python -m src.scripts.get_patients
```
- Solicita rango de fechas
- Genera Excel con pacientes del período

#### Completar Datos Faltantes
```bash
python -m src.scripts.fill_data
```
- Abre diálogo para seleccionar Excel
- Completa campos vacíos automáticamente

### Script de Prueba
```bash
python test_connection.py
```
Verifica la conexión y login al sistema.

## 📁 Estructura del Proyecto

```
sayen/
├── 📂 src/                    # Código fuente
│   ├── 📂 config/             # Configuración y constantes
│   │   ├── settings.py        # Configuración central
│   │   └── constants.py       # Constantes del dominio
│   ├── 📂 core/               # Funcionalidades base
│   │   ├── exceptions.py      # Excepciones personalizadas
│   │   ├── logging.py         # Sistema de logging
│   │   └── utils.py           # Utilidades generales
│   ├── 📂 domain/             # Modelos de dominio
│   │   ├── models.py          # Clases de datos
│   │   └── validators.py      # Validadores
│   ├── 📂 services/           # Lógica de negocio
│   │   ├── scraper_service.py # Automatización web
│   │   ├── patient_service.py # Gestión de pacientes
│   │   └── excel_service.py   # Manejo de Excel
│   ├── 📂 scripts/            # Scripts ejecutables
│   │   ├── get_patients.py    # Obtener pacientes
│   │   └── fill_data.py       # Completar datos
│   └── 📂 ui/                 # Interfaces de usuario
│       ├── gui.py             # Interfaz gráfica
│       └── console.py         # Interfaz de consola
├── 📂 data/                   # Datos y archivos
│   ├── 📂 input/              # Excel de entrada
│   ├── 📂 output/             # Excel generados
│   └── 📂 temp/               # Archivos temporales
├── 📂 logs/                   # Archivos de log
├── 📂 ico/                    # Iconos
│   └── sayen.ico              # Icono de la aplicación
├── 📄 main.py                 # Punto de entrada GUI
├── 📄 requirements.txt        # Dependencias
├── 📄 .env                    # Credenciales (no compartir)
└── 📄 README.md               # Este archivo
```

## ⚙️ Configuración Avanzada

### Variables de Entorno (.env)

| Variable | Descripción | Ejemplo |
|----------|------------|---------|
| `RAYEN_LOCATION` | Centro de salud | `cesfamaguirre` |
| `RAYEN_USERNAME` | RUT usuario | `194322712` |
| `RAYEN_PASSWORD` | Contraseña | `********` |
| `HEADLESS` | Modo sin ventana | `true` / `false` |
| `LOG_LEVEL` | Nivel de logging | `INFO` / `DEBUG` |

### Campos que Completa Automáticamente

| Campo | Lógica de Detección |
|-------|-------------------|
| **SEXO** | Lee desde ficha del paciente (Masculino/Femenino) |
| **CONSEJERÍA** | Asigna "LME" si edad < 4 meses |
| **TIPO DE ATENCIÓN** | Analiza texto de anamnesis (Asiste, NSP, Llamado, etc.) |
| **DÉFICIT** | Detecta palabras clave (Rezago, Riesgo, Retraso, etc.) |

## 🐛 Solución de Problemas

### Error: "No module named 'src'"
```bash
# Ejecutar desde la carpeta raíz del proyecto
cd path/to/sayen
python main.py
```

### Error: "ChromeDriver version mismatch"
```bash
# Actualizar Chrome a la última versión
# Selenium 4.20+ descarga el driver automáticamente
```

### No aparece el icono en la ventana
- Verificar que existe `ico/sayen.ico`
- El archivo debe ser formato .ico válido

### El Excel no se actualiza
- Cerrar el archivo Excel antes de ejecutar
- Verificar permisos de escritura en la carpeta

### Login falla constantemente
- Verificar credenciales en .env
- Confirmar que el centro (location) es correcto
- Revisar conexión a internet

## 📊 Formato de Archivos Excel

### Columnas del Excel Generado

| Columna | Descripción |
|---------|------------|
| FECHA | Fecha de la cita |
| SECTOR | Sector del paciente |
| NOMBRE | Nombre completo |
| RUN | RUT del paciente |
| TIPO DE ATENCIÓN | Estado de la atención |
| EDAD | Rango etario |
| DÉFICIT | Déficit detectado |
| SEXO | Sexo biológico |
| CONSEJERIA | Tipo de consejería |

### Códigos de Colores
- 🟨 **Amarillo**: Días impares
- 🌸 **Rosa**: Días pares

## 🔒 Seguridad

- **Credenciales locales**: Nunca se envían a servidores externos
- **Archivo .env**: Incluido en .gitignore para evitar exposición
- **Sin telemetría**: No recopila ni envía datos de uso
- **Logs locales**: Toda la información permanece en tu equipo

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.

## 👥 Autores

- **CoipoNorte** - *Desarrollo inicial* - [GitHub](https://github.com/coiponorte)

## 🙏 Agradecimientos

- Equipo de desarrollo de Rayen APS
- Comunidad de Python y Selenium
- Colaboradores del proyecto

## 📞 Soporte

Para soporte, envía un email a: christiancaceres1398@gmail.com

---

<div align="center">
  Desarrollado con ❤️ para optimizar la gestión de salud primaria
</div>
```