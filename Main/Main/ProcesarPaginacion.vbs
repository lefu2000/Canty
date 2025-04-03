Sub ProcesarPaginacion()
    Do
        crt.Screen.Send " " ' Enviar espacio para continuar paginación
        
        ' Esperar siguiente página o prompt final
        If crt.Screen.WaitForString("--More--", 1) <> 1 Then
            Exit Do
        End If
    Loop
End Sub