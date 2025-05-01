#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# seccrt.py
#
# Description: This is a module for functions
# Author: Michael Alvarez
# Email: michadom21@gmail.com
# Last Date Modified: 2020-05-19
# Version: 1.1
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
def connect_to_router_sshgateway(ip,username, password, SCRIPT_TAB):

    #Device information
    device = {"hostname": "", "username": username, "SO" : "", "conn" : "ssh", "status" : 0}

     #Connect via SSH to Router IP
    SCRIPT_TAB.Screen.Send("ssh -o StrictHostKeyChecking=no {0}@{1}\r".format(username,ip))
    result_pass = SCRIPT_TAB.Screen.WaitForStrings(["assword", "Connection refused"], 10)

    #Connect Telnet if Connection is Refused using SSH
    if result_pass == 2:
        SCRIPT_TAB.Screen.Send("telnet {0}\r".format(ip))
        result_pass = SCRIPT_TAB.Screen.WaitForStrings(["sername", "Connection refused"], 5)
        if result_pass == 1:
            SCRIPT_TAB.Screen.Send("{0}\r".format(username))
            result_pass = SCRIPT_TAB.Screen.WaitForStrings(["assword", "Connection refused"], 5)
            device["conn"] = "telnet"
        else:
            device["status"] = 2
            return device

    elif result_pass == 0:
        SCRIPT_TAB.Screen.Send(chr(3))
        SCRIPT_TAB.Screen.WaitForStrings(["@Coding-Networks"], 10)
        device["status"] = 2
        return device

    if result_pass == 1:
        SCRIPT_TAB.Screen.Send("{0}\r".format(password))
        result_pass = SCRIPT_TAB.Screen.WaitForStrings(["assword:","failed","#"], 8)
        if result_pass == 1 or result_pass == 0 or result_pass == 2:
            SCRIPT_TAB.Screen.Send(chr(3))
            SCRIPT_TAB.Screen.WaitForStrings(["@Coding-Networks"], 10)
            device["status"] = 1
            return device
        elif result_pass == 3:
            SCRIPT_TAB.Screen.Send("terminal length 0\r")
            device["SO"] = "ios"
            return device

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def validate_configuration_exists(command, router_configuration):

    if command in router_configuration:
        return "True"
    else:
        return "False"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def configure_ios_devices(commands, SCRIPT_TAB):
    SCRIPT_TAB.Screen.Send("\rconfigure terminal\r")
    for command in commands:
        command = command.strip()
        SCRIPT_TAB.Screen.Send("{0}\r".format(command))

        # Wait for the command to be echoed back to us.
        SCRIPT_TAB.Screen.WaitForString('\r', 1)
        SCRIPT_TAB.Screen.WaitForString('\n', 1)

    #ReadString return a String with the configuration
    result = SCRIPT_TAB.Screen.ReadString(["!end"])
    result = result.strip()
    SCRIPT_TAB.Screen.Send(chr(26)) #Control + Z
    return result

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
    SCRIPT_TAB.Screen.Send(chr(26))
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