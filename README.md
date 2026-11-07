# aitrade
An application that uses AI to run tradings for you


```mermaid
flowchart LR

    User(("User"))
    
    subgraph System
        
    
        subgraph Apps
            subgraph ai_data_downloader
                AiDataDownloader
                MarketDataListener
            end
            
            subgraph ai_trader [ai_trader]
                Trader
                OpenAIEngine
            end
            
            subgraph ai_web [ai_web]
                AiTraderHTTPServer
            end
        end
        
        ai_market_data_db[(ai_market_data_db)]
        ai_trades_db[(ai_trades_db)]
        GPU[RTX 3090]
    end

    IG[IG API]

    %% Flow Rules
    User -->|Http| AiTraderHTTPServer
    AiTraderHTTPServer -->|Read| ai_market_data_db
    AiTraderHTTPServer -->|Read| ai_trades_db

    AiDataDownloader -->|Subscribe| IG 
    IG -->|Sends Market Data| MarketDataListener
    MarketDataListener -->|Save| ai_market_data_db

    Trader -->|Read| ai_market_data_db
    Trader -->|Ask for recommendation| OpenAIEngine
    OpenAIEngine -->|Ask| GPU
    Trader -->|Make a trade| IG
    Trader -->|Save| ai_trades_db
    
    style Apps stroke-width:0, color:transparent
    style ai_data_downloader fill:#777777
    style ai_trader fill:#777777
    style ai_web fill:#777777
```



## Architecture

### ai_data_downloader

This module is responsible for downloading and storing market data from the IG API.

### ai_trader

This module is responsible for executing trades based on the downloaded market data and the trading strategy implemented in the `trading_engine` module.

### ai_web

This module is responsible for providing a web interface to view the trading results and market data.



## Development

Install system packages:

    sudo apt update
    sudo apt install python3 python3-pip python3-venv python-is-python3 pipx

Install the requirements:

    python -m venv .venv
    source .venv/bin/activate
    pip install .

Setup IG and Gemini API keys as described in https://www.ig.com/uk/myig/settings/api-keys

In the root folder, create a `.env` file and add all your configuration.



## Run

To execute the application from the project root with correct module resolution paths

### ai_data_downloader

    PYTHONPATH=src python src/ai_data_downloader/app.py

### ai_trader

    PYTHONPATH=src python src/ai_trader/app.py

### ai_web

    PYTHONPATH=src python src/ai_web/app.py



## Useful commands

### Command to test AI

    time curl http://server:9402/api/chat -H "Content-Type: application/json"   -d '{"model": "qwen2.5-coder:32b", "stream": false, "options": {"num_ctx": 16384}, "messages": [{"role": "user", "content": "Hello, how much is 4 * 5?"}]}'

### Update SQLite in prod

    docker exec -it ai_data_downloader python3 -c "import sqlite3; print(sqlite3.connect('/app/data/ai_market_data.db').execute('SELECT * FROM MARKET_DATA LIMIT 10;').fetchall())"
    docker exec -it ai_data_downloader python3 -c "import sqlite3; print(sqlite3.connect('/app/data/ai_trades.db').execute('SELECT * FROM TRADES;').fetchall())"

### Copy Data Locally

    scp server:/home/nio/docker-stack/aitrade/data/* ./data/
