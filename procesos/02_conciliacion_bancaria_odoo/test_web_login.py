import requests
from bs4 import BeautifulSoup
import urllib.parse
import json

def main():
    url = "https://your-company.odoo.com"
    login_url = f"{url}/web/login"
    
    session = requests.Session()
    
    print("Fetching login page to retrieve CSRF token...")
    r = session.get(login_url)
    if r.status_code != 200:
        print(f"Error fetching login page: {r.status_code}")
        return
        
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf_token_tag = soup.find('input', {'name': 'csrf_token'})
    if not csrf_token_tag:
        print("CSRF token not found in login page HTML.")
        return
        
    csrf_token = csrf_token_tag.get('value')
    print(f"CSRF Token: {csrf_token}")
    
    # We can also search for database list in the page source
    # Sometimes it's in a script tag or in window.odoo
    db_name = None
    for script in soup.find_all('script'):
        if script.string and 'db' in script.string:
            # Let's search for something like "db": "xxx"
            print("Found script tag containing 'db':")
            print(script.string[:500])
            print("-" * 50)
            
    payload = {
        'login': 'josmary.pinto@Empresa Demo.com',
        'password': 'Eduardo.24',
        'csrf_token': csrf_token
    }
    
    print("\nAttempting web login...")
    r_post = session.post(login_url, data=payload, allow_redirects=False)
    print(f"Post Response Code: {r_post.status_code}")
    print(f"Post Response Headers: {dict(r_post.headers)}")
    
    # If successful, it should redirect (usually status code 302 to /web or similar)
    if r_post.status_code in (302, 303):
        print("Login successful! Redirecting to:", r_post.headers.get('Location'))
    else:
        print("Login failed. Check username/password.")
        
    # Print session cookies
    print("\nSession Cookies:")
    for cookie in session.cookies:
        print(f"- {cookie.name}: {cookie.value}")
        if cookie.name == 'session_id':
            # Try to decode session info if possible, or print it
            pass

if __name__ == '__main__':
    main()
