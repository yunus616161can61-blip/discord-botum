import discord
from discord.ext import commands
import asyncio
import os
import json
import time

# --- AYARLAR ---
# 1. Adım: Yeni aldığın Token'ı tırnakların içine yapıştır.
TOKEN = "MTQ2MDAzODI0MTU5MDk2ODYwNg.G-uS3G.xvS8G0TdwEwV1nOi59YHl_Xmwj6f5tWCdEYuSE"

# Rütbe Sistemi
# Sol taraf: Gereken Dakika (Örn: 600 = 10 Saat)
# Sağ taraf: O rolün Discord ID'si
RUTBELER = {
    # --- ALT YETKİLİ ---
    600: 1459537081456922658,   # Hero Of Surface (10 Saat)
    1500: 1459537082270617795,  # Hiper Of Surface (25 Saat)
    2500: 1459537084090941697,  # Endless Of Surface (40 Saat)
    
    # --- ORTA YETKİLİ ---
    3500: 1459537080295100694,  # Chatty Of Surface
    5000: 1459537079376678952,  # Star Of Surface
    6500: 1459537078009204854,  # Crown Of The Head
    
    # --- ÜST YETKİLİ ---
    8000: 1459537076683804796,  # Lucifer Of Surface
    10000: 1459537075408994374, # Monster Of Surface
    
    # --- ALT YÖNETİM ---
    12500: 1459537072485437461, # Crazy Of Surface
    15000: 1459537071441055775, # Partner Of Surface
    18000: 1459537070740475978, # Chat Sorumlusu
    
    # --- ORTA YÖNETİM ---
    22000: 1459537068299391132, # Partner Manager
    26000: 1459537066776985701, # Sorun Çözücü
    30000: 1459537065506115917, # Ranger Of Surface
    
    # --- ÜST YÖNETİM KADROSU ---
    35000: 1459537090730659932, # Admin Of Surface
    40000: 1459537092614029576, # Moderator Of Surface
    50000: 1459537064398946399, # Supreme Of Surface
    60000: 1459537063404896379  # Discord Personeli (Final Rütbe)
}

# --- YENİ PYTHON SÜRÜMÜ YAMASI ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Tüm izinleri açıyoruz
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# Veritabanı Yönetimi
veriler = {}
ses_girisleri = {}

# Veritabanını yükle
if os.path.exists("database.json"):
    try:
        with open("database.json", "r", encoding="utf-8") as f:
            veriler = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        veriler = {}
else:
    veriler = {}

def verileri_kaydet():
    with open("database.json", "w", encoding="utf-8") as f:
        json.dump(veriler, f, indent=4)

@bot.event
async def on_ready():
    print("---------------------------------------")
    print(f"✅ {bot.user} TAM GÜÇLE AKTİF!")
    print(f"📊 İstatistik, Rütbe Silme ve Puan Sistemi Devrede.")
    print("---------------------------------------")
    await bot.change_presence(activity=discord.Game(name="Surface | .mestat"))

# --- RÜTBE SİSTEMİ (Eskiyi Sil, Yeniyi Ver) ---
async def rutbe_guncelle(member, puan, channel=None):
    # 1. Hak edilen en yüksek rütbeyi bul
    verilecek_rol_id = None
    for r_puan, r_id in sorted(RUTBELER.items()):
        if puan >= r_puan:
            verilecek_rol_id = r_id
    
    if not verilecek_rol_id: return 

    yeni_rol = member.guild.get_role(verilecek_rol_id)
    
    # 2. ESKİ RÜTBELERİ TEMİZLE
    tum_rutbeler = RUTBELER.values()
    for r_id in tum_rutbeler:
        if r_id != verilecek_rol_id: 
            eski_rol = member.guild.get_role(r_id)
            if eski_rol and eski_rol in member.roles:
                try:
                    await member.remove_roles(eski_rol)
                except:
                    pass # Yetki yetmezse devam et

    # 3. YENİ ROLÜ VER
    if yeni_rol and yeni_rol not in member.roles:
        try:
            await member.add_roles(yeni_rol)
            if channel:
                await channel.send(f"👑 Tebrikler {member.mention}! **{yeni_rol.name}** rütbesine terfi ettin! (Eskiler alındı)")
            print(f"TERFİ: {member.name} -> {yeni_rol.name}")
        except Exception as e:
            print(f"HATA: Rol verilemedi. Botun rolünü sunucu ayarlarında en üste taşı! Hata: {e}")

