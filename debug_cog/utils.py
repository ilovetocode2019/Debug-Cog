from discord.ext import menus

import copy
import subprocess
import asyncio, async_timeout
import functools
import inspect
import os
import pathlib
import codecs

async def copy_context(ctx, author=None, channel=None, command=None):
    new_message = copy.copy(ctx.message)

    if channel:
        new_message.channel = channel
    if author:
        new_message.author = author

    if command:
        prefix = ctx.bot.command_prefix
        if inspect.isfunction(prefix):
            prefix = prefix(ctx.bot, new_message)
        if inspect.iscoroutinefunction(prefix):
            prefix = await prefix(ctx.bot, new_message)
        if isinstance(prefix, list):
            prefix = prefix[0]
        new_message.content = f"{prefix}{command}"

    new_ctx = await ctx.bot.get_context(message=new_message)


    return new_ctx

def python_codeblock(arg):
    section = ""
    code = ""
    ticks = 0
    after_ticks = False

    for counter, char in enumerate(arg):
        #If in codeblock but the same line as the starting ticks, add the charecter to after_ticks


        if char == "\n":
            if after_ticks != "py" and after_ticks != "python" and after_ticks:
                code += after_ticks

            after_ticks = False
            code += "\n"
        
        #If after and on the same line as starting ticks, add the charecter to after_ticks
        elif isinstance(after_ticks, str):
            after_ticks += char

        #If it's a tick add it to a possible string to add on to the code
        #Depending on how many ticks are found before other charecters it may not be a new codeblock
        elif char == "`":
            ticks += 1
            section += char
            
            #If ticks is 1 or 3 (the number of ticks to start a code block), ignore the ticks
            if ticks == 0 or ticks == 3:
                section = ""
                ticks = 0
                after_ticks = ""

        else:
            #If the ticks counter is not 0 but it's not 3 or 1 either (the number of ticks to start a code block), add the ticks to the code
            if ticks != 0 and ticks != 3 and ticks != 1:
                code += section
                section = ""
                ticks = 0
            
            #Add the current charecter
            code += char
    
    return code

def get_lines_of_code(comments=False):
    """Gets every single line in .py files in the directory and the number or .py files"""

    total_lines = 0
    file_amount = 0
    for path, subdirs, files in os.walk("."):
        if "venv" in subdirs:
            subdirs.remove("venv")
        if "env" in subdirs:
            subdirs.remove("env")
        if "venv-old" in subdirs:
            subdirs.remove("venv-old")
        for name in files:
            if name.endswith(".py"):
                file_amount += 1
                f = open(str(pathlib.PurePath(path, name)), encoding="utf-8")
                total_lines += len(f.readlines())
                f.close()
    return {"lines":total_lines, "files":file_amount}

class Shell:
    """A shell session for the shell command"""
    
    def __init__(self, command, loop=None):
        #Create tasks to get stdout
        self.loop = loop or asyncio.get_event_loop()
        self.queue = asyncio.Queue()

        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.stdout_loop = self.loop.create_task(self.get_stdout())
        except Exception as e:
            self.loop.create_task(self.queue.put(f"Error: {e}"))
    
    async def get_stdout(self):
        while True:
            #Get stdout
            partial = functools.partial(self.process.stdout.read)
            stdout = await self.loop.run_in_executor(None, partial)
            if stdout:
                await self.queue.put(stdout.decode("utf-8"))
        
    def __enter__(self):
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            async with async_timeout.timeout(50):
                return await self.queue.get()
        except asyncio.TimeoutError:
            raise StopAsyncIteration

    def __exit__(self, *args):
        #When no more stdout
        if hasattr(self, "process"):
            self.process.kill()
            self.process.terminate()
            self.stdout_loop.cancel()

class Interface(menus.Menu):
    async def send_initial_message(self, ctx, channel):
        self.data = ""
        self.pos = 0
        return await ctx.send(f"```bash\n$ ```")

    async def add_data(self, data):
        self.data += data
        await self.message.edit(content="```" + self.language + "\n" + self.data[self.pos:self.pos+500] + "```")

    async def set_language(self, language):
        self.language = language
        await self.message.edit(content="```" + self.language + "\n" + self.data[self.pos:self.pos+500] + "```")

    @menus.button("⬅️")
    async def last_page(self, payload):
        if self.data[self.pos - 500:self.pos] == "":
            return

        self.pos -= 500
        await self.message.edit(content="```" + self.language + "\n" + self.data[self.pos:self.pos+500] + "```")

    @menus.button("➡️")
    async def next_page(self, payload):
        if self.data[self.pos + 500:self.pos + 1000] == "":
            return

        self.pos += 500
        await self.message.edit(content="```" + self.language + "\n" + self.data[self.pos:self.pos+500] + "```")