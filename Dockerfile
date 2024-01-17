FROM python:latest

WORKDIR /futsaal

COPY requirements.txt requirements.txt
COPY app.py app.py
COPY helpers.py helpers.py
COPY static static
COPY templates templates
COPY empty.db empty.db

RUN cp empty.db futsal.db

RUN pip install -r requirements.txt
RUN pip install gunicorn

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0", "app:app"]
