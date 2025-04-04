''Sub ProcesarPaginacion()
'    Do
 '        crt.Screen.Send " " ' Enviar espacio para continuar paginación
      '  
     '   ' Esperar siguiente página o prompt final
    '    If crt.Screen.WaitForString("--More--", 1) <> 1 Then
   '         Exit Do
  '      End If
 '   Loop
'End Sub


Sub SinPaginacion()

    ' Funciona comprobado para equipos 7250 Alcatel y 5928 ZTE
    crt.Screen.Send "terminal length 0" & vbCr ' Comando que evita la paginacion de los equipos, no sale mas --More--

End Sub
        
