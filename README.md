*Терминал 9160 подписывается на следующее топики*
  
`/_dispatch/_get_state/[device_sn]`      
`/_dispatch/command/[device_sn]`  
`/_dispatch/notify`

И отдает обратную связь в  
  
`/_report/state`  
`/_report/received`  
_______________________
*EMQX in Docker*  
  
`docker run -d --name emqx -p 8086:1883 -p 8081:8081 -p 8083:8083 -p 8084:8084 -p 8883:8883 -p 8085:18083 emqx/emqx:latest`
_______________________

RabbitMQ `3.11.8`      
`rabbitmq-plugins enable rabbitmq_management`  
`rabbitmq-plugins enable rabbitmq_mqtt`  
Erlang `25.2.2`   
EMQX `5.0.24`      
TERMINAL appVersionName': `1.4.15C_DBG` 

!При назначении Server IP возможно требуется сделать Factory Reset 

------------------------
*Заметки*  
`[update_person/create] userName = firstName + lastName`

Для DEBUG режима и просмотра логов по ssh

* Установить прошивку DEBUG
* Подключиться ssh root@192.168.1.100
* Пароль: rockchip  
  
* Изменить строчки файла /etc/init.d/S50lauche как на скриншоте ./docs/debug_settings.png
* Затем выполнить
* /etc/init.d/S50laucher stop
* /etc/init.d/S50laucher start
