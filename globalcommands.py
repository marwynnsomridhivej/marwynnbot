import math
import os
import json

from discord.ext.commands import CommandInvokeError


class GlobalCMDS:

    def file_check(self, filenamepath, init):
        if not os.path.exists(filenamepath):
            with open(filenamepath, 'w') as f:
                for str in init:
                    f.write(str)

    def json_load(self, filenamepath, init):
        if not os.path.exists(filenamepath):
            with open(filenamepath, 'w') as f:
                json.dump(init, f, indent=4)

    def incrCounter(self, ctx, cmdName):
        init = {'Server': {}, 'Global': {}}

        self.json_load(self, "./counters.json", init)
        with open('counters.json', 'r') as f:
            values = json.load(f)

            try:
                values['Server'][str(ctx.guild.id)]
            except KeyError:
                values['Server'][str(ctx.guild.id)] = {}
            try:
                values['Server'][str(ctx.guild.id)][str(cmdName)]
            except KeyError:
                values['Server'][str(ctx.guild.id)][str(cmdName)] = 1
            else:
                values['Server'][str(ctx.guild.id)][str(cmdName)] += 1

            try:
                values['Global'][str(cmdName)]
            except KeyError:
                values['Global'][str(cmdName)] = 1
            else:
                values['Global'][str(cmdName)] += 1

        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

    def prefix(self, ctx):
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        return prefixes[str(ctx.guild.id)]

    def ratio(self, user, filenamepath, gameName):
        with open(filenamepath, 'r') as f:
            file = json.load(f)
            try:
                wins = file[str(gameName)][str(user.id)]['win']
            except KeyError:
                file[str(gameName)][str(user.id)]['ratio'] = 0
            else:
                try:
                    losses = file[str(gameName)][str(user.id)]['lose']
                except KeyError:
                    file[str(gameName)][str(user.id)]['ratio'] = 1
                else:
                    file[str(gameName)][str(user.id)]['ratio'] = round((wins / losses), 3)
        with open(filenamepath, 'w') as f:
            json.dump(file, f, indent=4)
