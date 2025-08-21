from AAA3A_utils import Cog  # isort:skip
from redbot.core import commands, Config  # isort:skip
from redbot.core.bot import Red  # isort:skip
from redbot.core.i18n import Translator, cog_i18n  # isort:skip
import discord  # isort:skip
import typing  # isort:skip

import io
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont
from redbot.core.data_manager import bundled_data_path

from .view import Lang, WordleGameView

# Credits:
# General repo credits.

_: Translator = Translator("Wordlev2", __file__)


@cog_i18n(_)
class Wordlev2(Cog):
    """Play a match of Wordle game, in multiple languages and lengths!"""

    def __init__(self, bot: Red) -> None:
        super().__init__(bot=bot)

        self.config: Config = Config.get_conf(
            self,
            identifier=205192943327321000143939875896557571750,
            force_registration=True,
        )
        self.config.register_member(
            wins=0,
            games=0,
            guess_distribution=[0] * 10,
        )

        self.words: typing.Dict[str, typing.Dict[int, typing.List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.dictionaries: typing.Dict[str, typing.Dict[int, typing.List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.font: ImageFont.FreeTypeFont = None

    async def cog_load(self) -> None:
        await super().cog_load()
        data_path = bundled_data_path(self)
        for lang in Lang:
            for dirname in ("words", "dictionaries"):
                with (data_path / dirname / f"{lang.value}.txt").open(
                    mode="rt", encoding="utf-8"
                ) as file:
                    for word in file.read().split("\n"):
                        if word == "cancel":
                            continue
                        getattr(self, dirname)[lang.value][len(word)].append(word)
        self.font = ImageFont.truetype(str(data_path / "ClearSans-Bold.ttf"), 80)

    @property
    def games(self) -> typing.Dict[discord.Message, WordleGameView]:
        return self.views

    async def generate_image(
        self,
        word: str,
        lang: Lang,
        attempts: typing.List[str] = [],
        max_attempts: int = 6,
    ) -> discord.File:
        length, size, between, border = len(word), 70, 10, 5
        
        # Track letter statuses for keyboard
        letter_status = {}  # letter -> color (priority: green > yellow > gray)
        
        # Language-specific keyboard layouts
        KEYBOARD_LAYOUTS: typing.Dict[Lang, typing.List[str]] = {
            Lang.ENGLISH: ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"],
            Lang.NEDERLANDS: ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"],
            Lang.INDONESIAN: ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"],
            Lang.GAEILGE: ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM", "ÁÉÍÓÚ"],
            Lang.FILIPINO: ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"],
            Lang.ITALIANO: ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"],
            Lang.PORTUGUES: ["QWERTYUIOP", "ASDFGHJKLÇ", "ZXCVBNM"],
            Lang.FRANCAIS: ["AZERTYUIOP", "QSDFGHJKLM", "WXCVBN"],
            Lang.DEUTSCH: ["QWERTZUIOPÜ", "ASDFGHJKLÖÄ", "YXCVBNMß"],
            Lang.ESPANOL: ["QWERTYUIOP", "ASDFGHJKLÑ", "ZXCVBNM"],
            Lang.SVENSKA: ["QWERTYUIOPÅ", "ASDFGHJKLÖÄ", "ZXCVBNM"],
            Lang.CESTINA: ["QWERTZUIOP", "ASDFGHJKL", "YXCVBNM", "ĚŠČŘŽÝÁÍÉŮŤŇ"],
            Lang.POLSKI: ["QWERTYUIOP", "ASDFGHJKLŁ", "ZXCVBNM", "ĄĆĘŃÓŚŹŻ"],
            Lang.TURKCE: ["QWERTYUIOPĞÜ", "ASDFGHJKLŞİ", "ZXCVBNMÖÇ"],
            Lang.ELLENIKA: [";"],  # Placeholder, will be overridden below
            Lang.RUSSIAN: ["ЙЦУКЕНГШЩЗХЪ", "ФЫВАПРОЛДЖЭ", "ЯЧСМИТЬБЮ"],
            Lang.UKRAIHCBKA: ["ЙЦУКЕНГШЩЗХЇ", "ФІВАПРОЛДЖЄ", "ЯЧСМИТЬБЮ"],
        }
        # Greek (modern Greek keyboard layout)
        KEYBOARD_LAYOUTS[Lang.ELLENIKA] = [
            "ΣΕΡΤΥΘΙΟΠ",
            "ΑΣΔΦΓΗΞΚΛ",
            "ΖΧΨΩΒΝΜ",
        ]
        
        keyboard_rows = KEYBOARD_LAYOUTS.get(
            lang, ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        )
        
        key_size = 50
        key_spacing = 5
        keyboard_height = len(keyboard_rows) * (key_size + key_spacing) + key_spacing
        keyboard_top_margin = 30
        
        # Calculate image dimensions
        grid_width = length * size + (length + 1) * between + 2 * border
        grid_height = max_attempts * size + (max_attempts + 1) * between + 2 * border
        
        # Make image wider to accommodate keyboard
        max_keyboard_width = max(len(r) for r in keyboard_rows) * (key_size + key_spacing) + key_spacing
        image_width = max(grid_width, max_keyboard_width + 2 * border)
        image_height = grid_height + keyboard_top_margin + keyboard_height
        
        image = Image.new("RGB", (image_width, image_height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Center the grid if keyboard is wider
        grid_offset_x = (image_width - grid_width) // 2 if image_width > grid_width else 0
        
        # Draw the word grid and track letter statuses
        for i, attempt in enumerate(attempts):
            for j in range(length):
                letter = attempt[j]
                if letter == word[j]:
                    color = (106, 170, 100)  # Green
                    letter_status[letter] = color  # Green has highest priority
                elif any(letter == word[k] and attempt[k] != word[k] for k in range(length)):
                    color = (202, 180, 86)  # Yellow
                    # Only update to yellow if not already green
                    if letter not in letter_status or letter_status[letter] != (106, 170, 100):
                        letter_status[letter] = color
                else:
                    color = (120, 124, 126)  # Grey
                    # Only update to grey if not already green or yellow
                    if letter not in letter_status:
                        letter_status[letter] = color
                        
                draw.rectangle(
                    [
                        (
                            grid_offset_x + border + (j + 1) * between + j * size,
                            border + (i + 1) * between + i * size,
                        ),
                        (
                            grid_offset_x + border + (j + 1) * between + (j + 1) * size,
                            border + (i + 1) * between + (i + 1) * size,
                        ),
                    ],
                    fill=color,
                )
                s = self.font.getlength(letter.upper())
                draw.text(
                    (
                        grid_offset_x + border + (j + 1) * between + j * size + size // 2 - s // 2,
                        border + (i + 1) * between + i * size - size * 0.36,
                    ),
                    letter.upper(),
                    font=self.font,
                    fill=(255, 255, 255),
                )
                
        # Draw empty grid cells
        for i in range(max_attempts - len(attempts)):
            for j in range(length):
                draw.rectangle(
                    [
                        (
                            grid_offset_x + border + (j + 1) * between + j * size,
                            border
                            + (len(attempts) + i + 1) * between
                            + (len(attempts) + i) * size,
                        ),
                        (
                            grid_offset_x + border + (j + 1) * between + (j + 1) * size,
                            border
                            + (len(attempts) + i + 1) * between
                            + (len(attempts) + i + 1) * size,
                        ),
                    ],
                    outline=(211, 214, 218),
                    width=3,
                )
        
        # Draw keyboard
        keyboard_font = ImageFont.truetype(str(bundled_data_path(self) / "ClearSans-Bold.ttf"), 30)
        keyboard_y = grid_height + keyboard_top_margin
        
        for row_idx, row in enumerate(keyboard_rows):
            # Calculate row offset for centering (2nd row is indented, 3rd+ row more)
            if row_idx == 1:  # middle row
                row_offset = key_size // 2
            elif row_idx >= 2:  # subsequent rows
                row_offset = key_size + key_spacing
            else:
                row_offset = 0
            
            # Center the row
            row_width = len(row) * (key_size + key_spacing) - key_spacing
            row_x = (image_width - row_width - row_offset) // 2 + row_offset
            
            for col_idx, letter in enumerate(row):
                key_x = row_x + col_idx * (key_size + key_spacing)
                key_y = keyboard_y + row_idx * (key_size + key_spacing)
                
                # Determine key color
                base_letter = letter.lower()
                if base_letter in letter_status:
                    key_color = letter_status[base_letter]
                else:
                    key_color = (211, 214, 218)  # Light gray for unused
                
                # Draw key background
                draw.rectangle(
                    [
                        (key_x, key_y),
                        (key_x + key_size, key_y + key_size)
                    ],
                    fill=key_color,
                )
                
                # Draw letter on key
                letter_width = keyboard_font.getlength(letter)
                text_color = (255, 255, 255) if base_letter in letter_status else (0, 0, 0)
                draw.text(
                    (
                        key_x + (key_size - letter_width) // 2,
                        key_y + (key_size - 30) // 2
                    ),
                    letter,
                    font=keyboard_font,
                    fill=text_color,
                )
        
        buffer = io.BytesIO()
        image.save(buffer, "png")
        buffer.seek(0)
        return discord.File(buffer, filename="wordle.png")

    async def get_kwargs(
        self,
        ctx: commands.Context,
        lang: Lang,
        word: str,
        attempts: typing.List[str] = [],
        max_attempts: int = 6,
    ) -> typing.Dict[
        typing.Literal["embed", "file", "allowed_mentions"],
        typing.Union[discord.Embed, discord.File, discord.AllowedMentions],
    ]:
        embed: discord.Embed = discord.Embed(
            title=_("{flag} Wordle Game - {attempts}/{max_attempts} attempts").format(
                flag=f":flag_{'gb' if lang is Lang.ENGLISH else lang.value}:",
                attempts=len(attempts),
                max_attempts=max_attempts,
            ),
            color=await ctx.embed_color(),
            timestamp=ctx.message.created_at,
        )
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar,
        )
        has_won, has_lost = word in attempts, len(attempts) == 6
        if has_won or has_lost:
            embed.add_field(
                name=_("You won!") if has_won else _("You lost!"),
                value=_("The word was: **{word}**.").format(word=word),
            )
        embed.set_footer(
            text=ctx.guild.name,
            icon_url=ctx.guild.icon,
        )
        file = await self.generate_image(word, lang, attempts, max_attempts=max_attempts)
        embed.set_image(url="attachment://wordle.png")
        return {
            "embed": embed,
            "file": file,
            "allowed_mentions": discord.AllowedMentions(replied_user=False),
        }

    @commands.max_concurrency(1, commands.BucketType.member)
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    @commands.hybrid_command(aliases=["wordlegame"])
    async def wordle(
        self,
        ctx: commands.Context,
        lang: typing.Optional[Lang] = Lang.ENGLISH,
        length: typing.Optional[commands.Range[int, 4, 11]] = 5,
        max_attempts: typing.Optional[commands.Range[int, 5, 10]] = 6,
    ) -> None:
        """Play a match of Wordle game.

        You can find the rules of the game by clicking on the button after starting the game.
        Available languages: `en`, `fr`, `de`, `es`, `it`, `pt`, `nl`, `cs`, `el`, `id`, `ie`, `ph`, `pl`, `ua`, `ru`, `sv` and `tr`.
        """
        has_won, attempts = await WordleGameView(
            self,
            lang=lang,
            length=length,
            max_attempts=max_attempts,
        ).start(ctx)
        data = await self.config.member(ctx.author).all()
        data["games"] += 1
        if has_won:
            data["wins"] += 1
            data["guess_distribution"][len(attempts) - 1] += 1
        await self.config.member(ctx.author).set(data)

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.command()
    async def wordlestats(
        self,
        ctx: commands.Context,
        *,
        member: discord.Member = commands.Author,
    ) -> None:
        """Show the stats for the Wordle game."""
        data = await self.config.member(member).all()
        embed = discord.Embed(
            title=_("Wordle Game Stats"),
            description=_(
                ">>> **Games played**: {games}\n**Wins**: {wins}\n**Win rate:** {win_rate:.2%}"
            ).format(
                games=data["games"],
                wins=data["wins"],
                win_rate=data["wins"] / data["games"] if data["games"] else 0,
            ),
            color=await ctx.embed_color(),
            timestamp=ctx.message.created_at,
        )
        embed.set_author(
            name=member.display_name,
            icon_url=member.display_avatar,
        )
        embed.set_thumbnail(url=member.display_avatar)
        if data["games"]:
            embed.add_field(
                name=_("Guess distribution:"),
                value="\n".join(
                    [
                        _("- **{count}** guess{es} with {i} attempts").format(
                            count=count, i=i + 1, es="es" if count > 1 else ""
                        )
                        for i, count in enumerate(data["guess_distribution"], start=1)
                        if count > 0
                    ]
                ),
            )
        embed.set_footer(
            text=ctx.guild.name,
            icon_url=ctx.guild.icon,
        )
        await ctx.send(embed=embed)
