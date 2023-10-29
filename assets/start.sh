rabbitmq-server -detached
emqx start

sleep 30
python3 main.py