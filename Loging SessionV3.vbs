#$Language="VBScript"
#$Interface="1.0"

Sub Main()

    Dim rutaCarpetaSesiones, objFSO, objCarpeta, archivos, archivo, nombreSesion, comandos, comando, retardo
    Dim usuario, contrasena, host, archivoLog

    ' Credenciales
    usuario = "lriver14" ' Reemplaza con tu nombre de usuario
    contrasena = "Gamboa.16" ' Reemplaza con tu contraseÃ±a

    ' Ruta a la carpeta que contiene las sesiones de SecureCRT (.ini) "D:\usuario\XXXX\AppData\Roaming\Vanyke\Config\Session"
    ' El ejemplo de la ruta puede variar donde ud. tenga guardado las sessiones pre configuradas
    rutaCarpetaSesiones = "D:\Usuarios\lriver14\AppData\Roaming\VanDyke\Config\Sessions\PRUEBA - TESIS" ' CUIDADO CON LA RUTA

    ' Lista de comandos a ejecutar en cada sesiÃ³n
    comandos = Array("Hola mundo", "logout")

    ' Retardo entre sesiones (en segundos)
    retardo = 5

    ' Crear objeto FileSystemObject
    Set objFSO = CreateObject("Scripting.FileSystemObject")

    ' Obtener la carpeta de sesiones
    Set objCarpeta = objFSO.GetFolder(rutaCarpetaSesiones)

    ' Obtener la coleccion de archivos en una unica carpeta  * IMPORTANTE CUIDADO CON LA RUTA	
    Set archivos = objCarpeta.Files

    ' Crear archivo de log
    archivoLog = "D:\RESPALDO CRT\Logs-Tesis\log.txt" ' Cambia la ruta del archivo de log DONDE SE GUARDARAN LOS MENSAJES DEBUGGIN
    If Not objFSO.FileExists(archivoLog) Then
        objFSO.CreateTextFile archivoLog
    End If

    ' Bucle a traves de los archivos (sesiones)
    For Each archivo In archivos

        ' Verificar si el archivo es una sesiÃ³n de SecureCRT (.ini)
        If LCase(objFSO.GetExtensionName(archivo.Name)) = "ini" Then 
            if objFSO.GetBaseName(archivo.Name) != "__FolderData__" Then ' If para evitar que lea el archivo __FolderData__
                ' Obtener el nombre de la sesiÃ³n (sin la extension .ini)
                nombreSesion = objFSO.GetBaseName(archivo.Name)

                ' Extraer el host del nombre de la sesiÃ³n (asumiendo formato "usuario@host" o similar)
                ' host = Split(nombreSesion, " ")(1) ' Ajusta el delimitador si es diferente

                ' Valida que la session este desconectada
                crt.Session.Disconnect 

                ' 1. Entrada automatica (conexion)
                If crt.Session.Connect("/S" & nombreSesion) Then
                'If crt.Session.Connect("/ssh2 /l " & usuario & " /password " & contrasena & " " & host) Then

                    RegistrarLog archivoLog, "Conectado a " & nombreSesion

                    crt.Screen.Synchronous = True
                    crt.Sleep retardo * 1000

                    ' 2. IntroducciÃ³n de comandos
                    For Each comando In comandos
                        crt.Screen.Send comando & vbCr
                        If crt.Screen.WaitForString(Array("#","<",">"), 10) Then ' Caraceteres que espera que aparesca en pantalla para continuar
                            RegistrarLog archivoLog, "Comando: '" & comando & "' ejecutado correctamente en " & nombreSesion
                        Else
                            RegistrarLog archivoLog, "Error al ejecutar el comando '" & comando & "' en " & nombreSesion
                        End If
                    Next

                    ' 3. Salida automÃ¡tica (desconexiÃ³n)
                    crt.Session.Disconnect
                    RegistrarLog archivoLog, "Desconectado de " & nombreSesion

                    crt.Screen.Synchronous = False

                Else
                    RegistrarLog archivoLog, "Error al conectar a la sesion " & nombreSesion
                    crt.Dialog.MessageBox "Error al conectar a la sesion " & nombreSesion
                End If

                ' Retardo antes de conectar a la siguiente sesiÃ³n
                crt.Sleep retardo * 1000
            End if
        End If

    Next

End Sub

Sub RegistrarLog(rutaArchivoLog, mensaje)
    Dim objFSO, objArchivo

    Set objFSO = CreateObject("Scripting.FileSystemObject")
    Set objArchivo = objFSO.OpenTextFile(rutaArchivoLog, 8, True) ' 8 para anexar
    objArchivo.WriteLine Now() & " - " & mensaje
    objArchivo.Close
End Sub
