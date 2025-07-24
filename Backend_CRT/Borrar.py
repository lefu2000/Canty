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
import time
import seccrt
#import Connect_Session
def connect_network_device(ip, credentials, SCRIPT_TAB, timeout=20):
    
    #Versión mejorada con:
    #- Mejor detección de prompts
    #- Manejo más robusto de autenticación
    #- Soporte para key-exchange methods
    
    device = {
        "hostname": "",
        "username": credentials['username'],
        "conn": "",
        "status": 2  # 0=éxito, 1=auth fail, 2=conn fail
    }

    # Configuración de timeout global
    SCRIPT_TAB.Screen.IgnoreEscape = True
    SCRIPT_TAB.Screen.Synchronous = True

 

    for protocol in ["SSH2", "Telnet"]:
        try:
            if protocol == "SSH2":
                conn_str = f"/SSH2 /ACCEPTHOSTKEYS /L {credentials['username']} /PASSWORD {credentials['password']} {ip}"
                device["conn"] = "SSH2"
            else:
                conn_str = f"/TELNET {ip}"
                device["conn"] = "Telnet"

            if SCRIPT_TAB.Session.Connected:
                SCRIPT_TAB.Session.Disconnect()
            
            SCRIPT_TAB.Session.Connect(conn_str)
            
            if not SCRIPT_TAB.Session.Connected:
                device["status"] = 2
                continue

            # Establecer temporizador
            start_time = time.time()



            # Lista mejorada de prompts a detectar
            prompts = [
                "#", ">", "$",                        # Command prompts
                "Password:", "assword:",              # Password prompts
                "ogin:", "Username:", "sername:",     # Username prompts
                "User Access Verification"            # Cisco-style prompt
            ]

            while (time.time() - start_time) < timeout:
                result = SCRIPT_TAB.Screen.WaitForStrings(prompts, 2)
                if result == 0:  # Timeout
                    device["status"] = 2
                    continue
            
                # Manejo explícito del prompt "Username:"
                if result in [6, 7, 8, 9]:  # Username prompts
                    SCRIPT_TAB.Screen.Send(credentials['username'] + "\r")
                    SCRIPT_TAB.Screen.WaitForStrings(["Password:", "assword:"], timeout)
                    SCRIPT_TAB.Screen.Send(credentials['password'] + "\r")
                    result = SCRIPT_TAB.Screen.WaitForStrings(["#", ">", "$"], timeout)

                # Si aparece directamente password prompt
                elif result in [3, 4]:  # Password prompts
                    SCRIPT_TAB.Screen.Send(credentials['password'] + "\r")
                    result = SCRIPT_TAB.Screen.WaitForStrings(["#", ">", "$"], timeout)

                # Verificar éxito
                if result in [1, 2, 3]:  # Command prompts
                    device["status"] = 0
                    SCRIPT_TAB.Screen.Send("terminal length 0\r" if result in [1, 2] else "\r")
                    return device
                else:
                    device["status"] = 1
                    return device
            
                        # Si llegamos aquí, se agotó el tiempo
            raise TimeoutError("Tiempo de conexión agotado")        

        except TimeoutError:
            device["status"] = 2
            SCRIPT_TAB.Session.Disconnect()
            return device
        except Exception as e:
            device["status"] = 2
            continue

    return device






















#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    #Return the Tab or Session window from which the script was started
    SCRIPT_TAB = crt.GetScriptTab() 

    # Instruct WaitForString and ReadString to ignore escape sequences when
	# detecting and capturing data received from the remote.
    SCRIPT_TAB.Screen.IgnoreEscape = True
    SCRIPT_TAB.Screen.Synchronous = True   

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
            result = connect_network_device(ip, user_credentials, SCRIPT_TAB)
            if result["status"] == 1 and local_user_credentials != 1:
                result = connect_network_device(ip, user_credentials, SCRIPT_TAB)
        elif local_user_credentials != 1:
            result = connect_network_device(ip, user_credentials, SCRIPT_TAB)
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
            connect_result_file.writerow([router["router"],router['ip'],router["proveedor"],result["username"],"NOT AUTHENTICATE"])
        elif result["status"]  == 2:
            connect_result_file.writerow([router["router"],router['ip'],router["proveedor"],result["username"],"FAILED TO CONNECT"])
        
    file_connect.close()
    file_routers.close()
    crt.Screen.Synchronous = False
    crt.Dialog.MessageBox("Script Execution Completed")

main()