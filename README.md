[![Codacy Badge](https://app.codacy.com/project/badge/Grade/41bbb30fede24aa09a3bb772cc4f4d7f)](https://www.codacy.com/manual/marwynnsomridhivej/marwynnbot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=marwynnsomridhivej/marwynnbot&amp;utm_campaign=Badge_Grade)
![License](https://img.shields.io/badge/license-GPLv3.0-brightgreen)
![Clone Size](https://img.shields.io/github/repo-size/marwynnsomridhivej/marwynnbot?color=red&label=Clone%20Size)
![GitHub stars](https://img.shields.io/github/stars/marwynnsomridhivej/marwynnbot?label=Stars&style=social)
![GitHub forks](https://img.shields.io/github/forks/marwynnsomridhivej/marwynnbot?label=Forks&style=social)

# MarwynnBot
A Discord bot written in python using discord.py, a Discord API Wrapper.

## Add Me To Your Server ![uptime](https://img.shields.io/badge/uptime-90.0%25-brightgreen)
You can add the public MarwynnBot to your own Discord server by clicking [here](https://discord.com/oauth2/authorize?client_id=623317451811061763&scope=bot&permissions=8)

## Prefix
- The default prefix is `m!`
- Global prefixes are mentioning the bot or `mb`

## Commands ![progress](https://img.shields.io/badge/coverage-20%25-orange)
WIP, for an updated list, add the bot and do `m!help`.

For a guide on all commands and their usages, I will be updating [MarwynnBot's GitBook page](https://marwynn.gitbook.io/marwynnbot/)

Commands are separated into categories that determine a command's function. Below is a list that will be updated
frequently as the bot's functionality grows.

**Help**
-   `help`

**Actions**
-   Check [here]((https://marwynn.gitbook.io/marwynnbot/)) for a full list
-   `actions`

**Debug**
-   `ping`
-   `report`
-   `shard`

**Fun**
-   `8ball`
-   `choose`
-   `gifsearch`
-   `imgursearch`
-   `isabelle`
-   `peppa`
-   `randomcat`
-   `randomdog`
-   `say`
-   `toad`

**Games**
-   `blackjack`
-   `coinflip`
-   `connectfour`
-   `slots`
-   `uno`
-   *Currently under development*

**Games Commands**
-   `balance`
-   `gamestats`
-   `transfer`

**Moderation**
-   `chatclean`
-   `mute`
-   `unmute`
-   `kick`
-   `ban`
-   `unban`
-   `modsonline`

**Music**
-   `join`
-   `leave`
-   *Currently under development*

**Utility**
-   `prefix`
-   `setprefix`
-   `serveremotes`
-   `serverstats`
-   `timezone`

**Owner Only**
-   `blacklist`
-   `load`
-   `unload`
-   `reload`
-   `shutdown`
-   `balanceadmin`

## Self Hosting
For self hosting, you'll need:
-   A bot application
-   A bot token

bot.py has this line of code:
```bash
with open('./token.yaml', 'r') as f:
    stream = yaml.full_load(f)
    token = stream[str('token')]
client.run(token)
```
You will need to create the token.yaml file in the root directory. File contents should be as follows:
```yaml
token: botTokenHere
```
The bot will pull the token value from the `token.yaml` file and use that as the token value in `client.run(token)`
## Contact Info ![Discord](https://img.shields.io/discord/707981159748993084?color=blue&label=Discord)
**Discord:** MS Arranges#3060

**Discord Server:** https://discord.gg/fYBTdUp