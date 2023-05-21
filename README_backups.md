# For local backup/restore: 
(replace the --volumes-from container name with the one corresponding to the mssql service)

`docker run --rm --volumes-from fc68389248ac -v mssql_backup:/backup ubuntu tar cvf /backup/mssql_backup.tar /var/opt/mssql`
## Restore:

`docker run --rm --volumes-from fc68389248ac -v mssql_backup:/backup ubuntu bash -c "cd / && tar xvf /backup/mssql_backup.tar"`