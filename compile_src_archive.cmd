:: Запуск ./compile_src_archive.cmd env_mode
set env_mode=%1
echo "Dashboard build %env_mode%"

cd frontend
call npm run build -- --mode ".env.%env_mode%"
cd ..

call ./archive_whl_packages.cmd

echo "Create an archive src all..."
tar -acf 9160-service-%env_mode%.zip base dashboard services utils config.py main.py requirements.txt run.cmd install_requirements_offline.cmd packages.zip

del .\packages.zip

echo "Finished build src"
