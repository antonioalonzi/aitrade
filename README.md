# aitrade
AI trading online


## Development

Install pip

    sudo apt update
    sudo apt install python3 python3-pip python3-venv python-is-python3

Install the requirements

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt


Setup ig api keys as described in https://www.ig.com/uk/myig/settings/api-keys

in the .env file add:

    IG_SERVICE_API_KEY=<key>
    IG_SERVICE_USERNAME=<username>
    IG_SERVICE_PASSWORD=<password>
    IG_SERVICE_ACC_TYPE=<DEMO or LIVE>
    IG_SERVICE_ACC_NUMBER=<acc-number>

    
### Kate

If using kate:
    
    pipx install "python-lsp-server[all]"

Kate -> Settings -> Configure Kate -> Plugins -> LSP Client check -> Apply


    
## Run

    python main.py
