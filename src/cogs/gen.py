import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import os
from mutagen.flac import FLAC
from decouple import config 


class slash_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client   

    async def generate_database(self):
        directory = config("MUSIC_DIRECTORY")
        data_folder = "data"

        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        song_database = []

        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".flac"):
                    filepath = os.path.join(root, filename)
                    try:
                        audio = FLAC(filepath)
                        artist = audio["artist"][0] if "artist" in audio else "Desconocido"
                        title = audio["title"][0] if "title" in audio else "Desconocido"
                        duration_seconds = audio.info.length
                        duration_formatted = "{:02}:{:02}".format(int(duration_seconds // 60), int(duration_seconds % 60))
                        album = audio["album"][0] if "album" in audio else "Desconocido"
                        year = audio["date"][0] if "date" in audio else "Desconocido"
                        bitrate = audio.info.bitrate // 1000  # Convertir a kbps

                        # Buscar la imagen de portada en la carpeta del álbum
                        album_folder = os.path.dirname(filepath)
                        cover_path = None
                        for file in os.listdir(album_folder):
                            if file.lower() in ["cover.jpg", "folder.jpg"]:
                                cover_path = os.path.join(album_folder, file)
                                break

                        song_info = {
                            "title": title,
                            "artist": artist,
                            "album": album,
                            "duration": duration_formatted,
                            "year": year,
                            "bitrate": bitrate,
                            "filename": filename,
                            "filepath": os.path.normpath(filepath),
                            "cover_path": os.path.normpath(cover_path) if cover_path else None
                        }
                        song_database.append(song_info)
                    except Exception as e:
                        print(f"Error al procesar el archivo {filepath}: {e}")

        output_path = os.path.join(data_folder, "song_database.json")
        with open(output_path, "w") as f:
            json.dump(song_database, f, indent=4)

        # Mensaje de confirmación
        return "Base de datos generada correctamente."

    @commands.Cog.listener()
    async def on_ready(self):
        print("Comandos slash cargados correctamente.")

    @app_commands.command(name="gen_database", description="Generar archivo JSON")
    async def generate_database_command(self, interaction: discord.Interaction):
        # Crear una instancia de la clase para llamar al método
        instance = slash_commands(self.client)
        result = await instance.generate_database()
        await interaction.response.send_message(result, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(slash_commands(client))
