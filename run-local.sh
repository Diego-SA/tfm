#no hace falta el contenedor si se instala ubuntu y redis para windows 10, ver:
#https://redislabs.com/blog/redis-on-windows-10/
# docker run  -p 6379:6379  --name redis-container -d redis

#lanzar mi contenedor tfm-diego-local enlazado con el contenedor de redis
winpty docker run -p 8000:8000 -it tfm-diego-local