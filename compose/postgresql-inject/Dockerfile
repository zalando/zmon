FROM ubuntu:16.04
RUN apt-get -y update && apt-get -y install git postgresql-client bash wget unzip
RUN mkdir -p workdir
COPY inject.sh /inject.sh
CMD ["bash","-x","/inject.sh"]
