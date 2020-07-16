import discord
from discord.ext import commands

import sys, traceback
import importlib
import ast
import datetime, humanize
import shlex, subprocess
import asyncio

from . import utils
import debug_cog

def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

class Debug(commands.Cog):
    def __init__(self, bot, name):
        self.bot = bot
        self.loaded_time = datetime.datetime.now()
        self.__cog_name__ = name
        self.debug_command.name = name.lower()
        self.debug_command.description = f"The command for the {name} cog"
        
        importlib.reload(utils)

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group(invoke_without_command=True)
    async def debug_command(self, ctx):
        py_version = sys.version_info
        py_version = f"{py_version.major}.{py_version.minor}{py_version.micro}"
        message = f"Debug {debug_cog.__version__} was loaded {humanize.naturaltime(self.loaded_time)} on python {py_version}, with discord.py {discord.__version__} (OS is {sys.platform})."
        message += f"\nBot can see {len(self.bot.guilds)} guild(s), {len(list(self.bot.get_all_channels()))} channel(s), and {len(self.bot.users)} user(s), Bot's latency is {round(self.bot.latency*1000, 2)}ms"
        await ctx.send(message)

    @debug_command.command(name="python", description="Run python code", aliases=["py", "eval"])
    async def debug_python(self, ctx, *, cmd: utils.python_codeblock):
        
        #Indent the code
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
        
        #Put it into a function
        body = f"async def eval_code():\n{cmd}"
        
        #Try and parse the code
        try:
            parsed = ast.parse(body)
        except SyntaxError as e:
            full =''.join(traceback.format_exception(type(e), e, e.__traceback__, 0))
            return await ctx.send(f"❗ Syntax Error:```py\n{full}```")

        body = parsed.body[0].body
        insert_returns(body)

        env = {
            "bot": ctx.bot,
            "discord": discord,
            "commands": commands,
            "ctx": ctx,
            "message": ctx.message,
            "author": ctx.author,
            "channel": ctx.channel,
            "guild": ctx.guild,
            '__import__': __import__
        }

        #Execute the function definition        
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        #Run the code and catch any errors
        try:
            result = (await eval(f"eval_code()", env))
        except Exception as e:
            await ctx.message.add_reaction("‼️")
            full =''.join(traceback.format_exception(type(e), e, e.__traceback__))
            
            return await ctx.author.send(f"‼️ Exception: ```py\n{full}```")
        
        #React with a check or send the result
        if not result:
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send(result)

    @debug_command.command(name="shell", description="Runs a command in the system shell", aliases=["sh", "terminal", "cmd"])
    async def debug_shell(self, ctx, *, command: utils.python_codeblock):
        msg = f"$ {command}"
        
        interface = utils.ShellInterface()
        await interface.start(ctx)
        
        command = shlex.split(command)
        with utils.Shell(command, self.bot.loop) as reader:
            async for x in reader:
                await interface.add_data(x)

    @debug_command.command(name="reload", description="Reload an extension")
    async def debug_reload(self, ctx, *, ext):
        try:
            self.bot.reload_extension(ext)
            await ctx.send(f"🔄 `Reloaded {ext}`")
        except Exception as e:
            error = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await ctx.send(f"⚠️\n```py\n{error}```")

    @debug_command.command(name="toggle", description="Disable/undisable a command")
    async def debug_disable(self, ctx, command):
        command = self.bot.get_command(command)
        if not command:
            await ctx.send("❌ Command not found")
        
        if not hasattr(command, "disabled") or not command.disabled:
            #Create a disabed check that automaticly returns False
            #Set command.disabled to False so next time the owner of the bot uses this command it enables the command
            def disable_check(ctx):
                return False

            command.disabled_check = disable_check
            command.disabled = True
            command.add_check(disable_check)
            await ctx.send(f"⛔ Disabled {command.name}")

        else:
            command.remove_check(command.disabled_check)
            await ctx.send(f"✅ Enabled {command.name}")

    @debug_command.command(name="in", description="Run a command in a different channel")
    async def debug_in(self, ctx, channel: discord.TextChannel, *, command):
        #Copy context with the new channel and new command content
        new_ctx = await utils.copy_context(ctx=ctx, channel=channel, content=f"{self.bot.command_prefix}{command}")

        if not new_ctx.command:
            return await ctx.send(f"❌ Command not found")

        await new_ctx.command.invoke(new_ctx)

    @debug_command.command(name="as", description="Run the command as a different member")
    async def debug_as(self, ctx, user: discord.Member, *, command):
        #Copy context with the new user and new command content
        new_ctx = await utils.copy_context(ctx=ctx, author=user, content=f"{self.bot.command_prefix}{command}")

        if not new_ctx.command:
            return await ctx.send(f"❌ Command not found")
        await new_ctx.command.invoke(new_ctx)
        
    @debug_command.command(name="logout", description="Logs out the bot")
    async def logout(self, ctx):
        print("Logging out of discord.")
        await ctx.send("Logging out 👋")
        await self.bot.logout()

def setup(bot):
    bot.add_cog(Debug(bot))