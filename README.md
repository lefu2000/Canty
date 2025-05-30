SCRIPT DE AUTOMATIZACION DE EQUIPOS EN SECURECRT

EXPLICACIÓN DEL PROCESO

La presente documentaciòn da como conocimiento la explicación del proceso analizada para la programación por VBScript para la herramienta de SecureCRT, también se puede aplicar Python ya que tiene compatibilidad hasta la versión 3.11 

1. Extracción de configuraciones de los equipos:

1.1 Inicio automático de sesiones: SecureCRT permite programar sesiones para que se inicien automáticamente a intervalos regulares. Puedes configurar esto utilizando el programador de tareas de Windows o herramientas similares en otros sistemas operativos.

1.2 Comandos automáticos: Dentro de SecureCRT, puedes crear scripts (en VBScript, JScript, Python, etc.) que se ejecuten automáticamente al iniciar una sesión. Estos scripts pueden contener los comandos necesarios para extraer la información de configuración de los equipos.

1.3 Guardado de comandos en un archivo: Los scripts de SecureCRT pueden guardar la salida de los comandos en archivos de texto. Puedes especificar la ruta y el nombre del archivo en el script.

2. Almacenamiento de los archivos en una base de datos:
Base de datos: Necesitarás una base de datos para almacenar la información de configuración. Puedes utilizar MySQL, PostgreSQL, SQL Server u otra base de datos de tu preferencia.
Script de importación: Deberás crear un script (en Python, por ejemplo) que:
Lea los archivos de configuración generados por SecureCRT.
Se conecta a la base de datos.
Inserte la información en las tablas correspondientes
Página Web

3. Elaborar una Página Web que interactúe con la base de datos para leer la información almacenada
Para lograr la automatización que describes, combinando la extracción de configuraciones de equipos, el almacenamiento en una base de datos y utilizando SecureCRT y SecureFX, te propongo el siguiente enfoque:.

Flujo general:

a. Programación de sesiones: Guardar lista de enrutadores a buscar en un archivo CVS teniendo en cuenta principalmente los acrónimos de los equipo, ip, proveedor, marca

b. Scripts de SecureCRT: Crea scripts en SecureCRT que:
Lea un archivo CSV - Lista Enrutadores
Se conecten a los equipos.
Ejecuten los comandos para extraer la configuración.
Guarden la salida de los comandos en archivos de texto.

c. Script de importación: Desarrolla un script que:
Lea los archivos de texto generados por SecureCRT.
Extraiga la información relevante.
Se conecta a la base de datos.
Inserte la información en las tablas.

d. Automatización del script de importación: Programa el script de importación para que se ejecute periódicamente, por ejemplo, después de que SecureCRT haya terminado de extraer la información de los equipos.
