' Función para crear archivo de log si no existe
Sub CrearArchivoLog(ruta, objFSO)
    If Not objFSO.FileExists(ruta) Then
        objFSO.CreateTextFile(ruta).Close
    End If
End Sub