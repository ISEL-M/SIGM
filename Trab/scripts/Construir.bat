@ECHO OFF
SET host=192.168.56.102
SET db=postgres
SET user=postgres

:: psql -h host -p port -d database -U user -f psqlFile
for /r %%f in (*.sql) do psql -h %host% -p 5432 -d %db% -U %user% -f %%f

pause