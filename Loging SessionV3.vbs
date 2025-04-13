# $language = "VBScript"
# $Interface = "1.0"

Option Explicit

' Declaración de variables globales
Dim rutaCarpetaSesiones, objFSO, objCarpeta, archivos, archivo, nombreSesion
Dim retardo, archivoLog, comando
Dim contadorArchivos

' Configuración inicial
crt.Screen.Synchronous = False  ' Habilita modo asincrónico para evitar errores de tiempo de espera
crt.Screen.IgnoreEscape = True ' Ignora caracteres de escape para evitar problemas de conexión
crt.Session.Disconnect ' Desconectar sesión actual si está conectada

Sub Main()

    ' Rutas de configuración (MODIFICAR SEGÚN NECESARIO)
    rutaCarpetaSesiones = "D:\Usuarios\lriver14\AppData\Roaming\VanDyke\Config\Sessions\Tesis - Respaldo\"
    archivoLog = "D:\Usuarios\lriver14\Documents\Log - Falla -Codigo\log-debuging.txt"
    retardo = 1  ' Retardo entre sesiones en segundos
    
    ' Comandos a ejecutar en cada dispositivo
    comando = "show running-config"
    
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
        
        ' Ejemplo con reintentos automáticos
        Dim intentos, resultado
        For intentos = 1 To 3

        'On Error Resume Next ' Manejo básico de errores
        
        RegistrarLog archivoLog, "Conectando a " & nombreSesion
        
        ' Intentar conexión

        crt.Session.Connect("/S " & nombreSesion) ' Conectar a la sesión

        ' Obtener el prompt de la sesión
        resultado = Get_Prompt(nombreSesion)
        RegistrarLog archivoLog, "prompt: " & resultado & " - intentos: " & intentos

            If crt.Session.Connected Then
                RegistrarLog archivoLog, "Conexión exitosa a " & nombreSesion
                
                ' Esperar por el prompt inicial
                if resultado = 0 Then
                    RegistrarLog archivoLog, "Error esperando prompt en " & nombreSesion
                    Exit Sub
                End If
                    
                Select Case resultado
                    Case 0

                        RegistrarLog archivoLog, "Timeout ejecutando: " & comando
                    
                    Case 1 ' Caso para prompt '#'
                        
                        ' Configurar terminal para evitar paginación
                        crt.Screen.Send "terminal length 0" & vbCr
                        crt.Screen.WaitForString "#"
                        RegistrarLog archivoLog, "Ejecutando comando: " & comando
                        crt.Screen.Send comando & vbCr
                        RegistrarLog archivoLog, "Comando completado: " & comando 
                        crt.Screen.WaitForString "#"

                    case 2  ' Caso para prompt '>'

                        ' Configurar terminal para evitar paginación
                        crt.Screen.Send "terminal length 0" & vbCr
                        crt.Screen.WaitForString ">"
                        crt.Screen.Send "enable" & vbCr ' Enviar enable si es necesario
                        RegistrarLog archivoLog, "Ejecutando comando: " & comando
                        crt.Screen.Send comando & vbCr
                        RegistrarLog archivoLog, "Comando completado: " & comando 
                        crt.Screen.WaitForString "#"
                
                End Select
                    
            Else
                RegistrarLog archivoLog, "Error conectando a " & nombreSesion & ": " & crt.GetLastErrorMessage
            End If

            If crt.Session.Connected Then
                If resultado <> 0 Then Exit For ' Salir del bucle si conexión exitosa
                crt.Sleep 2000 ' Espera 2 segundos entre intentos
                RegistrarLog archivoLog, "Reintento " & intentos & " para conectar a " & nombreSesion
            End If

            If intentos > 3 Then
            RegistrarLog archivoLog, "Fallo definitivo al conectar a " & nombreSesion
                Exit Sub
            End If
      Next

        ' Esperar entre sesiones
        crt.Sleep retardo * 1000

        contadorArchivos = contadorArchivos + 1
        crt.Session.Disconnect ' Desconectar sesión
        RegistrarLog archivoLog, "Desconectado de " & nombreSesion
    End If
Next
    
    RegistrarLog archivoLog, "=== PROCESAMIENTO COMPLETADO ==="
    RegistrarLog archivoLog, "Total archivos procesados: " & contadorArchivos
 
End Sub

' Función para registrar en log
Sub RegistrarLog(rutaArchivoLog, mensaje)
    Dim objFSO, objArchivo
    
    'On Error Resume Next ' Manejo básico de errores
    
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    Set objArchivo = objFSO.OpenTextFile(rutaArchivoLog, 8, True) ' 8=append, True=crear si no existe
    
    objArchivo.WriteLine Now & " - " & mensaje
    objArchivo.Close
    
    'On Error GoTo 0
End Sub

' Función para crear archivo de log si no existe
Sub CrearArchivoLog(ruta, objFSO)
    If Not objFSO.FileExists(ruta) Then
        objFSO.CreateTextFile(ruta).Close
    End If
End Sub

Function Get_Prompt(nombreSesion)
    'On Error Resume Next ' Manejo básico de errores
    Dim lineaActual

    crt.Screen.Send vbCr ' Enviar un retorno de carro para asegurarse de que el cursor esté en la línea correcta
    If crt.Screen.WaitForStrings(Array(">", "#"), 5) Then

    ' Obtener la línea actual de la pantalla
    lineaActual = crt.Screen.Get(crt.Screen.CurrentRow, 1, crt.Screen.CurrentRow, crt.Screen.Columns)

        ' Verificar si la línea actual contiene los caracteres
        If InStr(1, lineaActual, "#") > 0 Then
            Get_Prompt = 1
        ElseIf InStr(1, lineaActual, ">") > 0 Then
            Get_Prompt = 2
        Else
            Get_Prompt = 0
        End If
    else
        ' Si no se encontró el prompt esperado, asignar 0
        Get_Prompt = 0
    End if

    RegistrarLog archivoLog, "Resultado Prompt: [" & Get_Prompt & "] - " & nombreSesion &" [1 = #, 2 = >, 0 = no encontro] "

End Function   

Function EsSesionValida(archivo, objFSO)
    Dim nombreArchivo, extension
    
    ' Obtener nombre y extensión limpios
    nombreArchivo = Trim(archivo.Name)  ' Elimina espacios al inicio y al final
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

