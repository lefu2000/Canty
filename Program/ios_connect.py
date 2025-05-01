#$language = "python3"
#$interface = "1.0"

import csv
import os,sys

# Get the path to this script we're running...
ScriptPath = os.path.dirname(__file__)

# Add the path to this script into sys.path for use when looking for modules
# to import.
if not ScriptPath in sys.path:
    # Add the path of the running script if it is not in sys.path
    sys.path.insert(0, ScriptPath)

import seccrt

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():

    #Return the Tab or Session window from which the script was started
    SCRIPT_TAB = crt.GetScriptTab()

    #Before running all the remaining script, validate if session is connected.
    if not SCRIPT_TAB.Session.Connected:
        crt.Dialog.MessageBox("Not Connected.  Please connect before running this script.")
        return

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

    # If No AAA was Inserted and Local users MessageBox No button was pressed,cancel the script.
    if user_credentials == 1 and msg_box_result2 != IDYES:
        crt.Dialog.MessageBox("Script Cancelled. Reason: No Credentials inserted.")
        return

    # If No AAA was Inserted and Local users MessageBox Yes button was pressed, but blank user or password was inserted
    # script will be cancelled.
    elif user_credentials == 1 and msg_box_result2 == IDYES and local_user_credentials == 1:
        crt.Dialog.MessageBox("Script Cancelled. Reason: No Credentials inserted.")
        return

    ##### End  - Credentials Request ######

    ##### Start  - Script Select Routers to Connect ######
    router_list = crt.Dialog.FileOpenDialog(title="Select CSV with Routers",
                                           filter="CSV Files (*.csv)|*.csv||")

    ##### End  - Script Select Routers to Connect ######
	# Instruct WaitForString and ReadString to ignore escape sequences when
	# detecting and capturing data received from the remote.
    SCRIPT_TAB.Screen.IgnoreEscape = True

    #Enable Synchronous setting to make No Missed Data fromo the server.
    SCRIPT_TAB.Screen.Synchronous = True

    while True:
        if not SCRIPT_TAB.Screen.WaitForCursor(1):
            break
    
    file_routers = open(router_list, 'r')
    routers = csv.DictReader(file_routers)

    for router in routers:
        ip = router["ip"].strip('\n')

        ##### Start  - Connect to the Router  #######
        if user_credentials != 1:
            result = seccrt.connect_to_router_sshgateway(ip,user_credentials["username"],
                                                      user_credentials["password"], SCRIPT_TAB)
            if result["status"] == 1 and local_user_credentials != 1:
                result = seccrt.connect_to_router_sshgateway(ip,local_user_credentials["username"],
                                                            local_user_credentials["password"], SCRIPT_TAB)
        elif local_user_credentials != 1:
            result = seccrt.connect_to_router_sshgateway(ip,local_user_credentials["username"],
                                                         local_user_credentials["password"], SCRIPT_TAB)
        ##### End  - Connect to the Router  #######

        ##### Start  - Connection Established with router, now SHOW  #######
        if result["status"] == 0:
            SCRIPT_TAB.Screen.Send("\r")
            if router["os"] == "ios":
                pass
            else:
                SCRIPT_TAB.Screen.Send("quit\r")
                SCRIPT_TAB.Screen.WaitForStrings(["@Coding-Networks"], 10)
                continue

            SCRIPT_TAB.Screen.Send("quit\r")

            SCRIPT_TAB.Screen.WaitForStrings(["@Coding-Networks"], 10)

    file_routers.close()
    crt.Screen.Synchronous = False
    crt.Dialog.MessageBox("Script Execution Completed")

main()
