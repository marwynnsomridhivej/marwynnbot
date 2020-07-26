import os
import json


class GlobalCMDS:

    def incrCounter(self, cmdName):
        if not os.path.exists('counters.json'):
            with open('counters.json', 'w') as f:
                f.write('{\n\n}')
        with open('counters.json', 'r') as f:
            values = json.load(f)
            try:
                values[str(cmdName)]
            except KeyError:
                values[str(cmdName)] = 1
            else:
                values[str(cmdName)] += 1
        with open('counters.json', 'w') as f:
            json.dump(values, f, indent=4)

    def prefix(self, ctx):
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        return prefixes[str(ctx.guild.id)]
