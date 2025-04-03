# $language = "VBScript"
# $Interface = "1.0"

Option Explicit

' Declaración de variables globales
Dim rutaCarpetaSesiones, objFSO, objCarpeta, archivos, archivo, nombreSesion
Dim retardo, archivoLog, comandos
Dim contadorArchivos
Dim objShell
Set objShell = CreateObject("WScript.Shell")



' Configuración inicial
crt.Screen.Synchronous = False  ' Habilita modo asincrónico para evitar errores de tiempo de espera
crt.Screen.IgnoreEscape = True ' Ignora caracteres de escape para evitar problemas de conexión

Sub Main()

    ' Rutas de configuración (MODIFICAR SEGÚN NECESARIO)
    rutaCarpetaSesiones = "D:\Usuarios\lriver14\AppData\Roaming\VanDyke\Config\Sessions\Tesis - Respaldo\"
    archivoLog = "D:\Usuarios\lriver14\Documents\Log - Falla -Codigo\log-debuging.txt"
    retardo = 5  ' Retardo entre sesiones en segundos

    ' Ejecutar script1
    objShell.Run "Conect_Session.vbs", 1, True

    ' Ejecutar script2
    objShell.Run "CrearArchivoLog.vbs", 1, True

    ' Ejecutar script3
    objShell.Run "EsperarPrompt.vbs", 1, True

    ' Ejecutar script4
    objShell.Run "EsSesionValida.vbs", 1, True

    ' Ejecutar script5
    objShell.Run "ProcesarPaginacion.vbs", 1, True

    ' Ejecutar script6
    objShell.Run "RegistrarLog.vbs", 1, True


    'crt.Session.Script.Load "Conect_Session.vbs"        ' CONEXION A LOS EQUIPOS
    'crt.Session.Script.Load "CrearArchivoLog.vbs"       ' LOG PARA DEBBUGIN
    'crt.Session.Script.Load "EsperarPrompt.vbs"         ' VERIFICA PROMPT PARA CONFIRMAR CONEXION
    'crt.Session.Script.Load "EsSesionValida.vbs"        '
    'crt.Session.Script.Load "ProcesarPaginacion.vbs"    ' PROCESAR PAGINACION Y EVITAR QUE SE TRABE LA SALIDA DE INFORMACION
    'crt.Session.Script.Load "RegistrarLog.vbs"          ' 

    ' Comandos a ejecutar en cada dispositivo
    comandos = Array("show running-config")
    
    ' Inicialización de objetos
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    
        ' Verificar existencia de la carpeta
    If Not objFSO.FolderExists(rutaCarpetaSesiones) Then
        RegistrarLog archivoLog, "Error: No se encuentra la carpeta de sesiones", vbExclamation
        Exit Sub
    End If

    ' Configurar archivo de log
    CrearArchivoLog archivoLog, objFSO
    RegistrarLog archivoLog, "=== INICIO DE PROCESAMIENTO ==="
    RegistrarLog archivoLog, "Buscando sesiones en: " & rutaCarpetaSesiones
    
    ' Verificar si existe la carpeta de sesiones
    If Not objFSO.FolderExists(rutaCarpetaSesiones) Then
        RegistrarLog archivoLog, "ERROR: No se encuentra la carpeta de sesiones"
        Exit Sub
    End If
    
    ' Obtener la carpeta de sesiones
    Set objCarpeta = objFSO.GetFolder(rutaCarpetaSesiones)
    contadorArchivos = 0

    ' Procesar cada archivo .ini encontrado
    For Each archivo In objCarpeta.Files
    RegistrarLog archivoLog, "Archivo completo: '" & archivo.Name & "' | Ext: " & objFSO.GetExtensionName(archivo.Name) & " | Size: " & archivo.Size

        If EsSesionValida(archivo, objFSO) Then 

            nombreSesion = objFSO.GetBaseName(archivo.Name)
            RegistrarLog archivoLog, "Procesando archivo: " & nombreSesion
            
            ' Conectar y ejecutar comandos

            ' Ejemplo con reintentos automáticos
            Dim intentos, resultado
            For intentos = 1 To 3

                ' Intentar conectar a la sesión
                Conect_Session nombreSesion, comandos

                resultado = EsperarPrompt(nombreSesion)
                If resultado = 0 Then Exit For
                crt.Sleep 2000 ' Espera 2 segundos entre intentos
                RegistrarLog archivoLog, "Reintento " & intentos & " para conectar a " & nombreSesion
            Next

            If resultado <> 0 Then
                RegistrarLog archivoLog, "Fallo definitivo al conectar a " & nombreSesion
                Exit Sub
            End If

            ' Esperar entre sesiones
            crt.Sleep retardo * 1000

            contadorArchivos = contadorArchivos + 1
            ' Desconectar
            crt.Session.Disconnect
        End If
    Next
    
    RegistrarLog archivoLog, "=== PROCESAMIENTO COMPLETADO ==="
    RegistrarLog archivoLog, "Total archivos procesados: " & contadorArchivos
 
End Sub
