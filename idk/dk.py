from __future__ import annotations
from typing import Optional, ClassVar, Any
import discord
#from discord import Webhook, RequestsWebhookAdapter
from Config import logging_webhook
import json
import discord_games
from akinator import CantGoBackAnyFurther

from discord_games.aki import Akinator
from discord_games.utils import DiscordColor, DEFAULT_COLOR, BaseView
from typing import Optional, ClassVar, Any
from enum import Enum
import asyncio
from discord_games.aki import Akinator
from discord.ext import commands

from typing import Optional, ClassVar
from discord_games import button_games

import discord
from discord.ext import commands
from akinator import CantGoBackAnyFurther



class AkiButton(discord.ui.Button['AkiView']):

    async def callback(self, interaction: discord.Interaction) -> None:
        return await self.view.process_input(interaction, self.label.lower())

class AkiView(BaseView):
    OPTIONS: ClassVar[dict[str, discord.ButtonStyle]] = {
        'Yes': discord.ButtonStyle.green,
        'No': discord.ButtonStyle.red,
        'Idk': discord.ButtonStyle.blurple,
        'Probably': discord.ButtonStyle.gray,
        'Probably Not': discord.ButtonStyle.gray,
    }

    def __init__(self, game: BetaAkinator, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.embed_color: Optional[DiscordColor] = None
        self.game = game

        for label, style in self.OPTIONS.items():
            self.add_item(AkiButton(label=label, style=style))

        if self.game.back_button:
            delete = AkiButton(
                label='Back',
                style=discord.ButtonStyle.red,
                row=1
            )
            self.add_item(delete)

        if self.game.delete_button:
            delete = AkiButton(
                label='Cancel',
                style=discord.ButtonStyle.red,
                row=1
            )
            self.add_item(delete)

    async def process_input(self, interaction: discord.Interaction, answer: str) -> None:
        game = self.game

        if interaction.user != game.player:
            return await interaction.response.send_message(content="This isn't your game", ephemeral=True)

        if answer == "Cancel":
            await interaction.message.reply("Game Ended.", mention_author=True)
            self.stop()
            return await interaction.message.delete()

        if answer == "Back":
            try:
                await game.aki.back()
                embed = game.build_embed(instructions=False)
            except CantGoBackAnyFurther:
                return await interaction.response.send_message('I cant go back any further!', ephemeral=True)
        else:
            await game.aki.answer(str(answer))

            if game.aki.progression >= game.win_at:
                self.disable_all()
                embed = await game.win()
                self.stop()
            else:
                embed = game.build_embed(instructions=False)
        try:
            return await interaction.response.edit_message(embed=embed, view=self)
        except discord.NotFound:
            pass

button_games.aki_buttons.AkiView = AkiView


class BetaAkinator(Akinator):
    """
    Akinator(buttons) Game
    """
    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        back_button: bool = False,
        delete_button: bool = False,
        embed_color: DiscordColor = DEFAULT_COLOR,
        win_at: int = 80,
        timeout: Optional[float] = None,
        child_mode: bool = True,
        lang = "en"
    ) -> discord.Message:
        """
        starts the Akinator(buttons) game
        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            the context of the invokation command
        back_button : bool, optional
            indicates whether or not to add a back button, by default False
        delete_button : bool, optional
            indicates whether to add a stop button to stop the game, by default False
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        win_at : int, optional
            indicates when to tell the akinator to make it's guess, by default 80
        timeout : Optional[float], optional
            the timeout for the view, by default None
        child_mode : bool, optional
            indicates to filter out NSFW content or not, by default True
        Returns
        -------
        discord.Message
            returns the game message
        """
        self.back_button = back_button
        self.delete_button = delete_button
        self.embed_color = embed_color

        self.player = ctx.author
        self.win_at = win_at
        self.view = AkiView(self, timeout=timeout)
        self.lang = lang

        self.aki.child_mode = child_mode
        await self.aki.start_game(language=self.lang, child_mode=self.aki.child_mode)

        embed = self.build_embed(instructions=False)
        self.message = await ctx.send(embed=embed, view=self.view)

        await self.view.wait()
        return self.message


button_games.aki_buttons.BetaAkinator = BetaAkinator
