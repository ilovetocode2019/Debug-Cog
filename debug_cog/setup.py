from .cog import Debug
from . import config

def setup(bot):
    bot.add_cog(Debug(bot, name=config.name))

def configure(name="Debug"):
    config.name = name