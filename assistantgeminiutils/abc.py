from abc import ABC
from typing import get_type_hints

from redbot.core import commands


class MixinMeta(type):
    """
    A metaclass that allows ABCs to be used as mixins without
    conflicting with the metaclass used by `discord.py` and `redbot.core`
    """

    def __new__(mcs, name, bases, cls_dict):
        cls = super().__new__(mcs, name, bases, cls_dict)
        if ABC in bases:
            # If this is an ABC, remove it from the bases to avoid metaclass conflicts
            bases = tuple(base for base in bases if base is not ABC)
            cls = super().__new__(mcs, name, bases, cls_dict)
        return cls


class CompositeMetaClass(type(commands.Cog), MixinMeta):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

    pass 