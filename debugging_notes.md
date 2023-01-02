Local debugging:
- recycle docker-compose up on changes to the python code
- connect to the sql db like so: `sqlcmd -U sa -P Your_password123`
- when ready to deploy, activate the annotations venv and pulumi up, then restart the app service.