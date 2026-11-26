FROM python:3.11

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir tomtoolkit==2.26.2

RUN pip install --no-cache-dir -r requirements.txt
RUN git clone -b 1.0.5-slack https://github.com/cjduffy/tom_registration.git && cd tom_registration && pip install .

COPY . .

COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "tidestom.wsgi:application"]

