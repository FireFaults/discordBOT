import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import random
import asyncio
from datetime import datetime, timedelta
import aiohttp

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_NAME = os.getenv("DISCORD_GUILD")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

WAARSCHUWINGEN = {}
SLECHTE_WOORDEN = [
    "shit", "kanker", "fuck", "lul", "klootzak", "sukkel", "idioot", "debiel", "homo",
    "tering", "mongool", "hoer", "flikker", "bitch", "eikel", "drol", "dwaas", "loser"
]
REMINDERS = []
MUTED = set()

def make_embed(title, desc, color=discord.Color.blurple()):
    return discord.Embed(title=title, description=desc, color=color, timestamp=datetime.utcnow())

def is_firefaults(ctx):
    return ctx.author.name.lower() == "firefaults"

@bot.event
async def on_ready():
    print(f"✅ Ingelogd als {bot.user}")
    await tree.sync()
    print("🔁 Slash commands gesynchroniseerd")
    check_reminders.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.author.id in MUTED:
        await message.delete()
        return
    for woord in SLECHTE_WOORDEN:
        if woord in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention}, je bericht is verwijderd wegens ongepaste taal.")
            return
    await bot.process_commands(message)

@tasks.loop(seconds=10)
async def check_reminders():
    now = datetime.utcnow()
    for r in REMINDERS[:]:
        if now >= r['tijd']:
            await r['user'].send(f"🔔 Herinnering: {r['bericht']}")
            REMINDERS.remove(r)

# --- SLASH COMMANDS VOOR FUN EN INFO (zichtbaar voor iedereen) ---

@tree.command(name="coinflip", description="Kop of munt")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(["🪙 Kop", "🪙 Munt"]))

@tree.command(name="dice", description="Gooi een dobbelsteen")
@app_commands.describe(max="Maximale waarde")
async def dice(interaction: discord.Interaction, max: int = 6):
    resultaat = random.randint(1, max)
    await interaction.response.send_message(f"🎲 Je gooide: {resultaat}")

@tree.command(name="reverse", description="Keer een zin om")
@app_commands.describe(tekst="Wat wil je omkeren?")
async def reverse(interaction: discord.Interaction, tekst: str):
    await interaction.response.send_message(tekst[::-1])

@tree.command(name="joke", description="Toon een mop")
async def joke(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://official-joke-api.appspot.com/random_joke") as resp:
            data = await resp.json()
            await interaction.response.send_message(f"{data['setup']} - {data['punchline']}")

@tree.command(name="quote", description="Toon een random quote")
async def quote(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.quotable.io/random") as resp:
            data = await resp.json()
            await interaction.response.send_message(f"💬 {data['content']} — *{data['author']}*")

@tree.command(name="remindme", description="Herinner me aan iets")
@app_commands.describe(tijd="Aantal minuten", bericht="Waar wil je aan herinnerd worden?")
async def remindme(interaction: discord.Interaction, tijd: int, bericht: str):
    wanneer = datetime.utcnow() + timedelta(minutes=tijd)
    REMINDERS.append({"tijd": wanneer, "bericht": bericht, "user": interaction.user})
    await interaction.response.send_message(f"⏰ Herinnering ingesteld over {tijd} minuten.")

# --- PREFIX COMMANDS VOOR ADMIN/MOD (NIET zichtbaar in slash lijst) ---

@bot.command()
async def say(ctx, *, boodschap: str):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    await ctx.message.delete()
    await ctx.send(boodschap)

@bot.command()
async def embed(ctx, titel: str, *, inhoud: str):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    await ctx.message.delete()
    embed = make_embed(titel, inhoud)
    await ctx.send(embed=embed)

@bot.command()
async def warn(ctx, member: discord.Member, *, reden: str):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    if member.id not in WAARSCHUWINGEN:
        WAARSCHUWINGEN[member.id] = []
    WAARSCHUWINGEN[member.id].append(reden)
    await ctx.send(f"⚠️ {member.mention} is gewaarschuwd: {reden}")

@bot.command()
async def warns(ctx, member: discord.Member):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    redenen = WAARSCHUWINGEN.get(member.id, [])
    if redenen:
        await ctx.send(f"{member.mention} heeft {len(redenen)} waarschuwingen:\n- " + "\n- ".join(redenen))
    else:
        await ctx.send(f"{member.mention} heeft geen waarschuwingen.")

@bot.command()
async def kick(ctx, member: discord.Member, *, reden: str = None):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    await member.kick(reason=reden)
    await ctx.send(f"👢 {member.mention} is gekickt.")

@bot.command()
async def ban(ctx, member: discord.Member, *, reden: str = None):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    await member.ban(reason=reden)
    await ctx.send(f"🔨 {member.mention} is verbannen.")

@bot.command()
async def unban(ctx, user_id: int):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"✅ {user} is ge-unbanned.")

@bot.command()
async def clear(ctx, aantal: int):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    deleted = await ctx.channel.purge(limit=aantal)
    await ctx.send(f"🧹 {len(deleted)} berichten verwijderd.", delete_after=5)

@bot.command()
async def mute(ctx, member: discord.Member, *, reden: str = None):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    MUTED.add(member.id)
    await ctx.send(f"🔇 {member.mention} is gedempt. Reden: {reden}")

@bot.command()
async def unmute(ctx, member: discord.Member):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    MUTED.discard(member.id)
    await ctx.send(f"🔊 {member.mention} is niet langer gedempt.")

@bot.command()
async def lock(ctx):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 Kanaal vergrendeld.")

@bot.command()
async def unlock(ctx):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 Kanaal ontgrendeld.")

@bot.command()
async def report(ctx, member: discord.Member, *, reden: str):
    mod_log = discord.utils.get(ctx.guild.text_channels, name="mod-log")
    if mod_log:
        embed = make_embed("🚨 Melding", f"**Gemeld door:** {ctx.author.mention}\n**Tegen:** {member.mention}\n**Reden:** {reden}")
        await mod_log.send(embed=embed)
        await ctx.send("✅ Gebruiker gemeld.", delete_after=5)
    else:
        await ctx.send("⚠️ Geen 'mod-log' kanaal gevonden.", delete_after=5)

# --- POLL COMMANDO ---

number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

@bot.command()
async def poll(ctx, vraag: str, *opties):
    if not is_firefaults(ctx):
        await ctx.send("⛔ Je hebt geen toegang tot dit commando.")
        return
    if len(opties) < 2:
        await ctx.send("⚠️ Je moet minstens 2 opties geven voor de poll.")
        return
    if len(opties) > 10:
        await ctx.send("⚠️ Maximaal 10 opties toegestaan.")
        return

    beschrijving = ""
    for i, optie in enumerate(opties):
        beschrijving += f"{number_emojis[i]} {optie}\n"

    embed = discord.Embed(title="📊 Poll", description=f"**{vraag}**\n\n{beschrijving}", color=discord.Color.blue())
    embed.set_footer(text=f"Poll gemaakt door {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    bericht = await ctx.send(embed=embed)
    for i in range(len(opties)):
        await bericht.add_reaction(number_emojis[i])

bot.run(TOKEN)
