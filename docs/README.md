Some insights on how to run the program.

## Python virtual environment

Creation:
```
    sudo apt install python3-virtualenv
    virtualenv orm-env --python=3.10
```
Activation/deactivation:
```
    source orm-env/bin/activate
    deactivate
```


## MySql + Workbench
```
    sudo apt install mysql-server
```

Set root password:
```
    sudo mysql -u root
```
& then run this command inside MySql Monitor:
```
    ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root';
```


Download link for mysql-workbench: https://dev.mysql.com/downloads/workbench/
```
    MySql-Workbench Community 8.0.34
```


## Other

If pip3 throws an error while trying to install mysqlclient, try:
```
    sudo apt install libmysqlclient-dev pkg-config    
```

Need to add geckodriver folder path for it to work:
```
    export PATH=$PATH:/path/to/geckodriver/folder
```

Other:
```
    sudo apt install xvfb
```
