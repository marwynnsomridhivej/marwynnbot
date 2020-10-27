import asyncio
import re
from inspect import iscoroutine, iscoroutinefunction
from typing import Any, List, Union

import discord
from discord.ext import commands

from . import customerrors


__all__ = (
    "SetupPanel",
)


channel_tag_rx = re.compile(r'<#[0-9]{18}>')
channel_id_rx = re.compile(r'[0-9]{18}')
role_tag_rx = re.compile(r'<@&[0-9]{18}>')
hex_color_rx = re.compile(r'#[A-Fa-f0-9]{6}')
url_rx = re.compile(r'https?://(?:www\.)?.+')


class SetupPanel():
    def __init__(self, ctx: commands.Context, bot: commands.AutoShardedBot,
                 timeout: int = 30, name: str = "interactive", embed: discord.Embed = None,
                 has_intro: bool = False):
        self.bot = bot
        self.ctx = ctx
        self.author = ctx.author
        self.channel = ctx.channel
        self.guild = ctx.guild
        self.send = ctx.channel.send
        self.timeout = timeout
        self.name = name
        self.embed = embed
        self.has_intro = has_intro
        self.steps = []
        self.map = {
            "get_channel": self._from_user_channel,
            "get_message_content": self._from_user,
            "get_role": self._from_user_role,
            "get_hex": self._from_user_hex,
            "get_url": self._from_user_url,
        }

    def _from_user(self, message: discord.Message) -> bool:
        return message.author == self.author and message.channel == self.channel

    def _from_user_role(self, message: discord.Message) -> bool:
        if not re.match(role_tag_rx, message.content):
            return False
        return self._from_user(message)

    def _from_user_channel(self, message: discord.Message) -> bool:
        if not re.match(channel_tag_rx, message.content) or re.match(channel_id_rx, message.content):
            return False
        return self._from_user(message)

    def _from_user_hex(self, message: discord.Message) -> bool:
        if not re.match(hex_color_rx, message.content):
            return False
        return self._from_user(message)

    def _from_user_url(self, message: discord.Message) -> bool:
        if not re.match(url_rx, message.content):
            return False
        return self._from_user(message)

    async def intro(self, **options) -> None:
        embed = options.get("embed", self.embed)
        if not embed:
            raise ValueError("An embed must be provided for use in the intro")
        sleep_time = float(options.get("sleep_time", 3.0))
        await self.send(embed=embed)
        await asyncio.sleep(sleep_time)
        return

    def add_step(self, coro: callable, **options) -> None:
        if not iscoroutine(coro) or not iscoroutinefunction(coro):
            raise TypeError("Function must be a coroutine or a coroutine function")
        if options.get("ignore_error", False):
            async def ie_coro():
                try:
                    return await coro
                except Exception:
                    return options.get("default", None)
            self.steps.append(ie_coro)
        else:
            self.steps.append(coro)

    async def start(self, **options) -> List[Any]:
        if self.has_intro:
            await self.intro(**options)
        return [await coro for coro in self.steps]

    def get_channel(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int, **kwargs) -> int:
            provided = kwargs.get("provided", None)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user_channel, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided
            return int(response.content) if not "<#" in response.content else int(response.content[2:20])

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, provided=provided))

    def get_hex(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int, **kwargs) -> int:
            provided = kwargs.get("provided", None)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user_hex, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided
            return int(response.content[1:], 16)

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, provided=provided))

    def get_url(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int, **kwargs) -> str:
            provided = kwargs.get("provided", None)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user_url, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided
            return response.content

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, provided=provided))

    def get_message_content(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int, **kwargs) -> str:
            provided = kwargs.get("provided", False)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided
            return response.content

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, provided=provided))

    def get_role(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int,
                       obtain_type: str = "full", **kwargs) -> Union[discord.Role, int]:
            provided = kwargs.get("provided", False)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user_role, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided

            if obtain_type == "full":
                return self.guild.get_role(int(response.content[3:21]))
            else:
                return int(response.content[3:21])

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        obtain_type = options.get("obtain_type", "id")
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, obtain_type=obtain_type, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, obtain_type=obtain_type, provided=provided))

    def until_finish(self, coro: callable, **options) -> None:
        async def repeater(func: callable, **kwargs) -> List[Any]:
            values = []
            embed = kwargs.get("embed")
            timeout = kwargs.get("timeout", 30)

            def validate(message: discord.Message):
                checker = self.map[func.__name__]
                if checker(message):
                    return True
                return message.author == self.author and message.channel == self.channel

            while True:
                await self.send(embed=embed)
                try:
                    message = await self.bot.wait_for("message", check=validate, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
                if message.content == "finish":
                    break
                values.append(func(**kwargs, provided=message, immediate=True))
            return [task.result() for task in values]

        if iscoroutine(coro) or iscoroutinefunction(coro):
            raise TypeError("Please specify one of the setup functions")

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        self.add_step(repeater(coro, **options))
