:: Запуск ./compile_src_archive.cmd env_mode
set env_mode=%1
echo "Dashboard build %env_mode%"
cd frontend
call npm run build -- --mode ".env.%env_mode%"
cd ..
echo "Compile an archive..."
tar -acf 9160-service-%env_mode%.zip base dashboard services utils config.py main.py requirements.txt
echo "Finished"
