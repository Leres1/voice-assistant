#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

Process, Exist, Spotify.exe

Run "C:\Users\volod\AppData\Roaming\Spotify\Spotify.exe"

sleep 5000


Send, {Space}
sleep 200
Send, !{Tab}

Return