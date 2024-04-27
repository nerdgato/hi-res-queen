import discord
from discord.ext import commands
import os
import asyncio
import json
from mutagen import File
from difflib import SequenceMatcher
from decouple import config

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
        self.now_playing = None
        self.song_database = None
        self.disconnect_timer = None  # Temporizador de desconexión
        self.folder_id = config("FOLDER")  # FOLDER_ID de OneDrive
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog de Comandos cargado correctamente.")
        self.load_song_database()  # Cargamos la base de datos de canciones cuando el bot está listo
    
    def load_song_database(self):
        # Cargamos la base de datos de canciones desde el archivo JSON
        with open("data/song_database.json", "r") as f:
            self.song_database = json.load(f)
    
    @commands.command(brief="Recarga la base de datos de canciones desde el archivo JSON.", help="Recarga la base de datos de canciones desde el archivo JSON.", aliases=["rdb", "RDB"])
    async def reload_database(self, ctx):
        self.load_song_database()
        image_url = "https://imgur.com/Zk27ucC.png"
        cantidad = len(self.song_database)-10
        embed = discord.Embed(
                title="Base de datos Recargada",
                description=f"Se ha actualizado la lista de canciones.",
                color=discord.Color.from_rgb(255, 255, 255)  # Color azul por defecto
            )
        embed.add_field(name="Canciones", value=cantidad, inline=True)
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)
    @commands.command(brief="Conecta el bot al canal de voz.", help="Conecta el bot al canal de voz.", aliases=["j", "J"])
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            print(f"Bot conectado al canal de voz: {channel}")
            # Cuando el bot se una al canal, iniciamos el temporizador
            self.reset_disconnect_timer()
        else:
            await ctx.send("Primero debes estar en un canal de voz.")
    
    @commands.command(brief="Desconecta el bot del canal de voz.", help="Desconecta el bot del canal de voz.",aliases=["l", "L"])
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.song_queue.clear()
            self.cancel_disconnect_timer()  # Cancela el temporizador de desconexión si existe
            print("Bot desconectado del canal de voz.")
        else:
            await ctx.send("No estoy en un canal de voz... 🥱")
        # Cancela el temporizador de desconexión si se ejecuta el comando !leave
        self.cancel_disconnect_timer()

    @commands.command(brief="Añade una canción por nombre de archivo.", help="Añade una canción por nombre de archivo.\n\nParámetros:\n-s: Buscar por título de la canción.\n-a: Buscar por nombre del artista.\n-l: Buscar por nombre del álbum.", aliases=["p", "P"])
    async def play(self, ctx, *, query):
        # Convertir todos los comandos y argumentos a minúsculas
        query = query.lower()
        if not ctx.voice_client:
            await ctx.invoke(self.join)
            # Inicia el temporizador solo si el bot se une al canal de voz
            self.reset_disconnect_timer()
        
        target_songs = await self.parse(query, ctx)
        self.song_queue.extend(target_songs)
        thumbnail_url = "https://imgur.com/IKsan7z.png"

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.play_song(ctx)
        else:
            # Obtener el título de la última canción agregada a la cola
            last_song_data = target_songs[-1]
            last_song_title = last_song_data["title"]
            last_artist = last_song_data["artist"]
            # Crear un mensaje embed para notificar que la canción se ha agregado a la cola
            embed = discord.Embed(
                title="Canción Agregada a la Cola",
                description=f"La canción **{last_song_title}** de **{last_artist}** se ha agregado a la cola.",
                color=discord.Color.from_rgb(255, 255, 255)  # Color azul por defecto
            )
            embed.set_thumbnail(url=thumbnail_url)
            await ctx.send(embed=embed)
    
    async def parse(self, query, ctx):
        play_args = query.split(" ")
        target_songs = []

        if "-s" in play_args:
            song_index = play_args.index("-s") + 1
            song_query = " ".join(play_args[song_index:])
            target_songs = self.search_by_song(song_query)

            # Calcular la puntuación de cada canción basada en la similitud del título con la consulta
            for song in target_songs:
                song["score"] = self.calculate_similarity(song["title"], song_query)

            # Ordenar las canciones por puntuación de mayor a menor
            target_songs.sort(key=lambda x: x["score"], reverse=True)

            if len(target_songs) > 1:  # Si hay más de una canción con el mismo nombre
                # Crear un mensaje embed con la lista de canciones
                thumbnail_url = "https://imgur.com/cG8hTZe.png"
                embed = discord.Embed(
                    title="Múltiples Canciones Encontradas",
                    description="Se encontraron varias canciones con ese nombre. Por favor, elige una:",
                    color=discord.Color.from_rgb(255, 255, 255)  # Color azul por defecto
                )
                embed.set_thumbnail(url=thumbnail_url)
                for i, song_data in enumerate(target_songs, start=1):
                    embed.add_field(name=f"{i}. {song_data['artist']} - {song_data['title']}", value=f"", inline=False)
                message = await ctx.send(embed=embed)

                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                try:
                    response = await self.bot.wait_for('message', check=check, timeout=30.0)  # Esperar la respuesta del usuario durante 30 segundos

                    # Verificar si la respuesta es un número entero válido dentro del rango de opciones
                    choice = int(response.content)
                    if 1 <= choice <= len(target_songs):
                        # Obtener la canción seleccionada
                        selected_song = target_songs[choice - 1]
                        # Agregar la canción a la cola
                        self.song_queue.append(selected_song)
                        # Reproducir la canción si no hay ninguna reproduciéndose
                        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                            await self.play_song(ctx)
                        else:
                            # Crear un mensaje embed para notificar que la canción se ha agregado a la cola
                            thumbnail_url = "https://imgur.com/IKsan7z.png"
                            
                            last_song_title = selected_song["title"]
                            last_artist = selected_song["artist"]
                            
                            embed = discord.Embed(
                                title="Canción Agregada a la Cola",
                                description=f"La canción **{last_song_title}** de **{last_artist}** se ha agregado a la cola.",
                                color=discord.Color.from_rgb(255, 255, 255)  # Color azul por defecto
                            )
                            embed.set_thumbnail(url=thumbnail_url)
                            await ctx.send(embed=embed)
                                            
                        # # Reproducir la canción si no hay ninguna reproduciéndose
                        # if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                        #     await self.play_song(ctx)
                    else:
                        await ctx.send("El número ingresado no corresponde a una canción válida.")
                except asyncio.TimeoutError:
                    await ctx.send("Se ha agotado el tiempo para seleccionar una canción.")
                return 


        elif "-a" in play_args:
            artist_index = play_args.index("-a") + 1
            artist_query = " ".join(play_args[artist_index:])
            target_songs.extend(self.search_by_artist(artist_query))
        elif "-l" in play_args:
            album_index = play_args.index("-l") + 1
            album_query = " ".join(play_args[album_index:])
            target_songs.extend(self.search_by_album(album_query))

        return target_songs

    def search_by_artist(self, artist_query):
        return [song for song in self.song_database if artist_query.lower() in song["artist"].lower()]

    def search_by_album(self, album_query):
        return [song for song in self.song_database if album_query.lower() in song["album"].lower()]

    def search_by_song(self, song_query):
        return [song for song in self.song_database if song_query.lower().replace("'", "") in song["title"].lower().replace("'", "")]

    def calculate_similarity(self, title, query):
        # Calcular la similitud utilizando la función ratio de SequenceMatcher
        similarity = SequenceMatcher(None, title.lower(), query.lower()).ratio()
        return similarity
    
    async def play_selected_song(self, ctx, song_data):
        try:
            filepath = song_data["filepath"]
            print(f"Ruta del archivo: {filepath}")  # Imprime la ruta del archivo
            
            # Obtener la imagen de la portada del archivo de audio
            cover_path = song_data.get("cover_path")
            # Crear el objeto discord.File con la imagen de la portada
            if cover_path:
                cover_file = discord.File(cover_path, filename=os.path.basename(cover_path))
            else:
                cover_file = None
                

            # Crear el mensaje embed para la canción seleccionada
            embed = discord.Embed(
                title="Reproduciendo",
                description=f"**{song_data['artist']}** - **{song_data['title']}**",
                color=discord.Color.from_rgb(255, 255, 255)  # Color azul por defecto
            )
            # Agregar la miniatura al mensaje embed si hay una imagen de portada adjunta
            if cover_file:
                embed.set_thumbnail(url=f"attachment://{cover_file.filename}")

            # Agregar el álbum al mensaje embed si está disponible
            if "album" in song_data:
                embed.add_field(name="Álbum", value=song_data["album"], inline=True)

            # Agregar el año al mensaje embed si está disponible
            if "year" in song_data:
                embed.add_field(name="Año", value=song_data["year"], inline=True)

            # Agregar la duración al mensaje embed si está disponible
            if "duration" in song_data:
                embed.add_field(name="Duración", value=song_data["duration"], inline=True)

            # Agregar el bitrate al mensaje embed si está disponible
            if "bitrate" in song_data:
                embed.add_field(name="Bitrate", value=str(song_data["bitrate"]) + " kb/s", inline=True)

            # Enviar el mensaje embed
            await ctx.send(embed=embed)

            # Cancelar el temporizador de desconexión
            self.cancel_disconnect_timer()

            # Esperar un momento después de conectar antes de reproducir la canción
            await asyncio.sleep(0.5)

            # Cargar el audio
            audio_source = discord.FFmpegPCMAudio(filepath)

            # Configurar el volumen del audio
            if ctx.voice_client.source:
                ctx.voice_client.source.volume = 0.5  # Establece el volumen en 0.5 (la mitad)

            # Reproducir el audio
            ctx.voice_client.play(audio_source, after=lambda e: self.bot.loop.call_soon_threadsafe(self.song_finished, ctx))

        except Exception as e:
            print(f"Error al reproducir la canción seleccionada: {str(e)}")
            await ctx.send("Ocurrió un error al reproducir la canción seleccionada.")

    async def play_song(self, ctx):
        try:
            if not self.song_queue:
                self.now_playing = None
                return
            song_data = self.song_queue.pop(0)
            filepath = song_data["filepath"]
            print(f"Ruta del archivo: {filepath}")  # Imprime la ruta del archivo
            self.now_playing = song_data["title"]
            print(f"Reproduciendo: {self.now_playing}")

            # Obtener la imagen de la portada del archivo de audio
            cover_path = song_data.get("cover_path")
            

            # Crear el objeto discord.File con la imagen de la portada
            if cover_path:
                cover_file = discord.File(cover_path, filename=os.path.basename(cover_path))
            else:
                cover_file = None
                

            # Crear el mensaje embed
            embed = discord.Embed(
                title="Reproduciendo",
                description=f"**{song_data['artist']}** - **{self.now_playing}**",
                color=discord.Color.from_rgb(255, 255, 255)  # Color azul por defecto
            )

            # Agregar la miniatura al mensaje embed si hay una imagen de portada adjunta
            if cover_file:
                embed.set_thumbnail(url=f"attachment://{cover_file.filename}")

            # Agregar el álbum al mensaje embed si está disponible
            if "album" in song_data:
                embed.add_field(name="Álbum", value=song_data["album"], inline=True)

            # Agregar el año al mensaje embed si está disponible
            if "year" in song_data:
                embed.add_field(name="Año", value=song_data["year"], inline=True)
                   
            
            if "duration" in song_data:
                embed.add_field(name="Duración", value=song_data["duration"], inline=True)
            
            if "bitrate" in song_data:
                embed.add_field(name="Bitrate", value=str(song_data["bitrate"]) + " kb/s", inline=True )

            # Enviar el mensaje embed con la miniatura adjunta
            await ctx.send(embed=embed, file=cover_file)

            # Cancela el temporizador de desconexión
            self.cancel_disconnect_timer()
            
            # Esperar un momento después de conectar antes de reproducir la canción
            await asyncio.sleep(0.5)

            # Cargar el audio
            audio_source = discord.FFmpegPCMAudio(filepath)
            
            # Configurar el volumen del audio
            if ctx.voice_client.source:
                ctx.voice_client.source.volume = 0.5  # Establece el volumen en 0.5 (la mitad)
            
            # Reproducir el audio
            ctx.voice_client.play(audio_source, after=lambda e: self.bot.loop.call_soon_threadsafe(self.song_finished, ctx))
        
        except Exception as e:
            print(f"Error al reproducir la canción: {str(e)}")
            await ctx.send("Ocurrió un error al reproducir la canción.")

    def song_finished(self, ctx):
        # Verificar si hay más canciones en la cola
        if not self.song_queue:
            # Si no hay más canciones, reiniciar el temporizador
            self.reset_disconnect_timer()
        else:
            # Si hay más canciones en la cola, reproducir la siguiente
            asyncio.run_coroutine_threadsafe(self.play_song(ctx), self.bot.loop)

    @commands.command(brief="Pausa la reproducción actual.", help="Pausa la reproducción actual.")
    async def pause(self, ctx):
        try:
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                ctx.voice_client.pause()
                await ctx.send("Reproducción pausada.")
            else:
                await ctx.send("No hay ninguna reproducción en curso.")
        except AttributeError:
            await ctx.send("No estoy en un canal de voz... 🥱")

    @commands.command(brief="Reanuda la reproducción.", help="Reanuda la reproducción.")
    async def resume(self, ctx):
        try:
            if ctx.voice_client.is_paused():
                ctx.voice_client.resume()
            else:
                await ctx.send("La reproducción no está pausada.")
        except AttributeError:
            await ctx.send("No estoy en un canal de voz... 🥱")

    @commands.command(brief="Salta la canción actual.", help="Salta la canción actual.\n\nAbreviaciones: !skip, !s, !S", aliases=["s", "S"] )
    async def skip(self, ctx):
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                await self.play_song(ctx)
            else:
                await ctx.send("No hay ninguna reproducción en curso para saltar.")
        except AttributeError:
            await ctx.send("No estoy en un canal de voz... 🥱")

    @commands.command(brief="Detiene la reproducción actual y limpia la cola.", help="Detiene la reproducción actual y limpia la cola sin salir del canal de voz.")
    async def stop(self, ctx):
        try:
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                ctx.voice_client.stop()
                self.song_queue.clear()  # Limpia la cola de reproducción
                self.cancel_disconnect_timer()  # Cancela cualquier temporizador de desconexión activo
                await ctx.send("Reproducción detenida y cola limpiada.")
            else:
                await ctx.send("No hay ninguna reproducción en curso para detener.")
        except AttributeError:
            await ctx.send("No estoy en un canal de voz... 🥱")
    def reset_disconnect_timer(self):
        # Cancela el temporizador de desconexión si existe
        self.cancel_disconnect_timer()
        # Programa la desconexión después de 3 minutos
        self.disconnect_timer = self.bot.loop.create_task(self.disconnect_after_timeout())

    def cancel_disconnect_timer(self):
        if self.disconnect_timer:
            self.disconnect_timer.cancel()

    async def disconnect_after_timeout(self):
        remaining_time = 180
        while remaining_time > 0:
            print(f"Tiempo restante para la desconexión automática: {remaining_time} segundos")
            await asyncio.sleep(10)  # Espera 10 segundos antes de verificar de nuevo
            remaining_time -= 10

        print("Bot desconectado por inactividad")
        await self.bot.voice_clients[0].disconnect()

async def setup(client):
    await client.add_cog(Commands(client))
