def connect_network_device(ip, credentials, SCRIPT_TAB, timeout=30):
    """
    Versión mejorada con:
    - Mejor detección de prompts
    - Manejo más robusto de autenticación
    - Soporte para key-exchange methods
    """
    device = {
        "hostname": "",
        "username": credentials['username'],
        "conn": "",
        "status": 2  # 0=éxito, 1=auth fail, 2=conn fail
    }

    # Configurar métodos de key-exchange compatibles
    preferred_kex = "diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha1"
    SCRIPT_TAB.Session.Config.Set("KeyExchange", preferred_kex)

    # Configuración de timeout global
    SCRIPT_TAB.Session.SetTimeout(timeout)
    SCRIPT_TAB.Screen.SynchronousTimeout = timeout
    SCRIPT_TAB.Screen.IgnoreEscape = True
    SCRIPT_TAB.Screen.Synchronous = True

    # Ignorar verificación de host keys
    crt.Session.Config.Set("SSH2 HostKey Acceptance", "Accept Automatically")

    for protocol in ["SSH2", "Telnet"]:
        try:
            if protocol == "SSH2":
                conn_str = f"/SSH2 /L {credentials['username']} /PASSWORD {credentials['password']} {ip}"
                device["conn"] = "SSH2"
            else:
                conn_str = f"/TELNET {ip}"
                device["conn"] = "Telnet"

            if SCRIPT_TAB.Session.Connected:
                SCRIPT_TAB.Session.Disconnect()

            # Establecer temporizador
            start_time = time.time()

            if not SCRIPT_TAB.Session.Connect(conn_str):
                continue

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
            SCRIPT_TAB.Screen.Send("\x03")  # Ctrl+C para cancelar operación pendiente
            continue
    
    return device