from extensions import app  # Umesto kreiranja novih objekata, uvozi ih
from Backend.API import *

import threading


from werkzeug.middleware.proxy_fix import ProxyFix


#ne zaboravi blueprinte da dodas



if __name__ =='__main__':
    app.run(host='0.0.0.0', port=5000,debug=True, threaded=True)#debug ->autoReload ako je promena u python code-u server se automatski restartuje, i debug console koju flask pokaze ako dodje do errora

