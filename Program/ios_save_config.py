#$language = "python"
#$interface = "1.0"

import os,sys

# Get the path to this script we're running...
ScriptPath = os.path.dirname(__file__)

# Add the path to this script into sys.path for use when looking for modules
# to import.
if not ScriptPath in sys.path:
    # Add the path of the running script if it is not in sys.path
    sys.path.insert(0, ScriptPath)

import csv
from datetime import date
import seccrt
import Connect_Session


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    #Return the Tab or Session window from which the script was started
    SCRIPT_TAB = crt.GetScriptTab()

    # Instruct WaitForString and ReadString to ignore escape sequences when
	# detecting and capturing data received from the remote.
    SCRIPT_TAB.Screen.IgnoreEscape = True
    SCRIPT_TAB.Screen.Synchronous = True
    SCRIPT_TAB.Screen.SynchronousTimeout = 60    

    # Ignorar verificación de host keys
    SCRIPT_TAB.Session.Config.Set("SSH2 HostKey Acceptance", "Accept Automatically")

    #List of commands to execute // The commands depend on the model and supplier
    COMMANDS_ZTE = [
        "enable",
        "terminal length 0",
        "show running-config",
        "!end"
        ]
    
    COMMANDS_ALCATEL = [
        "enable",
        "environment no more",
        "show running-config",
        "!end"
        ]

    COMMANDS_HUAWEI = [
        "display current-configuration",
        "!end"
        ]

    PROVEEDORES = [
        "ZTE",
        "ALCATEL",
        "HUAWEI"
    ]
    
    ##### Start  - Script Run Confirmation  ######
    msg_box_result = crt.Dialog.MessageBox("Do you want to run the script?", "Connect Routers Script", ICON_QUESTION | BUTTON_YESNO | DEFBUTTON2 )
    if msg_box_result == IDNO:
        return
    ##### End  - Script Run Confirmation  ######

    ##### Start  - Credentials Request ######
    user_credentials = seccrt.get_user_authentication_data(crt)
    local_user_credentials = 1

    msg_box_result2 = crt.Dialog.MessageBox("Would you like to use a local User?", "Local User", ICON_QUESTION | BUTTON_YESNO | DEFBUTTON2 )
    if msg_box_result2 == IDYES:
        local_user_credentials = seccrt.get_user_authentication_data(crt)

    if user_credentials == 1 and msg_box_result2 != IDYES:
        crt.Dialog.MessageBox("Script Cancelled. Reason: No Credentials inserted.")
        return
    elif user_credentials == 1 and msg_box_result2 == IDYES and local_user_credentials ==1:
        crt.Dialog.MessageBox("Script Cancelled. Reason: No Credentials inserted.")
        return
    ##### End  - Credentials Request ######

    ##### Start  - Script Select Routers to Connect ######
    router_list = crt.Dialog.FileOpenDialog(title="Select CSV with Routers",
                                           filter="CSV Files (*.csv)|*.csv||")

    path1 = os.path.dirname(router_list)
    connect_result = os.path.join(path1, "save_results.csv")

    ##### End  - Script Select Routers to Connect ######

    log_directory = os.path.join(path1, 'save')

    if not os.path.exists(log_directory):
	    os.mkdir(log_directory)    

    log_file_template = os.path.join(log_directory, "%(HOSTNAME)s_save_%(DATE)s.txt")

    # Archivo de resultados
    file_connect = open(connect_result, 'w', newline='', encoding='utf-8')
    file_routers = open(router_list, 'r')
    routers = csv.DictReader(file_routers, delimiter=';')
    connect_result_file = csv.writer(file_connect)

    # Table Headers (corregido también las comillas)
    connect_result_file.writerow(["router", "ip","proveedor", "username", "connection", "status"])

    #file_connect = open(connect_result, 'wb')
    #file_routers = open(router_list, 'r')
    #routers = csv.DictReader(file_routers)
    #connect_result_file = csv.writer(file_connect)

    #Table Headers
    #connect_result_file.writerow(["router","ip","username","connection","status"])

    for router in routers:
        # Verificar que existen todas las claves necesarias
        required_keys = ['router', 'ip', 'proveedor']
        if not all(key in router for key in required_keys):
            error_msg = f"Fila inválida en CSV. Faltan datos: {router}"
            crt.Dialog.MessageBox(error_msg)
            connect_result_file.writerow([router.get('router', 'N/A'), 'N/A', 'N/A', 'ERROR_CSV', error_msg[:50]])
            continue
    
        ip = router["ip"].strip('\n')

        log_file_name = log_file_template % {"HOSTNAME" : router["router"], "DATE" : date.today().isoformat()}

        ##### Start  - Connect to the Router  #######
        if user_credentials != 1:
            result = Connect_Session.connect_network_device(ip, user_credentials, SCRIPT_TAB)
            if result["status"] == 1 and local_user_credentials != 1:
                result = Connect_Session.connect_network_device(ip, user_credentials, SCRIPT_TAB)
        elif local_user_credentials != 1:
            result = Connect_Session.connect_network_device(ip, user_credentials, SCRIPT_TAB)
        ##### End  - Connect to the Router  #######

        ##### Start  - Connection Established with router, now SHOW  #######
        if result["status"] == 0:
            SCRIPT_TAB.Screen.Send("\r")
            status = "OK"
            if router["proveedor"].upper() in [p.upper() for p in PROVEEDORES]:

                if router["proveedor"].upper() == "ZTE":
                    # Comandos para equipos ZTE
                    command = COMMANDS_ZTE
                if router["proveedor"].upper() == "ALCATEL":
                    # Comandos para equipos ALCATEL
                    command = COMMANDS_ALCATEL
                if router["proveedor"].upper() == "HUAWEI":
                    # Comandos para equipos HUAWEI
                    command = COMMANDS_HUAWEI  


                # Código para dispositivos de estos proveedores
                result_log = seccrt.show_conf_statistics(command, SCRIPT_TAB)
            else:
                status = "FAILED. PROVEEDOR NO SOPORTADO."
                SCRIPT_TAB.Screen.Send("quit\r")
                connect_result_file.writerow([router['router'], router['ip'],router["proveedor"], result["username"], result["conn"], status])
                continue

        
            connect_result_file.writerow([router['router'],router['ip'],router["proveedor"],result["username"],result["conn"],status])

            SCRIPT_TAB.Session.Disconnect()

            filep = open(log_file_name, 'wb+')

            # Write out the results of the command to our log file
            filep.write(result_log.encode('utf8'))

            # Close the log file
            filep.close()
        
        #"router", "ip","proveedor", "username", "connection", "status"
        elif result["status"]  == 1:
            connect_result_file.writerow([router['router'],router['ip'],router["proveedor"],result["username"],"NOT AUTHENTICATE"])
        elif result["status"]  == 2:
            connect_result_file.writerow([router['router'],router['ip'],router["proveedor"],result["username"],"FAILED TO CONNECT"])
        
    file_connect.close()
    file_routers.close()
    crt.Screen.Synchronous = False
    crt.Dialog.MessageBox("Script Execution Completed")

main()
