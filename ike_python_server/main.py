from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from ike_python_server.database import query_db, Neo4jCredentials, can_connect
from ike_python_server.logger import logger
import json
import os
import logging


logger.setLevel(logging.DEBUG)

app = FastAPI()

origins = [
    "http://127.0.0.1:8000",  # Alternative localhost address
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",  # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load the Neo4j credentials from the environment
# neo4j_creds = Neo4jCredentials(
#     uri=os.getenv("NEO4J_URI"),
#     username=os.getenv("NEO4J_USERNAME"),
#     password=os.getenv("NEO4J_PASSWORD"),
#     database=os.getenv("NEO4J_DATABASE"),
# )


@app.post("/validate")
async def check_database_connection(creds: Neo4jCredentials):

    success, msg = can_connect(creds)
    if success:
        return {"message": "Connection successful"}, 200
    else:
        return {"message": "Connection failed", "error": msg}, 400


@app.post("/nodes/labels/")
def get_node_labels(creds: Neo4jCredentials) -> list[str]:
    """Return a list of Node labels from a specified Neo4j instance.

    Args:
        creds (Neo4jCredential): Credentials object for Neo4j instance to get node labels from.

    Returns:
        list[str]: List of Node labels
    """
    result = []
    query = """
        call db.labels();
    """
    response, _, _ = query_db(creds, query)

    logger.debug(f"get node labels response: {response}")

    result = [r.data()["label"] for r in response]

    logger.info(f"Node labels found: {result}")
    return result


@app.post("/nodes/")
def get_nodes(creds: Neo4jCredentials, labels: list[str] = []):

    if labels is not None and len(labels) > 0:
        query = """
    MATCH (n)
    WHERE any(label IN labels(n) WHERE label IN $labels)
    RETURN n
        """
        params = {"labels": labels}
    else:
        query = """
        MATCH (n)
        RETURN n
    """
        params = {}

    records, summary, key = query_db(creds, query, params)

    result = [
        {
            "data": {
                "id": r.values()[0]._element_id,
                "label": list(r.values()[0]._labels)[0],
                "node_data": r.data(),
            }
        }
        for r in records
    ]

    logger.debug(f"{len(result)} results found")
    if len(result) > 0:
        logger.debug(f"First result: {result[0]}")

    return result


@app.post("/nodes/new")
def create_node(creds: Neo4jCredentials, node_data: dict):
    # Process the node data and create a new node
    label = node_data["label"]
    id = node_data["id"]
    query = f"""
    MERGE (n:`{label})
    SET n.id = $id
    RETURN n.id as id, label(n) as label
    """
    params = {
        "id": id,
    }
    records, summary, keys = query_db(creds, query, params)

    logger.info(f"Add nodes summary: {summary}")

    return {"message": "New node created", "summary": summary}


@app.post("/relationships/types/")
def get_relationship_types(creds: Neo4jCredentials) -> list[str]:
    """Return a list of Relationship types from a Neo4j instance.

    Args:
        creds (Neo4jCredential): Credentials object for Neo4j instance to get Relationship types from.

    Returns:
        list[str]: List of Relationship types
    """
    result = []
    query = """
        call db.relationshipTypes();
    """
    response, _, _ = query_db(creds, query)

    logger.debug(f"get relationships types response: {response}")

    result = [r.data()["relationshipType"] for r in response]

    logger.info("Relationships found: " + str(result))
    return result


@app.post("/relationships/")
def get_relationships(
    creds: Neo4jCredentials,
    labels: Optional[list[str]] = None,
    types: Optional[list[str]] = None,
):

    # TODO: Add label and type filtering

    # query = f"""
    # MATCH (n)-[r]->(n2)
    # RETURN n.id as source, type(r) as label, n2.id as target, type(r) as id
    # """
    # query = f"""
    #     MATCH (n)-[r]->(n2)
    #     WHERE any(label IN labels(n) WHERE label IN $labels) AND any(label IN labels(n2) WHERE label IN $labels) AND type(r) in $types
    #     RETURN n, r, n2
    # params = {"labels": labels, "types": types}

    # """
    query = f"""
    MATCH (n)-[r]->(n2)
    RETURN n, r, n2
    """
    params = {}

    records, summary, keys = query_db(creds, query, params)

    result = []
    for r in records:
        source_id = r.values()[0]._element_id
        rid = r.values()[1]._element_id
        target_id = r.values()[2]._element_id
        r_label = r.data()["r"][1]
        result.append(
            {
                "data": {
                    "source": source_id,
                    "target": target_id,
                    "id": rid,
                    "label": r_label,
                    "relationship_data": r.data(),
                }
            }
        )

    logger.debug(f"{len(result)} results found")
    if len(result) > 0:
        logger.debug(f"First result: {result[0]}")

    return result


@app.post("/relationships/new/")
def create_relationship(creds: Neo4jCredentials, relationship_data: dict):
    # Process the relationship data and create a new relationship

    sid = relationship_data.source_id
    tid = relationship_data.target_id
    query = f"""
    MATCH (n{{id:$sid}}), (n2:{{id:$tid}})
    MERGE (n)-[r:{relationship_data.type}]->(n2)
    RETURN r
    """
    params = {"sid": sid, "tid": tid}
    records, summary, keys = query_db(creds, query, params)
    logger.info(f"Add relationship summary: {summary}")
    return {"message": "New relationship created", "summary": summary}
