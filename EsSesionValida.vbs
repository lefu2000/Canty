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
