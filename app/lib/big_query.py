import os
from google.cloud import bigquery


def query_patent(patent_spif: str) -> tuple[dict, bool]:
    os.environ[
        "GOOGLE_APPLICATION_CREDENTIALS"
    ] = "../law-project-service-account.json"
    client = bigquery.Client()

    # Perform a query. Need to UNNEST the struct of string arrays in several fields.
    # TODO Validate query so we don't get an injection attack.
    QUERY = (
        f"SELECT spif_publication_number as spif, t.text as title,  a.text as abstract, c.text as claims "
        f"FROM `patents-public-data.patents.publications`, UNNEST(title_localized) as t, UNNEST(abstract_localized) as a,  UNNEST(claims_localized) as c "
        f'WHERE spif_publication_number = "{patent_spif}" '
        f"LIMIT 100"
    )

    query_job = client.query(QUERY)  # Send API request.
    rows = query_job.result()  # Waits for query to finish.

    # `rows` is an iterator, but SPIF should be unique to one patent, so we should only iterate once.
    num_iters = 0
    patent_data = dict()
    for row in rows:
        patent_data["spif"] = row.spif
        patent_data["title"] = row.title
        patent_data["abstract"] = row.abstract
        patent_data["claims"] = row.claims
        # TODO Add in description

        num_iters += 1
        assert (
            num_iters == 1
        ), f"More than one entry was returned from BigQuery query to patent SPIF {patent_spif}; that cannot be correct."

    found_patent_in_bq = True if len(patent_data) > 1 else False
    return patent_data, found_patent_in_bq
