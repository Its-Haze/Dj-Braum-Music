# Dj Braum


## Introduction
Dj Braum is a free and open source discord bot with no pay-wall. Made using discord.py and wavelink.


Invite the bot to your server!: [Click here to invite](https://discord.com/api/oauth2/authorize?client_id=939307188072116305&permissions=2150911040&scope=bot)


Support Server : https://discord.gg/krVFr8vUrV
 

<br>

# Local Development

Clone the Repository
```sh
$ git clone https://github.com/Erik-Avakian/Dj-Braum-Music
```
Enter Dj-Braum-Music and install all the requirements using

### Windows
```sh
# Do not include the "$" in your commands.
# Execute each command one by one.
$ cd Dj-Braum-Music
$ python -m pip install virtualenv
$ python -m virtualenv venv
$ cd .\venv\Scripts\
$ .\activate
$ cd ../..
$ python -m pip install -r requirements.txt
```

### Alternative for Windows
if ```python -m pip install virtualenv``` does not work, try replacing ```python``` with ```py.exe```
```sh
$ cd Dj-Braum-Music
$ py.exe -m pip install virtualenv
$ py.exe -m virtualenv venv
$ cd .\venv\Scripts\
$ .\activate
$ cd ../..
$ py.exe -m pip install -r requirements.txt
```


### Linux & Mac
```bash
$ cd Dj-Braum-Music
$ python3 -m pip install virtualenv
$ python3 -m pip virtualenv venv
$ source venv/bin/activate
$ pip3 install -Ur requirements.txt
```
Fill in [`.env`](https://github.com/Erik-Avakian/Dj-Braum-Music/master/src/credentials/.env) with all the appropiate info. (Check the file)


## Install Java 17+

### __Java 17__
- Linux [Download](https://www.oracle.com/java/technologies/downloads/#jdk17-linux)
- Windows [Download](https://www.oracle.com/java/technologies/downloads/#jdk17-windows)


## Start Lavalink (Self host)
### This is needed for your bot to play music!

```bash
$ cd Dj-Braum-Music
$ cd src/lavalink
$ java -jar Lavalink.jar
```
When this is started, we can start the bot.

## Start the bot
### Windows
```bash
$ cd Dj-Braum-Music
$ python .\main.py
```

### Linux & Mac
```bash
$ cd Dj-Braum-Music
$ python3 main.py
```