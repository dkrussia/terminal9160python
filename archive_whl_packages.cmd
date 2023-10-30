:: Запуск ./compile_whl_requirements.cmd
mkdir packages
echo "Download pip requirements ..."
pip download -r .\requirements.txt -d .\packages\
echo "Create an archive ..."
tar -acf packages.zip packages
rd /s /q packages
echo "Finished pip req"
