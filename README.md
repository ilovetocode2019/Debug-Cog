# Debug-Cog

A discordpy debug cog

# Setup

Install from GitHub:

`pip install git+https://github.com/ilovetocode2019/Debug-Cog`

# Usage

```python
from discord.ext import commands
import debug_cog

#Configure the name of the cog and command
debug_cog.configure(name="Debug")

#Create the bot and load the extension
bot = commands.Bot("test!")
bot.load_extension("debug_cog")
bot.run(TOKEN)
```