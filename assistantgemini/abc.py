from abc import ABC
from redbot.core import commands


class MixinMeta(ABC):
    """
    A mixin base class for command mixins
    """
    pass


class CompositeMetaClass(type(commands.Cog)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """
    pass