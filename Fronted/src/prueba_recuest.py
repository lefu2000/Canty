import requests
from getpass import getpass

class FlaskClient:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, username=None, password=None):
        """Login to the Flask server"""
        if username is None:
            username = input("Username: ")
        if password is None:
            password = getpass("Password: ")
        
        login_url = f"{self.base_url}/"
        response = self.session.post(login_url, data={
            'username': username,
            'password': password
        })
        
        if response.status_code == 200:
            if "dashboard" in response.url:
                print("Login successful!")
                return True
            else:
                print("Login failed. Check your credentials.")
                return False
        else:
            print(f"Login failed with status code: {response.status_code}")
            return False
    
    def get_dashboard(self):
        """Access the dashboard page"""
        dashboard_url = f"{self.base_url}/dashboard"
        response = self.session.get(dashboard_url)
        
        if response.status_code == 200:
            print("\nDashboard Content:")
            print("=================")
            # Extract and display relevant information from the HTML
            if '<table' in response.text:
                # Simple extraction of table data (would be better with BeautifulSoup)
                start = response.text.find('<table')
                end = response.text.find('</table>') + 8
                table_html = response.text[start:end]
                print("Devices Table:")
                print(table_html)
            else:
                print("Could not find devices table in response.")
            
            # Extract username if available
            if 'username' in response.text:
                user_pos = response.text.find('username')
                print(f"\nLogged in as: {response.text[user_pos:user_pos+50].split('>')[1].split('<')[0]}")
            
            return response.text
        else:
            print(f"Failed to access dashboard. Status code: {response.status_code}")
            return None
    
    def logout(self):
        """Logout from the server"""
        logout_url = f"{self.base_url}/logout"
        response = self.session.get(logout_url)
        if response.status_code == 200:
            print("Logged out successfully.")
            return True
        else:
            print(f"Logout failed with status code: {response.status_code}")
            return False

if __name__ == "__main__":
    client = FlaskClient()
    
    # Example usage
    print("Flask Server Client")
    print("===================")
    
    # Login
    if client.login():
        # Access dashboard
        client.get_dashboard()
        
        # Logout
        client.logout()