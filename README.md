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
    
### Kate IDE Integration

If using Kate editor for development, install the language server:
    
    pipx install "python-lsp-server[all]"

Then enable it via:

    Kate -> Settings -> Configure Kate -> Plugins -> Check "LSP Client" -> Apply


### AI with aider and local models

Install [ollama](https://docs.ollama.com/linux) and model

    curl -fsSL https://ollama.com/install.sh | sh    
    ollama pull qwen2.5-coder:7b
                         # or 1.5b if your machine cannot afford it

Install [aider](https://aider.chat/#getting-started)

    pipx install aider-install
    aider-install
    pipx uninstall aider-install

Run aider with the above model

    OLLAMA_NUM_CTX=8192 aider --model ollama_chat/qwen2.5-coder:7b .gitignore README.md requirements.txt $(find src -type f -not -path '*/__pycache__*')
                                       # or 1.5b
    
Now ask aider to code for you!
    
    

## Run

To execute the application from the project root with correct module resolution paths:

    PYTHONPATH=src python src/main.py
