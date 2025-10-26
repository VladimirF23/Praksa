
#main.py
from extensions import app,socketio  # Umesto kreiranja novih objekata, uvozi ih
from Backend.API import *
#from Backend.Service import LiveMeteringWebSocket



import threading


from werkzeug.middleware.proxy_fix import ProxyFix

# region ProxyFix,Gunicorn 
# Posto koristim reverse proxy nginx-a moze doci do problema sa prepoznavanjem IP originalnih adresa klienata i originalnog protokola HTTP/HTTPS sa strane python flask aplikacije
# posto ce on videti izvnornu adresu request-a kao IP adresa Nginx-a container-a pa cu koristiti proxy fix, nginx dodaje header-e dodatne za pravi IP usera
# protokol koji se koritsti HTTPS/HTTP, i zato cu koristiti proxyFIx moze se koristiti i u dev-u i u production-u

# Taj IP se koristi za tipa logovanje user-ovih IP-a, da se prikaze user-ov IP, da se vidi da li je HTTP/HTTPS
# A NE KORISTISE  se da Flask salje nazad na taj IP odgovor, nginx uspostavi TCP/IP vezu za Flask-App i onda preko tog socket-a salje request, a Flask-app salje odgovor na taj socket
# nginx isto ima TCP/IP vezu za web browserom klienta pa njemu vraca odgovor isto preko socket-a

app.wsgi_app = ProxyFix(app.wsgi_app,x_for=1, x_proto=1,x_host=1)


#ne zaboravi blueprinte da dodas
app.register_blueprint(registration_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(iot_bp)
app.register_blueprint(battery_bp)

# app.register_blueprint(live_metering_bp)



#

if __name__ =='__main__':
    # Start SocketIO instead of Flask's built-in run


    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True
    )
