# nginx/Dockerfile

FROM nginx:alpine


# Bolje je da se mount-uje preko docker-compose jer ako kopiram onda svaka promena na file-u u host machini zahteva rebuild
# 'docker compose build nginx' Nginx image-a i restartovanje container-a da bi se videle promene
# A kada se mount-uje kao volume docker napravi LIVE link i ako se dese promene na host file-u odma se vide izmene u pokrenutom NGinx container-u
# i samo treba da se se kaze Nginx-u da treba da reload-uje svoj config 'docker compose exec nginx nginx -s reload' ili lakse 
# samo restartujemo nginx service docker compose restart nginx da bi se apply-ovali changovi. 

# image treba da bude genericna da je STVARNO generican default.conf koji se skoro nikad ne menja za skoro svaki enviorment
# onda bih ga kopirao kao dole ali za project-specific config mountovanje je bolje
# COPY nginx.conf /etc/nginx/nginx.conf

# necemo ih kopirati posto cemo koristiti volume da mountujemo ih na docker container
# ako ih ovako kopiram onda postaju deo built image-a, a to ne valja jer  1. ti certificati rade samo na mom kompu
# 2. Ako neko drugi pulluje image certifikati nece matchovati njihov env, mogu se exposovati privatni kljucevi
# Forcuje se rebuild ako se certif promene
# 3. image postane manje portabilan:  Portabilan image  je image koji radi na razlicitim envormentima bez modifikacije
# 4. Krsi separation of concerns nginx posao je da radi sa trafficom ne da storuje private key-eve ili development certf
#   Ako bake-ujem certs u image  onda mesam web-server (nginx) i env specific cers (cers)
# ovaj image treba da ocekuje certifikate da ce biti predati u runtime-u preko volume-a ili secrets
 
#COPY certs/ /etc/nginx/certs/

EXPOSE 80
EXPOSE 443
