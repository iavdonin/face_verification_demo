FROM python:3.9

RUN python -m pip install --upgrade pip
RUN python -m pip install poetry

COPY . .

RUN poetry install

ENTRYPOINT ["docker-entrypoint.sh"]