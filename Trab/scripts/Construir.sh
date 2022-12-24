#!/bin/bash
host=localhost
db=postgres
user=postgres
# psql -h host -p port -d database -U user -f psqlFile
for f in ./*.sql
do
read -p "Press Enter to continue"
done;
