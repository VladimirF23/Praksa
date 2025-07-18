#!/bin/bash
set -e          

env #da vidim koje sve .env variable ova skripta vidi

#ova skripta zna za .env varbaible zato sto docker engine ih loaduje u dockerComposu ./devinfo... a docker 
#Takodje potrebno je promeniti u donjem desnom uglu na LF da bi unixov format

: "${MYSQL_HOST?Need to set MYSQL_HOST}"                #ove moraju da postoje, ako ne postoje scripta ce izaci sa error mesageom
: "${REDIS_PASSWORD?Need to set REDIS_PASSWORD}"

#proveri ovaj port
MYSQL_PORT=${MYSQL_PORT}
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

echo "⏳ Waiting for MySQL to be ready at $MYSQL_HOST:$MYSQL_PORT..."

# Wait for MySQL to respond
while ! mysqladmin ping -h"$MYSQL_HOST" -P"$MYSQL_PORT" --silent; do
    sleep 1
done
echo "✅ MySQL is up."



# Startujemo Flask app
echo "🚀 Starting Flask app..."
#exec python main.py

#exec je najbitniji ovde jer ce zameniti trenutni shell process wait-for-mysql.sh sa novim procesom python -m debugpy...

#python -m debugpy --listen 0.0.0.0:5678 --wait-for-client main.py -> Ovako se pokrece flask aplikacija, 
# i ja je launchujem sa debugpy za remote debuging containera u VScode-u
#listen govori debugpy da slusa za debuger-om na portu 5678 
# --wait-for client -> govori debugpy da pauzira pokretanje main.py dok debuger client VSCode-a se ne konektuje na njega

exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client main.py              #debuger ima fora zasto mora ovako a ne preko onog  u main-u sto ceka kao





#prvo manuelno sa docker-compose up da napravis containere ako si removovao i onda pozoves debug onaj preko VS-a e tada moze da se debuguje