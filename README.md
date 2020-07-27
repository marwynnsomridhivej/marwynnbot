# MarwynnBot
A Discord bot written in python using discord.py, a Discord API Wrapper.

## Add Me To Your Server
You can add the public MarwynnBot to your own Discord server by clicking [here](https://discord.com/oauth2/authorize?client_id=623317451811061763&scope=bot&permissions=8)

## Prefix
- The default prefix is `m!`
- Global prefixes are mentioning the bot or `mb`

## Commands
WIP, for an updated list, add the bot and do `m!help`.

For a guide on all commands and their usages, I will be updating [MarwynnBot's GitBook page](https://marwynn.gitbook.io/marwynnbot/)

Commands are separated into categories that determine a command's function. Below is a list that will be updated
frequently as the bot's functionality grows.

**Help**
- `help`

**Debug**
- `ping`
- `shard`

**Fun**
- `8ball`
- `choose`
- `gifsearch`
- `isabelle`
- `peppa`
- `say`
- `toad`

**Games**
- Currently under development

**Moderation**
- `chatclean`
- `mute`
- `unmute`
- `kick`
- `ban`
- `unban`
- `modsonline`

**Music**
- Currently under development
- `join`
- `leave`

**Utility**
- `prefix`
- `setprefix`
- `serverstats`
- `timezone`

## Self Hosting
For self hosting, you'll need:
- A bot application
- A bot token

bot.py has this line of code:
```
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
## Contact Info
**Discord:** MS Arranges#3060

**Discord Server:** https://discord.gg/fYBTdUp