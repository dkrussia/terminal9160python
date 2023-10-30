:: Запуск ./compile_whl_requirements.cmd
mkdir packages
pip download -r .\requirements.txt -d .\packages\
echo "Compile an archive..."
tar -acf packages.zip packages
rd /s /q packages
echo "Finished"
