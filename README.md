# Hi-Res Queen

This Discord bot allows users to play music in a voice channel from a pre-defined database of songs. Users can search for songs by title, artist, or album, and add them to the bot's queue for playback. The bot supports pausing, resuming, skipping, and stopping playback, as well as automatic disconnection from the voice channel after a period of inactivity.

<div align="center">
  <img src="https://imgur.com/IKsan7z.png" width=450px>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://imgur.com/N6yyXeT.png" width=477px>
</div>

> [!NOTE]
> At the moment it only works with songs in FLAC format. Although Discord only supports a maximum bitrate of 96 kbps, It can make the difference between choosing whether to play your own music using FFmpeg, or play it with a bot that uses streaming services as an intermediary (Spotify, Deezer, Soundcloud, Etc.)
 
Maybe one day Discord will increase the transfer speed limit in voice chat. 

## Commands
- **join**: Connect the bot to the voice channel.
- **leave**: Disconnect the bot.
- **play**: Add a song to the queue by title, artist, or album.
- **pause**: Pause the current playback.
- **resume**: Resume playback if paused.
- **skip**: Skip the current song and play the next one in the queue.
- **stop**: Stop playback and clear the queue.
- **reload_database**: Reloads the list of available songs in case you add more music while listening.

## Setup

1. Clone this repository to your local machine.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Set up your Discord bot token and other configurations in a `.env` file.
4. Start the bot by running `python .\src\main.py`.

## Configuration

Make sure to configure the following variables in the `.env` file:

<div>
  <img src="https://imgur.com/0x8QJpz.png" width=200px>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://imgur.com/FKpooAo.png" width=200px>
</div>

- `TOKEN`: Your Discord bot token.
- `MUSIC_DIRECTORY`: The path of your music.

> [!TIP]
> You can do this process legally by extracting the data from any CD with an internal or external drive.

> [!IMPORTANT]
> You also need to have installed [FFmpeg](https://ffmpeg.org/download.html) on your system.

<div>
  <img src="https://imgur.com/F2gMGDS.png">
</div>

## Usage
1. To create the JSON file, while in a voice channel you have to use `/gen_database`. You need to use this command whenever you add new music to the specified path.
<div>
  <img src="https://imgur.com/OE2TbmZ.png" width=300px>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://imgur.com/Hsb26RK.png" width=300px>
</div>

2. Then you should use `!reload_database` or `!rdb` to make the scan of the songs.
 

3. Finally, you can use all the other commands to start playing music. You can check them with `!help`.

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

<div>
  <img src="https://imgur.com/cG8hTZe.png" width=450px>
</div>



