@ECHO OFF
:: [PTS: AJUSTAR]
set psqlPath="C:\Program Files\PostgreSQL\14\bin"

:: Base de Dados e nome do utilizador
SET hostName=192.168.56.102
SET dataBase=postgres
SET userName=postgres

:: psql -h host -p port -d database -U user -f psqlFile
%psqlPath%\psql -h %hostName% -p 5432 -d %dataBase% -U %userName% -f %1

pause

