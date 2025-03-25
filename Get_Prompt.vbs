#$language = "VBScript"
#$interface = "1.0"

' Funcion para obtener la ultima linea activa 

crt.Screen.Synchronous = True

Sub Main()
    
	Dim final
	final = DetectarPrompt()
	crt.Dialog.MessageBox final

End Sub

Function DetectarPrompt()
    ' Detectar el prompt
    Dim prompt
    crt.Screen.WaitForString "#", 1
    
	Dim lastLine
    lastLine = crt.Screen.Get(crt.Screen.CurrentRow, 1, crt.Screen.CurrentRow, crt.Screen.Columns)

    DetectarPrompt = lastLine

End Function
