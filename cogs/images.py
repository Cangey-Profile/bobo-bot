from __future__ import annotations

from typing import TYPE_CHECKING

from discord import StickerFormatType, DeletedReferencedMessage
from discord.ext.commands import PartialEmojiConverter, PartialEmojiConversionFailure, UserConverter, UserNotFound

from core import Cog, Regexs

if TYPE_CHECKING:
    from discord import Message, User, Member
    from core import BoboContext

class ImageResolver:
    __slots__ = ('ctx', 'static')

    def __init__(self, ctx: BoboContext, static: bool) -> None:
        self.ctx = ctx
        self.static = static

    async def check_attachments(self, message: Message) -> str | None:
        if embeds := message.embeds:
            for embed in embeds:
                if embed.type == 'image':
                    return embed.thumbnail.url
                elif embed.type == 'rich':
                    if url := embed.image.url:
                        return url
                    if url := embed.thumbnail.url:
                        return url
                elif embed.type == 'article':
                    if url := embed.thumbnail.url:
                        return url

        if attachments := message.attachments:
            for attachment in attachments:
                if attachment.height:
                    if attachment.filename.endswith('.gif') and self.static:
                        return None

                    return attachment.url
        
        if stickers := message.stickers:
            for sticker in stickers:
                if sticker.format is not StickerFormatType.lottie:
                    if sticker.format is StickerFormatType.apng and not self.static:
                        return sticker.url

        if message.content:
            if url := await self.parse_content(message.content):
                return url

        return None
    
    def to_avatar(self, author: User | Member) -> str:
        if self.static:
            return author.display_avatar.with_format('png').url
        
        return author.display_avatar.with_static_format('png').url
    
    async def parse_content(self, content: str) -> str | None:
        ctx = self.ctx
        static = self.static

        try:
            emoji = await PartialEmojiConverter().convert(ctx, content)
            
            if emoji.is_custom_emoji():
                if emoji.animated and not static:
                    return emoji.url
                
                return emoji.url.replace('.gif', '.png')
            
            try:
                return f'https://twemoji.maxcdn.com/v/latest/72x72/{ord(content):x}.png'
            except TypeError:
                pass
        except PartialEmojiConversionFailure:
            pass

        try:
            user = await UserConverter().convert(ctx, content)

            return self.to_avatar(user)
        except UserNotFound:
            pass

        content = content.strip('<>')

        if Regexs.URL_REGEX.match(content):
            return content

        return None


    async def get_image(self, arg: str | None = None) -> str:
        if ref := self.ctx.message.reference:
            message = ref.resolved

            if isinstance(message, DeletedReferencedMessage) and ref.message_id:
                message = await self.ctx.channel.fetch_message(ref.message_id)
            
            if message and not isinstance(message, DeletedReferencedMessage):
                if res := await self.check_attachments(message):
                    return res
        
        if res := await self.check_attachments(self.ctx.message):
            return res
        
        if not arg:
            return self.to_avatar(self.ctx.author)
        
        if res := await self.parse_content(arg):
            return res
        
        return self.to_avatar(self.ctx.author)


class Images(Cog):
    ...


setup = Images.setup
