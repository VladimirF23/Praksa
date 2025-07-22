FROM node:24-slim

WORKDIR /app

#Drzimo 2 DockerFile jedan za flask a jedan za react
#1.Zato sto su drugiciji Tehnology Stackovi tj Flask je Python base a React je JavaScript(Node.js) based i zato i trebaju razl base image i dependencies
#2. Izolocija Dependencija ->Flask koristi lib (Flask,SQLAlchemy itd) a React koristi NPM packages(react,axios,etc)
#   Ako ih kombinujemo imali bi python i node dependencies u 1 image-u sto nije efikasno i bloatovano je
#3.Nezavisan Build i demplyoment
#   Nezavisno mozemo da buildujemo,scale-ujemo,deployujemo Flask API i react frontend
#   Npr ako front ima vise trafica mozemo da scalujemo samo react container
#4. Separation of Concerns
#   lakse za debug i maintan
#   React mozemo zameniti sa bilo kojim drugim frontendom (angular) bez da effectuje Flask
#   Flask moze da se zameni sa Django ili FastAPI bez uticaja na React

# Copy the package.json and package-lock.json from the my-app directory
# assuming your Dockerfile is in the `Frontend` folder
COPY ./my-app/package*.json ./


#install dependencies, Redux, react-dom
RUN npm install --legacy-peer-deps



#Kopiramo ostali code u image dockera
COPY ./my-app/ ./

#podsetnik dodatno procitati jos o docker cachiranju 
#zasto ovako 2 put kopiramo je zbog 
#1. Docker Cache Optimization:
#Docker caches layers during the build process. If you copy the package.json and package-lock.json files first, and run npm install at that stage, 
#Docker will only re-run npm install if either of those files changes. 
#This allows Docker to cache the npm install layer and avoid 
#unnecessary re-installation of dependencies if only your source code changes.

#2. Separation of Concerns:
#By copying the package.json first and running npm install before copying the rest of the application,
#Docker is able to avoid re-running npm install whenever there's a change in the app's code (i.e., source files). 
#If you copied everything in one step, even a minor code change would trigger npm install again, which is unnecessary if dependencies haven't changed.

#Layer Caching: Docker caches the result of each step. 
#When you run docker-compose build, Docker will cache the npm install step if there are no changes to the package.json files, 
#and only rebuild the application files (which could change more frequently).

#Performance: If you only copy the source code and run npm install every time,
# Docker will have to reinstall dependencies even when there's no change in package.json. 
#This can slow down your build times unnecessarily.


# OBRISATI U PRODUCTION-u ! ! ! 
# KLJUČNO: Ovde postavljamo varijable za React Development Server 
# HTTPS=true govori Reactu da aplikacija radi preko HTTPS-a.
# React dev server sluša na 3000, i tu mu šaljemo WebSockets

#ovo je fix bio za error sa WebSocket connection to 'wss://localhost:3000/ws' failed
ENV HTTPS=true \
    WDS_SOCKET_PORT=3000 \ 
    DANGEROUSLY_DISABLE_HOST_CHECK=true

#Expose port
EXPOSE 3000



#Start react app
CMD ["npm","start"]
