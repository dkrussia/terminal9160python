pyinstaller .\main_exe.py --name=Launcher9160 --noconsole --onefile --windowed --icon=favicon.ico
copy .\dist\Launcher9160.exe Launcher9160.exe
rmdir /s /q .\build
rmdir /s /q .\dist
del Launcher9160.spec