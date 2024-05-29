# IKE Python Server
Experimental FastAPI Server for providing [cytoscape.js](https://js.cytoscape.org/) formatted data from/to a [Neo4j](https://neo4j.com/developer/) database.

## Usage
```
poetry install
poetry run uvicorn ike_python_server.main:app --reload --host 0.0.0.0
```

Interactive docs should now be located at:

```
http://localhost:8000/docs
```
