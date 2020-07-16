from discord.ext import menus

import copy
import subprocess
import asyncio, async_timeout
import functools

async def copy_context(ctx, author=None, channel=None, content=None):
    new_message = copy.copy(ctx.message)

    if content:
        new_message.content = content

    if channel:
        new_message.channel = channel
    if author:
        new_message.author = author

    new_ctx = await ctx.bot.get_context(message=new_message)

    if channel:
        new_ctx.channel = channel
    if author:
        new_ctx.author = author

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

class Shell:
    """A shell session for the shell command"""
    
    def __init__(self, command, loop=None):
        #Create tasks to get stdout
        self.loop = loop or asyncio.get_event_loop()
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.queue = asyncio.Queue()
        self.stdout_loop = self.loop.create_task(self.get_stdout())
    
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
        self.process.kill()
        self.process.terminate()
        self.stdout_loop.cancel()

class ShellInterface(menus.Menu):
    async def send_initial_message(self, ctx, channel):
        self.data = ""
        self.pos = 0
        return await ctx.send(f"```bash\n$ ```")

    async def add_data(self, data):
        self.data += data
        await self.message.edit(content="```bash\n" + self.data[self.pos:self.pos+500] + "```")

    @menus.button("⬅️")
    async def last_page(self, payload):
        if self.pos >= 0:
            self.pos -= 500
        await self.message.edit(content="```bash\n" + self.data[self.pos:self.pos+500] + "```")

    @menus.button("➡️")
    async def next_page(self, payload):
        if (len(self.data)-1)+500 >  self.pos+500:
            self.pos += 500
        await self.message.edit(content="```bash\n" + self.data[self.pos:self.pos+500] + "```")
