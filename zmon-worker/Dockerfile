FROM orchardup/python:2.7

RUN apt-get update && apt-get -y install python-dev libev4 libev-dev python-psycopg2 libpq-dev python-dev libldap2-dev libsasl2-dev libssl-dev freetds-dev

#making this a cachable point as compile takes forever without -j
RUN pip install numpy
RUN apt-get install -y python-ldap

RUN mkdir -p /app
WORKDIR /app

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ADD src /app/src
ADD web.conf /app/web.conf

CMD ["python", "/app/src/web.py"]
