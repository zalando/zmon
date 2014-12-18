===============
Zmon Scheduler
===============

Unit tests
----------------
Navigate to zmon-scheduler/src directory:
cd <project_dir>/zmon-scheduler/src
Run:
python -m unittest discover -s tests


Running and building with Docker
--------------------------------

docker build -t zmon-scheduler .

docker run -i -e="ZONE=local" -t zmon-scheduler