# --- OTOMATİK PUAN KAZANMA ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    uid = str(message.author.id)
    
    if uid not in veriler: veriler[uid] = {"voice": 0, "messages": 0, "bonus": 0}
    veriler[uid]["messages"] += 1
    verileri_kaydet()
    
    puan = veriler[uid]["messages"] + veriler[uid]["voice"] + veriler[uid].get("bonus", 0)
    await rutbe_guncelle(message.author, puan, message.channel)
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot: return
    uid = str(member.id)
    
    # Sese giriş
    if before.channel is None and after.channel is not None:
        ses_girisleri[uid] = time.time()
        
    # Sesten çıkış
    elif before.channel is not None and after.channel is None:
        if uid in ses_girisleri:
            giris = ses_girisleri.pop(uid)
            dakika = int((time.time() - giris) / 60)
            
            if dakika > 0:
                if uid not in veriler: veriler[uid] = {"voice": 0, "messages": 0, "bonus": 0}
                veriler[uid]["voice"] += dakika
                verileri_kaydet()
                
                puan = veriler[uid]["messages"] + veriler[uid]["voice"] + veriler[uid].get("bonus", 0)
                await rutbe_guncelle(member, puan)

# --- KOMUTLAR ---
@bot.command()
async def mestat(ctx, member: discord.Member = None):
    """Gelişmiş İstatistik Paneli"""
    target = member or ctx.author
    uid = str(target.id)
    
    if uid not in veriler:
        await ctx.send(f"🚫 {target.name} verisi yok.")
        return

    d = veriler[uid]
    bonus = d.get("bonus", 0)
    toplam = d["voice"] + d["messages"] + bonus
    
    # Rütbe ve Hedef
    suanki = "Başlangıç"
    hedef = "Zirvedesin! 👑"
    kalan = 0
    ilerleme = 0
    
    for p, r in sorted(RUTBELER.items()):
        if toplam >= p:
            ro = ctx.guild.get_role(r)
            if ro: suanki = ro.name
            
    for p, r in sorted(RUTBELER.items()):
        if p > toplam:
            ro = ctx.guild.get_role(r)
            hedef = ro.name if ro else "???"
            kalan = p - toplam
            ilerleme = int((toplam / p) * 100)
            break
            
    embed = discord.Embed(title=f"📊 {target.name} İstatistikleri", color=0xffd700)
    embed.add_field(name="🏅 Rütbe", value=suanki, inline=False)
    embed.add_field(name="Puan Detayı", value=f"💬 Mesaj: {d['messages']}\n🎙️ Ses: {d['voice']}\n✨ Bonus: {bonus}", inline=False)
    embed.add_field(name="🏆 TOPLAM", value=f"**{toplam}**", inline=False)
    
    if kalan > 0:
        bar = "🟩" * int(ilerleme/10) + "⬜" * (10 - int(ilerleme/10))
        embed.add_field(name=f"🚀 Hedef: {hedef}", value=f"{bar} %{ilerleme}\nKalan Puan: **{kalan}**", inline=False)
        
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def puanver(ctx, member: discord.Member, miktar: int):
    uid = str(member.id)
    if uid not in veriler: veriler[uid] = {"voice": 0, "messages": 0, "bonus": 0}
    veriler[uid]["bonus"] = veriler[uid].get("bonus", 0) + miktar
    verileri_kaydet()
    
    puan = veriler[uid]["messages"] + veriler[uid]["voice"] + veriler[uid]["bonus"]
    await ctx.send(f"✅ {member.mention} +{miktar} Bonus verildi. Yeni Puan: {puan}")
    await rutbe_guncelle(member, puan, ctx.channel)

@bot.command()
@commands.has_permissions(administrator=True)
async def puanal(ctx, member: discord.Member, miktar: int):
    uid = str(member.id)
    if uid in veriler:
        veriler[uid]["bonus"] = veriler[uid].get("bonus", 0) - miktar
        verileri_kaydet()
        puan = veriler[uid]["messages"] + veriler[uid]["voice"] + veriler[uid]["bonus"]
        await ctx.send(f"⚠️ {member.mention} -{miktar} Puan silindi.")
        await rutbe_guncelle(member, puan)

@bot.command()
@commands.has_permissions(administrator=True)
async def terfi(ctx, member: discord.Member, rol: discord.Role):
    """Manuel olarak rütbe verir"""
    await member.add_roles(rol)
    await ctx.send(f"👑 {member.mention} kullanıcısına {rol.name} verildi!")

# Botu çalıştır (Yukarıdaki TOKEN değişkenini kullanır)
if TOKEN == "BURAYA_YENI_TOKENI_YAPISTIR":
    print("HATA: Lütfen main.py dosyasındaki TOKEN değişkenine kendi bot token'ını yapıştır!")
else:
    bot.run(TOKEN)