# aitrade
AI trading online



## Development

Install system packages:

    sudo apt update
    sudo apt install python3 python3-pip python3-venv python-is-python3 pipx

Install the requirements:

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Setup IG and Gemini API keys as described in https://www.ig.com/uk/myig/settings/api-keys

In the root folder, create a `.env` file and add:

    IG_SERVICE_API_KEY=<key>
    IG_SERVICE_USERNAME=<username>
    IG_SERVICE_PASSWORD=<password>
    IG_SERVICE_ACC_TYPE=<DEMO or LIVE>
    IG_SERVICE_ACC_NUMBER=<acc-number>
    
    GEMINI_API_KEY=<key>



## Run

To execute the application from the project root with correct module resolution paths:

    PYTHONPATH=src python src/main.py
