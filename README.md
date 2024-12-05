# smartGrid-e-mobCalculator

## Overview

The SmartGrid e-Mobility Calculator is a tool designed to optimize the configuration of photovoltaic (PV) panels and energy storage systems to achieve various goals such as minimizing costs, achieving self-sufficiency, or meeting a target yearly cost. The program calculates the optimal configuration based on user-defined parameters and provides detailed results including investment costs, yearly savings, and payback periods.

## Features

- Calculate optimal configuration of PV panels and batteries
- Support for multiple goals: most self-sufficient, target cost
- Detailed results including investment costs, yearly savings, and payback periods
- Web-based interface for easy parameter input and result visualization

## Project Structure

.gitattributes .gitignore .pytest_cache/ client/ APP.py requirements.txt static/ css/ styles.css js/ scripts.js media/ templates/ index.html main.py main.spec ngrok_authtoken.txt README.md server/ APP.py requirements.txt tests/

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/smartGrid-e-mobCalculator.git
    cd smartGrid-e-mobCalculator
    ```

2. Install the required Python packages for both the client and server:

    ```sh
    pip install -r client/requirements.txt
    pip install -r server/requirements.txt
    ```

3. Install ngrok and set up the authentication token:

    ```sh
    ngrok authtoken <your-ngrok-authtoken>
    ```

4. Create a file named `ngrok_authtoken.txt` and paste your ngrok authentication token into it.

## Usage

1. Start the main script:

    ```sh
    python main.py
    ```

2. The script will start the backend and frontend servers, and ngrok will provide public URLs for accessing the services.

3. Open the frontend URL provided by ngrok in your web browser to access the web interface.

4. Input the desired parameters and submit the form to calculate the optimal configuration.

## Configuration

- `main.py`: Main script to start the backend and frontend servers and ngrok.
- `server/APP.py`: Backend server implementation using Flask.
- `client/APP.py`: Frontend server implementation using Flask.
- `client/static/js/scripts.js`: JavaScript functions for handling form submissions and displaying results.
- `client/templates/index.html`: HTML template for the web interface.
- `client/static/css/styles.css`: CSS styles for the web interface.

## Logging

Log files are created for the backend, frontend, and ngrok processes:

- `backend.log`
- `frontend.log`
- `ngrok.log`

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Flask: A micro web framework for Python.
- ngrok: Secure introspectable tunnels to localhost.
- Bootstrap: Frontend component library for developing responsive web interfaces.
