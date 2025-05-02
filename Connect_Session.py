
def connect_Session(ip,username, password):
    
    # ip: host
    # username: cualquier usuario
    # password: contrasena del usuario

    # Conectar a la sesión
    crt.Session.Connect("/SSH2 /L {} /PASSWORD {} {}".format(
        username, password, ip))
    
    # Esperar conexión y enviar comandos
    crt.Screen.WaitForString("$")
    crt.Screen.Send("ls -l\r")



Conectar por SSH y por Telnet







def connect_network_device(ip, credentials, timeout=10):

    #Device information
    device = {"hostname": "", "username": credentials['username'], "proveedor" : "", "conn" : "ssh", "status" : 0}

    """Versión especializada para equipos """
    for protocol in ["SSH", "Telnet"]:
        try:
            if protocol == "SSH":
                conn_str = f"/SSH2 /L {credentials['username']} /PASSWORD {credentials['password']} {ip}"
                device["conn"] = "SSH2"
            else:
                conn_str = f"/TELNET {ip}"
                device["conn"] = "Telnet"

            crt.Session.Connect(conn_str)
            
            # Manejo de prompts genéricos para equipos de red
            result = crt.Screen.WaitForStrings([":", "#", ">", "assword", "ogin"], timeout)
            
            if result in [4, 5]:  # Password o login prompt
                crt.Screen.Send(credentials['username'] + "\r")
                result = crt.Screen.WaitForStrings(["#", ">"], timeout)
            
            if result in [1, 2, 3]:  # Prompt encontrado
                crt.Screen.Send("terminal length 0\r")
                return True
                
        except Exception:
            continue
    
    return device


device["SO"] = "ios"
device["status"] = 2



Diccionario de Estado del Dispositivo
La función devuelve un diccionario con esta estructura:

Clave	Valores	Descripción
hostname	string	Nombre del host (vacío inicialmente)
username	string	Nombre de usuario usado
SO	"ios" o ""	Sistema operativo detectado
conn	"ssh" o "telnet"	Método de conexión usado
status	0, 1, 2	Estado de la conexión:
0 = Éxito	
1 = Error autenticación	
2 = Error conexión	
