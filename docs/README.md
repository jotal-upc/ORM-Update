Some insights on how to run the program.

##  Installation process

### Python venv cheatsheet

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
Install requirements (inside venv):
```
    pip install -r requirements.txt
```


### MySql + Workbench

Install mysql & set root password:
```
    sudo apt install mysql-server
    sudo mysql -u root

    mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root';
```
Download link for mysql-workbench: https://dev.mysql.com/downloads/workbench/
Currently using: MySql-Workbench Community 8.0.34 


### Firefox + geckodriver

Extract the files in assets/firefox/:
```
    cd assets/firefox/
    tar -xvf geckodriver-v0.33.0-linux64.tar.gz --one-top-level
    tar -xvf firefox-115.5.0esr.tar.bz2 --one-top-level
```


### Other

Some other components that may be missing and are necessary:
```
    sudo apt install libmysqlclient-dev pkg-config xvfb
```
