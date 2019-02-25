cd C:\Users\Kiril\Desktop\musics

FOR /R %%f in (*.m4a) DO (

ffmpeg -i "%%f" -codec:v copy -codec:a libmp3lame -q:a 0 "%%f.mp3"
del "%%f" /s /f /q
)
