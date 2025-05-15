#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# seccrt.py
#
# Description: This is a module for functions
# Author: Luis Rivera
# Email: michadom21@gmail.com
# Last Date Modified: 2025-05-14
# Version: 0.0.1
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_user_authentication_data(SCRIPT_TAB):

    user_credentials = {}
    user_credentials["username"] = SCRIPT_TAB.Dialog.Prompt("Write Username:", "Logon Script", "", False)

    if user_credentials["username"] == "":
        SCRIPT_TAB.Dialog.MessageBox("WARNING: Blank User. Script could be cancelled")
        return 1

    user_credentials["password"] = SCRIPT_TAB.Dialog.Prompt("Write Password:", "Logon Script", "", True)

    # User clicked Cancel button
    if user_credentials["password"] == "":
        SCRIPT_TAB.Dialog.MessageBox("WARNING: Blank Password. Script could be cancelled")
        return 1

    return user_credentials

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def show_conf_statistics(commands, SCRIPT_TAB):

    for command in commands:
        command = command.strip()
        SCRIPT_TAB.Screen.Send("{0}\r".format(command))

        # Wait for the command to be echoed back to us.
        SCRIPT_TAB.Screen.WaitForString('\r', 1)
        SCRIPT_TAB.Screen.WaitForString('\n', 1)

		#SCRIPT_TAB.Screen.WaitForStrings(["#"], 120)
    #ReadString return a String with the configuration
    result = SCRIPT_TAB.Screen.ReadString(["!end"])
    result = result.strip()
    clear_buffer(SCRIPT_TAB)
#    SCRIPT_TAB.Screen.Send(chr(26))
    return result

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def load_files(file_name,extension,SCRIPT_TAB):
    while True:
        filesource = SCRIPT_TAB.Dialog.FileOpenDialog(title="Please select " + file_name +" file",
                                           filter="Files (*." + extension +")|*." + extension +"||")
        if file_name in filesource:
            return filesource
        elif not filesource:
            return filesource
        else:
            SCRIPT_TAB.Dialog.MessageBox("Este NO es el archivo" + file_name + ", Intente de Nuevo")


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Función para limpiar buffer
def clear_buffer(tab):
    tab.Screen.Send("\r\n")
    tab.Screen.WaitForString("\r\n", 1)
    tab.Screen.Send("\x03\x03")  # Múltiples Ctrl+C
    time.sleep(1)

# Usar antes de cada nueva conexión
clear_buffer(SCRIPT_TAB)