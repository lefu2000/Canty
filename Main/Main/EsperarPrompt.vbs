' Versión corregida de la función EsperarPrompt
Function EsperarPrompt(nombreSesion)
    ' Esperar por el prompt de la sesión
    Dim promptEncontrado
    
    ' Esperar por cualquiera de los prompts posibles
    If crt.Screen.WaitForString("#", 5) Then
        RegistrarLog archivoLog, "Prompt # detectado en " & nombreSesion
        EsperarPrompt = 1  ' Éxito
    ElseIf crt.Screen.WaitForString(">", 2) Then
        RegistrarLog archivoLog, "Prompt > detectado en " & nombreSesion
        EsperarPrompt = 2  ' Éxito
    ElseIf crt.Screen.WaitForString("--more--", 2) Then
        RegistrarLog archivoLog, "Prompt --more-- detectado en " & nombreSesion
        EsperarPrompt = 3  ' Éxito
    Else
        RegistrarLog archivoLog, "No se detectó prompt válido en " & nombreSesion
        EsperarPrompt = 0  ' Error
    End If
End Function    

