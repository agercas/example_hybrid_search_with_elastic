# Example Hybrid Search using Elasticsearch and FastAPI
Example code using elasticsearch and fastapi for hybrid search endpoints. 

# Setup
The following environment variables are required 

```bash
export ELASTIC_URL='https://localhost:9200'
export ELASTIC_USERNAME='elastic'
export ELASTIC_PASSWORD='**********************'
export ELASTIC_HTTP_CA_CRT='http_ca.crt'
```

# Run

Start an app
```bash
uvicorn main:app --reload
```

Load sample data
```bash
python cli.py ./data.json
```
