import tkinter as tk
from tkinter import messagebox
import os
import threading
import sys
import youtube_dl
import os
from moviepy.editor import AudioFileClip
import random
import time
from mutagen.mp3 import MP3
import math
import sys
import pygame
import traceback

def filler():
    pass

os.chdir(os.path.dirname(os.path.realpath(__file__)))

pygame.mixer.init()

def audio_length(audio):
    return math.ceil(MP3(audio).info.length)

class MusicTimer:
    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self.timer = threading.Timer(timeout, callback, args = None)
        self.startTime = time.time()

    def start(self):
        self.timer.start()

    def cancel(self):
        self.timer.cancel()

    def pause(self):
        self.timer.cancel()
        self.pauseTime = time.time()

    def resume(self):
        self.timer = threading.Timer(self.timeout - (self.pauseTime - self.startTime), self.callback)

class MusicPlayer(threading.Thread):
    def __init__(self, playlist, playlist_name):
        threading.Thread.__init__(self)
        self.index = 0
        self.timer = MusicTimer(10, filler)
        self.playlist = playlist
        self.blocker = threading.Event()
        self.playlist_name = playlist_name

    def run(self):
        while True:
            if self.index == len(self.playlist):
                pygame.mixer.music.unload()
                app.switch_frame(ChoosePlaylist)
                sys.exit()
            self.blocker.clear()
            self.timer = MusicTimer(audio_length(os.path.join('Playlists', self.playlist_name, self.playlist[self.index])), self.blocker.set)
            pygame.mixer.music.load(os.path.join('Playlists', self.playlist_name, self.playlist[self.index]))
            app.switch_frame(PlaybackControl)
            pygame.mixer.music.play()
            self.timer.start()
            self.blocker.wait()
            self.index += 1

    def close(self):
        pygame.mixer.music.unload()
        app.switch_frame(ChoosePlaylist)
        sys.exit()

class RootApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.frame = tk.Tk()
        self.geometry("500x200")

        self.switch_frame(StartPage)
        self.winfo_toplevel().title("Music")
        self.ytlink = None
        self.songname = None
        self.playlist = None
        self.songlist = None
        self.stream = MusicPlayer(None, None)

    def switch_frame(self, frame_class):
        new_frame = frame_class(self)
        self.frame.destroy()
        self.frame = new_frame
        self.frame.pack()

    def dlprocess(self, ytlink, songname):
        self.ytlink = ytlink
        self.songname = songname
        if self.ytlink == '' or self.songname == '':
            messagebox.showerror("Come On...", "Fill in the blanks")
        elif self.playlist == None:
            messagebox.showerror("You Serious?", 'Choose a playlist')
        else:
            try:
                ydl_opts = {'format': 'bestaudio/best',
                            'outtmpl': 'Temp\A'[:-1] + self.songname + '.mp4'}
                youtube_dl.YoutubeDL(ydl_opts).download([self.ytlink])
            except:
                messagebox.showerror("Hmmmmmmmmm", "Something wrong with the link?")
                self.switch_frame(DownloadPage)
            else:
                try:
                    file = open('Playlists\A'[:-1] + self.playlist + '\A'[:-1] + self.songname + '.mp3', "x")
                    file.close()
                    audioclip = AudioFileClip('Temp\A'[:-1] + self.songname + ".mp4")
                    audioclip.write_audiofile('Playlists\A'[:-1] + self.playlist + '\A'[:-1] + self.songname + '.mp3')
                except:
                    messagebox.showerror("Bruh", "You already have that song")
                finally:
                    for f in os.listdir('Temp'):
                        os.remove(os.path.join('Temp', f))
                    self.switch_frame(DownloadPage)

    def playmusic(self):
        self.songlist = [os.path.basename(os.path.join(f'Playlists\{self.playlist}', f)) for f in os.listdir(f'Playlists\{self.playlist}')]
        random.shuffle(self.songlist)
        self.stream = MusicPlayer(self.songlist, self.playlist)
        self.stream.index = 0
        self.switch_frame(PlaybackControl)
        self.stream.start()

    def playback_control(self, choice):
        if choice == 'rewind':
            pygame.mixer.music.stop()
            self.stream.index -= 1
            self.stream.timer.cancel()
            self.stream.blocker.set()
        elif choice == 'skip':
            pygame.mixer.music.stop()
            self.stream.timer.cancel()
            self.stream.blocker.set()
        elif choice == 'pause':
            pygame.mixer.music.pause()
            self.stream.timer.pause()
        elif choice == 'resume':
            pygame.mixer.music.unpause()
            self.stream.timer.resume()
        elif choice == 'back':
            self.stream.index -= 2
            self.stream.timer.cancel()
            self.stream.blocker.set()

    def playlist_assigner(self, playlist):
        self.playlist = playlist

class StartPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="What do you want").pack(side = "top", fill = "x", pady = 10)
        tk.Button(self, text="Download Music", command = lambda: master.switch_frame(DownloadPage)).pack(side = 'bottom')
        tk.Button(self, text="Play Existing Music", command = lambda: master.switch_frame(ChoosePlaylist)).pack()

class DownloadPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text = "Paste Youtube link and enter name to download").pack(side = "top", fill = "x", pady = 10)

        youtube_link = tk.Text(self, height = 1, width = 60)
        youtube_link.pack()

        song_name = tk.Text(self, height = 1, width = 25)
        song_name.pack()

        varList = tk.StringVar(master)
        varList.set("Choose a Playlist")
        om = tk.OptionMenu(self, varList, *[os.path.basename(os.path.join('Playlists', f)) for f in os.listdir('Playlists')], command = master.playlist_assigner)
        om.pack(side = 'top', pady = 10)

        tk.Button(self, text = "Download", command = lambda: master.dlprocess(youtube_link.get("1.0",'end-1c'), song_name.get("1.0",'end-1c'))).pack()
        tk.Button(self, text = "Return to start page", command = lambda: master.switch_frame(StartPage)).pack()

class ChoosePlaylist(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text = "Choose Playlist to shuffle through").pack(side = "top", fill = "x", pady = 10)

        varList = tk.StringVar(master)
        varList.set("Choose a Playlist")
        om = tk.OptionMenu(self, varList, *[os.path.basename(os.path.join('Playlists', f)) for f in os.listdir('Playlists')], command = master.playlist_assigner)
        om.pack(side = 'top', pady = 10)

        tk.Button(self, text = 'Play', command = master.playmusic).pack()
        tk.Button(self, text = "Return to start page", command = lambda: master.switch_frame(StartPage)).pack()

class PlaybackControl(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        current_song = os.path.join('Playlists', master.playlist, master.songlist[master.stream.index])
        tk.Label(self, text = f'Now Playing: {master.songlist[master.stream.index][:-4]}\nLength: {audio_length(current_song) // 60} minutes {audio_length(current_song) % 60} seconds').grid(row = 0, column = 1)
        tk.Button(self, text = 'Rewind', command = lambda: master.playback_control('rewind')).grid(row = 1, column = 0)
        tk.Button(self, text = 'Resume', command = lambda: master.playback_control('resume')).grid(row = 1, column = 2)
        tk.Button(self, text = 'Back', command = lambda: master.playback_control('back')).grid(row = 2, column = 0)
        tk.Button(self, text = 'Pause', command = lambda: master.playback_control('pause')).grid(row = 2, column = 1)
        tk.Button(self, text = 'Skip', command = lambda: master.playback_control('skip')).grid(row = 2, column = 2)

app = RootApp()
app.mainloop()
