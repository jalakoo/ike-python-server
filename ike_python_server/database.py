from neo4j import GraphDatabase, basic_auth
from pydantic import BaseModel
from ike_python_server.logger import logger


class Neo4jCredentials(BaseModel):
    uri: str
    password: str
    user: str = "neo4j"
    database: str = "neo4j"


def query_db(creds: Neo4jCredentials, query: str, params: dict = {}):
    try:
        with GraphDatabase.driver(
            creds.uri, auth=basic_auth(creds.user, creds.password)
        ) as driver:
            return driver.execute_query(query, params, database=creds.database)
    except Exception as e:
        logger.error(
            f"Problem running query: {query} with params: {params}. ERROR: {e}"
        )
        raise e
