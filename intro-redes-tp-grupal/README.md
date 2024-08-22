# intro-redes-tp-grupal

## Requisitos
- Python 3.10
- Mininet (Opcional)

## Correr

Dentro de la carpeta de este archivo

### Server

``` bash
~ python src/start-server.py -H -p -s [-q] [-v]

-q, --quiet Decreases the output of the logging of the application
-v, --verbose Increases the output of the logging of the application. Takes precedence over -q
-H, --host service IP address
-p, --port service port
-s, --storage storage dir path
```

### Upload

``` bash
~ python src/upload.py -H -p -s [-q] [-v]

-q, --quiet Decreases the output of the logging of the application
-v, --verbose Increases the output of the logging of the application. Takes precedence over -q
-H, --host server IP address
-p, --port server Port
-s, --src Complete path to the file that will be uploaded
-n, --name Name of how the file will be saved in the server
```

### Download

``` bash
~ python src/upload.py -H -p -s [-q] [-v]

-q, --quiet Decreases the output of the logging of the application
-v, --verbose Increases the output of the logging of the application. Takes precedence over -q
-H, --host server IP address
-p, --port server Port
-s, --dst Source path where the file will be saved
-n, --name Name of how the file will be saved in the server
```


### Mininet 
``` bash
~sudo mn --custom topologia/topo.py --topo fiuba-ftp-topo --mac -x
```
