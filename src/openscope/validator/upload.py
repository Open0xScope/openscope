import os

import psycopg2


def upload_data(token: str) -> (str, str):
    db_connection_uri = os.environ.get("DB_CONNECTION_URI")
    with psycopg2.connect(db_connection_uri) as conn:
        with conn.cursor() as cursor:
            address = token.lower()
            query = f"""
            select project_id, project_name from multichain_view_dim.view_dim_project_info where coingecko_id in (\
            select coingecko_id from multichain_view_dim.view_dim_addr_tokens_all where token_address = '{address}')
            """
            cursor.execute(
                query,
            )

            results = cursor.fetchall()
            if len(results) > 0:
                return (results[0][0], results[0][1])
    return None