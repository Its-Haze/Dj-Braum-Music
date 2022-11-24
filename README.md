<h1 align="center">Dj Braum ♪ - Discord Music Bot</h1>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]() [![Forks](https://img.shields.io/github/forks/Its-Haze/Dj-Braum-Music)]() [![Stars](https://img.shields.io/github/stars/Its-Haze/Dj-Braum-Music)]() [![GitHub Issues](https://img.shields.io/github/issues/Its-Haze/Dj-Braum-Music)](https://github.com/Its-Haze/Dj-Braum-Music/issues) [![GitHub Pull Requests](https://img.shields.io/github/issues-pr/kylelobo/The-Documentation-Compendium.svg)](https://github.com/Its-Haze/Dj-Braum-Music/pulls) [![License](https://img.shields.io/badge/license-MIT-purple.svg)](/LICENSE)

</div>

# ⭐ Introduction

Dj Braum is a free and open source discord bot with no pay-wall. Made using discord.py and wavelink.

- Invite the bot to your server!: [Click here to invite](https://discord.com/api/oauth2/authorize?client_id=939307188072116305&permissions=2150911040&scope=bot)

- Support Server : https://discord.gg/krVFr8vUrV

- Follow these steps from top to bottom.

- **Always** start Lavalink before starting the main.py

<br>

#  Discord

Join the official support server here https://discord.gg/dQwCc6tkvj

- Get help
- Talk code
- Test your bot & more

# Prerequisites

- Latest release of [Python3](https://www.python.org/) (3.11 is recommended)
- Java 17+ [Get it here](https://www.oracle.com/java/technologies/downloads/#java17)

# Local Development

Clone the Repository

```sh
$ git clone https://github.com/Its-Haze/Dj-Braum-Music.git
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

if `python -m pip install virtualenv` does not work, try replacing `python` with `py.exe`

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

Fill in [`.env`](https://github.com/Its-Haze/Dj-Braum-Music/blob/master/src/credentials/.env) with all the appropiate info. (Check the file)

# Install Java 17+

### **Java 17**

- Linux [Download](https://www.oracle.com/java/technologies/downloads/#jdk17-linux)
- Windows [Download](https://www.oracle.com/java/technologies/downloads/#jdk17-windows)

# Start Lavalink (Self host)

### This is needed for your bot to play music!

```bash
$ cd Dj-Braum-Music
$ cd src/lavalink
$ java -jar Lavalink.jar
```

When this is started, we can start the bot.

# Start the bot

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

# Things to think about

- Always remember to source/activate your virtual environment
  Read more about virtual environments here [Virtualenv](https://virtualenv.pypa.io/en/latest/user_guide.html)
- To run this bot 24/7 I recommend using a [raspberry pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) (Non affiliate link)
- Do not run this bot on Replit, Heroku and such.. they will give you more headache.
- If you find issues, please report them [here](https://github.com/Its-Haze/Dj-Braum-Music/issues)

<br>

# ✍️ Contributers

- [@Its-Haze](https://github.com/Its-Haze) - Creator

See also the list of [contributors](https://github.com/Its-Haze/Dj-Braum-Music/graphs/contributors) who participated in this project.

# 🖌️ Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

# 🎉 Acknowledgements

- This bot is a fork of the [Niko-Music bot](https://github.com/ZingyTomato/Niko-Music). So thank you ZingyTomato for making that project!
- Thanks to all the contributors of this project!
- Thanks to the [Python Discord server](https://discord.gg/python) for all help!
