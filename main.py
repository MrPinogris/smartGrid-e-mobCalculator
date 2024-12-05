import os
import sys
import subprocess
import time
import socket
import requests
import json

# Paths to your scripts
BACKEND_SCRIPT = "server/app.py"
FRONTEND_SCRIPT = "client/app.py"

# Log file paths
BACKEND_LOG = "backend.log"
FRONTEND_LOG = "frontend.log"
NGROK_LOG = "ngrok.log"

# File paths for PID and lock files
PID_FILE = os.path.join(os.path.dirname(sys.argv[0]), "script.pid")
LOCK_FILE = os.path.join(os.path.dirname(sys.argv[0]), "script.lock")

def start_server(script_path, log_path):
    python_executable = sys.executable
    with open(log_path, 'w') as log_file:
        process = subprocess.Popen(
            [python_executable, script_path],
            stdout=log_file,
            stderr=log_file,
            text=True
        )
    print(f"Started server for {script_path} with PID: {process.pid}")
    return process

def create_ngrok_config(authtoken):
    content = f"""version: "3"
agent:
    authtoken: {authtoken}
tunnels:
  flask_backend:
    proto: http
    addr: 5001
  flask_frontend:
    proto: http
    addr: 5000
"""
    with open("ngrok.yml", "w") as file:
        file.write(content)
    print("ngrok.yml file created successfully!")

def start_ngrok():
    with open('ngrok_authtoken.txt', 'r') as token_file:
         authtoken = token_file.read()
         print(f"Raw authtoken: {authtoken}")  # Debugging statement
         authtoken = authtoken.strip()
         print(f"Stripped authtoken: {authtoken}")  # Debugging statement

    create_ngrok_config(authtoken)

    with open(NGROK_LOG, 'w') as log_file:
        ngrok_process = subprocess.Popen(
            ['ngrok', 'start', '--all', '--config', 'ngrok.yml'],
            stdout=log_file,
            stderr=log_file,
            text=True
        )
    time.sleep(3)  # Give ngrok time to start
    return ngrok_process

def get_ngrok_urls(retries=5, delay=2):
    for _ in range(retries):
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            response.raise_for_status()
            tunnels = response.json()['tunnels']
            urls = {tunnel['name']: tunnel['public_url'] for tunnel in tunnels}
            return urls
        except requests.exceptions.RequestException as e:
            print(f"Error getting ngrok URLs: {e}")
            time.sleep(delay)
    return {}

def set_ngrok_url(url):
    try:
        response = requests.post('http://localhost:5001/ngrok_url', json={'ngrok_url': url})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error setting ngrok URL: {e}")

def set_backend_url_in_frontend(url):
    try:
        response = requests.post('http://localhost:5000/backend_url', json={'backend_url': url})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error setting backend URL in frontend: {e}")

def main():
    print("Starting main function.")
    
    # Check if the lock file exists
    if os.path.exists(LOCK_FILE):
        print("Lock file exists. Script is already running. Exiting.")
        return

    print("Creating lock file.")
    # Create the lock file
    with open(LOCK_FILE, 'w') as f:
        f.write("")

    print("Creating PID file.")
    # Create the PID file
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    try:
        print("Starting backend server.")
        # Start backend and frontend servers
        backend_process = start_server(BACKEND_SCRIPT, BACKEND_LOG)
        
        print("Starting frontend server.")
        frontend_process = start_server(FRONTEND_SCRIPT, FRONTEND_LOG)

        # Start ngrok
        print("Starting ngrok.")
        ngrok_process = start_ngrok()

        # Get ngrok URLs
        print("Getting ngrok URLs.")
        ngrok_urls = get_ngrok_urls()
        backend_ngrok_url = ngrok_urls.get('flask_backend')
        frontend_ngrok_url = ngrok_urls.get('flask_frontend')
        print(f"Backend ngrok URL: {backend_ngrok_url}")
        print(f"Frontend ngrok URL: {frontend_ngrok_url}")

        # Set the ngrok URL in the backend
        if backend_ngrok_url:
            set_ngrok_url(backend_ngrok_url)
            set_backend_url_in_frontend(backend_ngrok_url)

        # Give servers time to start
        print("Waiting for servers to start.")
        time.sleep(3)

        # Check if log files are created and print their content
        if os.path.exists(BACKEND_LOG):
            print(f"Backend log file created: {BACKEND_LOG}")
            with open(BACKEND_LOG, 'r') as f:
                print(f.read())
        else:
            print("Backend log file not created.")

        if os.path.exists(FRONTEND_LOG):
            print(f"Frontend log file created: {FRONTEND_LOG}")
            with open(FRONTEND_LOG, 'r') as f:
                print(f.read())
        else:
            print("Frontend log file not created.")

        if os.path.exists(NGROK_LOG):
            print(f"ngrok log file created: {NGROK_LOG}")
            with open(NGROK_LOG, 'r') as f:
                print(f.read())
        else:
            print("ngrok log file not created.")

        # Keep the script running until terminated
        print("Servers are running. Press CTRL+C to terminate.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Terminating servers.")
        backend_process.terminate()
        frontend_process.terminate()
        ngrok_process.terminate()
    finally:
        print("Cleaning up lock and PID files.")
        # Remove the lock file
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        # Remove the PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        print("Cleaned up lock and PID files.")

if __name__ == "__main__":
    main()