Running and building with Docker
================================

docker build -t zmon-worker .

docker run -i -e="ZONE=local" --dns=10.229.4.7 --dns=10.229.4.8 -t zmon-worker
