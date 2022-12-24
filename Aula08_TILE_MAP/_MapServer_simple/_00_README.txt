================================================================================
:: Paulo Trigo Silva (PTS)
- use python, venv, virtual environment
- install, in venv, the driver database PostgreSQL
================================================================================
(1) set up a python, venv, virtual environment
(2) install psycopg2 driver (because tile-server needs database connection)
(3) always launch the tile-server within the venv



________________________________________________________________________________
(1) set up a python, venv, virtual environment

:: create venv, install and work
$ cd _MapServer_simple
$ python3.7 -m venv ./__vEnv_py3-7-2



________________________________________________________________________________
(2) install psycopg2 driver (because tile-server needs database connection)

:: the binary package is a practical choice for development and testing
:: but in production it is advised to use the package built from sources
$ cd _MapServer_simple
$ source __vEnv_py3-7-2/bin/activate
$ pip install --upgrade pip
$ pip install psycopg2

:: install the executable ONLY if the previous install fails
$ pip install psycopg2-binary


________________________________________________________________________________
(3) always launch the tile-server within the venv

$ cd _MapServer_simple
$ source __vEnv_py3-7-2/bin/activate

:: execute the tile-server within the venv
$ python mapServer_simple.py

:: when work finishes, deactivate the venv
$ deactivate

:: at the browser
http://localhost:8080


