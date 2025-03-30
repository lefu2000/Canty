# $language = "VBScript"
# $Interface = "1.0"

Option Explicit

' Declaración de variables globales
Dim rutaCarpetaSesiones, objFSO, objCarpeta, archivos, archivo, nombreSesion
Dim retardo, archivoLog, comandos
Dim contadorArchivos

' Configuración inicial
crt.Screen.Synchronous = False  ' Habilita modo asincrónico para evitar errores de tiempo de espera
crt.Screen.IgnoreEscape = True ' Ignora caracteres de escape para evitar problemas de conexión

Sub Main()
    ' Rutas de configuración (MODIFICAR SEGÚN NECESARIO)
    rutaCarpetaSesiones = "D:\Usuarios\lriver14\AppData\Roaming\VanDyke\Config\Sessions\Tesis - Respaldo\"
    archivoLog = "D:\Usuarios\lriver14\Documents\Log - Falla -Codigo\log-debuging.txt"
    retardo = 5  ' Retardo entre sesiones en segundos
    
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
            
            ' Desconectar si hay sesión activa
            If crt.Session.Connected Then
                crt.Session.Disconnect
                crt.Sleep 2000 ' Esperar 2 segundos
            End If
            
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
        End If
    Next
    
    RegistrarLog archivoLog, "=== PROCESAMIENTO COMPLETADO ==="
    RegistrarLog archivoLog, "Total archivos procesados: " & contadorArchivos
 
End Sub

Sub Conect_Session(nombreSesion, comandos)
    Dim comando, resultado
    
    RegistrarLog archivoLog, "Conectando a " & nombreSesion
    
    ' Intentar conexión

    crt.Session.Connect("/S " & nombreSesion) ' Conectar a la sesión

    If crt.Session.Connected Then
        RegistrarLog archivoLog, "Conexión exitosa a " & nombreSesion
        
        ' Esperar por el prompt inicial
        if EsperarPrompt(nombreSesion) <> 0 Then
            RegistrarLog archivoLog, "Error esperando prompt en " & nombreSesion
            Exit Sub
        End If
        
        ' Configurar terminal para evitar paginación
        crt.Screen.Send "terminal length 0" & vbCr
        crt.Screen.WaitForString "#"
        
        ' Ejecutar cada comando
        For Each comando In comandos
            RegistrarLog archivoLog, "Ejecutando comando: " & comando
            
            crt.Screen.Send comando & vbCr
            resultado = crt.Screen.WaitForString(Array("#", ">", "--More--"), 10)
            
            Select Case resultado
                Case 0
                    RegistrarLog archivoLog, "Timeout ejecutando: " & comando
                Case 1
                    RegistrarLog archivoLog, "Comando completado: " & comando 
                case 2
                    crt.Screen.Send "enable" & vbCr ' Enviar enable si es necesario
                    RegistrarLog archivoLog, "Comando completado: " & comando 
                Case 3
                    ProcesarPaginacion()
            End Select
            
            crt.Sleep 1000 ' Pequeña pausa entre comandos
        Next
        
        ' Desconectar
        crt.Session.Disconnect
        RegistrarLog archivoLog, "Desconectado de " & nombreSesion
    Else
        RegistrarLog archivoLog, "Error conectando a " & nombreSesion & ": " & crt.GetLastErrorMessage
    End If
End Sub

Sub ProcesarPaginacion()
    Do
        crt.Screen.Send " " ' Enviar espacio para continuar paginación
        
        ' Esperar siguiente página o prompt final
        If crt.Screen.WaitForString("--More--", 1) <> 1 Then
            Exit Do
        End If
    Loop
End Sub

' Función para registrar en log
Sub RegistrarLog(rutaArchivoLog, mensaje)
    Dim objFSO, objArchivo
    
    On Error Resume Next ' Manejo básico de errores
    
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    Set objArchivo = objFSO.OpenTextFile(rutaArchivoLog, 8, True) ' 8=append, True=crear si no existe
    
    objArchivo.WriteLine Now & " - " & mensaje
    objArchivo.Close
    
    On Error GoTo 0
End Sub

' Función para crear archivo de log si no existe
Sub CrearArchivoLog(ruta, objFSO)
    If Not objFSO.FileExists(ruta) Then
        objFSO.CreateTextFile(ruta).Close
    End If
End Sub

' Versión corregida de la función EsperarPrompt
Function EsperarPrompt(nombreSesion)
    ' Esperar por el prompt de la sesión
    Dim promptEncontrado
    
    ' Esperar por cualquiera de los prompts posibles
    If crt.Screen.WaitForString("#", 10) Then
        RegistrarLog archivoLog, "Prompt # detectado en " & nombreSesion
        EsperarPrompt = 0  ' Éxito
    ElseIf crt.Screen.WaitForString(">", 2) Then
        RegistrarLog archivoLog, "Prompt > detectado en " & nombreSesion
        EsperarPrompt = 0  ' Éxito
    ElseIf crt.Screen.WaitForString("--more--", 2) Then
        RegistrarLog archivoLog, "Prompt --more-- detectado en " & nombreSesion
        EsperarPrompt = 0  ' Éxito
    Else
        RegistrarLog archivoLog, "No se detectó prompt válido en " & nombreSesion
        EsperarPrompt = 1  ' Error
    End If
End Function    

Function EsSesionValida(archivo, objFSO)
    Dim nombreArchivo, extension
    
    ' Obtener nombre y extensión limpios
    nombreArchivo = Trim(archivo.Name)  ' Elimina espacios al inicio/final
    extension = LCase(objFSO.GetExtensionName(nombreArchivo))
    
    ' Depuración - registrar detalles del archivo
    RegistrarLog archivoLog, "Validando archivo: " & nombreArchivo & _
                           " | Ext: " & extension & _
                           " | Tamaño: " & archivo.Size & " bytes" & _
                           " | FolderData: " & (InStr(1, nombreArchivo, "__FolderData__", vbTextCompare) > 0)
    
    ' Condiciones de validación
    EsSesionValida = (extension = "ini" And _
                     InStr(1, nombreArchivo, "__FolderData__", vbTextCompare) = 0 And _
                     archivo.Size > 0)  ' Cambiado a > 0 para aceptar cualquier tamaño
End Function
