from typing import List, NamedTuple, Tuple, Union

import discord
from discord.ext.commands import Context

from .paginator import SubcommandPaginator


class EntryData(NamedTuple):
    usage: str = None
    returns: str = None
    aliases: List[str] = None
    note: str = None


class SubCommandEntry(object):
    __slots__ = [
        "name",
        "pfx",
        "_usage",
        "_returns",
        "_aliases",
        "_note",
        "inline",
    ]

    def __init__(self, name: str, pfx: str, data: EntryData, inline: bool = False) -> None:
        self.name = name
        self.pfx = pfx
        self._usage = data.usage
        self._returns = data.returns
        self._aliases = data.aliases
        self._note = data.note
        self.inline = inline

    @property
    def usage(self) -> str:
        return f"**Usage:** `{self.pfx} {self._usage}`"

    @usage.setter
    def set_usage(self, usage: str) -> None:
        self._usage = usage

    @property
    def returns(self) -> str:
        return f"**Returns:** {self._returns}"

    @returns.setter
    def set_returns(self, returns: str) -> None:
        self._returns = returns

    @property
    def aliases(self) -> str:
        return f"**Aliases:** {self._aliases}"

    @usage.setter
    def set_usage(self, aliases: str) -> None:
        self._aliases = " ".join(f"`{alias}`" for alias in aliases)

    @property
    def note(self) -> str:
        return f"**Note:** {self._note}"

    @note.setter
    def set_note(self, note: str) -> None:
        self._note = note

    @property
    def all(self) -> Tuple[str, List[str], bool]:
        return self.name, [
            getattr(self, attr) for attr in [
                "usage", "returns", "aliases", "note"
            ] if getattr(self, f"_{attr}")
        ], self.inline


class SubcommandHelp(object):
    __slots__ = [
        "pfx",
        "title",
        "description",
        "per_page",
        "entries",
        "show_entry_count",
        "embed",
    ]

    def __init__(self, pfx: str, title: str = None, description: str = None,
                 per_page: int = 3, show_entry_count: bool = False,
                 embed: discord.Embed = None) -> None:
        self.pfx = str(pfx)
        self.title = str(title)
        self.description = str(description)
        self.per_page = per_page
        self.entries: List[SubCommandEntry] = []
        self.show_entry_count = show_entry_count
        self.embed = embed

    def add_entry(self, name: str, data: Union[EntryData, dict], inline: bool = False) -> "SubcommandHelp":
        self.entries.append(
            SubCommandEntry(
                name,
                self.pfx,
                data if isinstance(data, EntryData) else EntryData(**dict),
                inline
            )
        )
        return self

    def _prepare_embed(self, embed: discord.Embed) -> discord.Embed:
        if not embed:
            return discord.Embed(title=self.title,
                                 description=self.description,
                                 color=discord.Color.blue())
        return self.embed

    async def show_help(self, ctx: Context) -> discord.Message:
        self.embed = self._prepare_embed(self.embed)
        return await SubcommandPaginator(
            ctx,
            entries=[entry.all for entry in self.entries],
            per_page=self.per_page,
            show_entry_count=self.show_entry_count,
            embed=self.embed,
        ).paginate()
