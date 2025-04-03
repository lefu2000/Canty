Sub Conect_Session(nombreSesion, comandos)
    Dim comando, resultado
    
    RegistrarLog archivoLog, "Conectando a " & nombreSesion
    
    ' Intentar conexión

    crt.Session.Connect("/S " & nombreSesion) ' Conectar a la sesión

    If crt.Session.Connected Then
        RegistrarLog archivoLog, "Conexión exitosa a " & nombreSesion
        
        ' Esperar por el prompt inicial
        if EsperarPrompt(nombreSesion) = 0 Then
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
            resultado = EsperarPrompt(nombreSesion)

            'EsperarPrompt
            ' 0 = Fallo
            ' 1 = Comando Show running-config corriendo.
            ' 2 = Para equipos 7250 Alcatel, pasar a modo administrador.
            ' 3 = Procesa Paginacion


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
        
        RegistrarLog archivoLog, "Desconectado de " & nombreSesion
    Else
        RegistrarLog archivoLog, "Error conectando a " & nombreSesion & ": " & crt.GetLastErrorMessage
    End If
End Sub