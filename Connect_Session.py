def connect_network_device(ip, credentials, SCRIPT_TAB, timeout=5):
    """
    Conecta a un dispositivo de red usando SSH o Telnet como fallback
    Args:
        ip (str): Dirección IP del dispositivo
        credentials (dict): Diccionario con {'username': str, 'password': str}
        timeout (int): Tiempo de espera en segundos
    Returns:
        dict: Información del dispositivo y estado de conexión
    """
    # Estructura de información del dispositivo
    device = {
        "hostname": "",
        "username": credentials['username'],
        "conn": "",
        "status": 2  # Por defecto asumimos fallo (0=éxito, 1=auth fail, 2=conn fail)
    }

    for protocol in ["SSH2", "Telnet"]:
        try:
            if protocol == "SSH2":
                conn_str = f"/SSH2 /L {credentials['username']} /PASSWORD {credentials['password']} {ip}"
                device["conn"] = "SSH2"
            else:
                conn_str = f"/TELNET {ip}"
                device["conn"] = "Telnet"

            if Session.Connected:
                SCRIPT_TAB.Session.Disconnect

            SCRIPT_TAB.Session.Connect(conn_str)

            # Esperar diferentes tipos de prompts
            result = SCRIPT_TAB.Screen.WaitForString(["#", ">", "$", "Password:", "assword:", "ogin:", "Username: ", "sername"], timeout)
            
            # Si pide credenciales
            if result in [4, 5, 6, 7, 8]:  # Password o login prompts
                if result in [6, 7, 8]:  # Login prompt
                    SCRIPT_TAB.Screen.Send(credentials['username'] + "\r")
                    SCRIPT_TAB.Screen.WaitForString(["assword:", "Password:"], timeout)
                
                SCRIPT_TAB.Screen.Send(credentials['password'] + "\r")
                result = SCRIPT_TAB.Screen.WaitForString(["#", ">", "$"], timeout)
            
            # Si obtenemos prompt de comando
            if result in [1, 2, 3]:
                device["status"] = 0  # Éxito
                SCRIPT_TAB.Screen.Send("terminal length 0\r" if result in [1, 2] else "\r")
                
                return device
            else:
                device["status"] = 1  # Fallo de autenticación
                return device
                
        except Exception:
            continue  # Continuar con el siguiente protocolo si falla
    
    return device  # Retorna device con status=2 si ambos protocolos fallan