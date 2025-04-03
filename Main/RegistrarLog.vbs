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