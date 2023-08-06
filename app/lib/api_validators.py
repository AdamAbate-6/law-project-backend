from fastapi import Query, Path

__user_id_requirements = dict(
    max_length=24,
    min_length=24,
    regex="^[a-z0-9]+$",
    description="_id field of entry in `projects` collection of MongoDB",
)

USER_ID_QUERY = Query(**__user_id_requirements)
USER_ID_PATH = Path(**__user_id_requirements)

USER_EMAIL_PATH = Path(
    regex=r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
)

__project_id_requirements = dict(
    max_length=24,
    min_length=24,
    regex="^[a-z0-9]+$",
    description="_id field of entry in `users` collection of MongoDB",
)
PROJECT_ID_QUERY = Query(**__project_id_requirements)
PROJECT_ID_PATH = Path(**__project_id_requirements)

PATENT_SPIF_PATH = Path(
    min_length=3,  # 2 country code characters + >=1 alphanumeric(s)
    max_length=99,  # Really just a sanity check
    regex=r"^[a-zA-Z]{2}[a-zA-Z0-9]+",
    description="Patent SPIF (see http://static.spif.group/spif-spec-0.3.0.pdf)",
)
