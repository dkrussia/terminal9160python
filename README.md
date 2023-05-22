*Терминал 9160 подписывается на следующее топики*

`/_dispatch/_get_state/[device_sn]`      
`/_dispatch/command/[device_sn]`  
`/_dispatch/notify`

И отдает обратную связь в

`/_report/state`  
`/_report/received`
  
-----------------------
**Пример рабочего потока данных Matrix-Terminal:**  
  
MCI_SERVICE Получает данные из ПО Matrix  
MCI_SERVICE Отправляет данные в очередь команд  RABBIT_MQ (`/command_[device_sn]`)   
PYTHON_TERMINAL_SERVICE Получает данные из RABBIT_MQ (`/command_[device_sn]`)    
PYTHON_TERMINAL_SERVICE Отправляет полученные данные в очередь команд MQTT (`/_dispatch/command/[device_sn]`)  
PYTHON_TERMINAL_SERVICE Получает результат выполнения команды из MQTT (`/_report/received`)
PYTHON_TERMINAL_SERVICE Отправляет результат выполнения команды в RABBIT_MQ (`/reply_to`)  
MCI_SERVICE Получает данные результата выполнение команды на терминале из RABBIT_MQ (`/reply_to`)     
MCI_SERVICE Отправляет результаты выполнение команды на терминале в ПО Matrix 
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
__________________________________
**Шина сообщений MCI_SERVICE.**  

1. MCI_SERVICE отправляет: CommandsQueue => commands_$device.    

                      Header                                      Body
       {"command_type": "user_update"}               |   {id, firsName, lastName}
       {"command_type": "user_delete"}               |   {id}
       {"command_type": "user_update_biophoto"}      |   {id, picture}  
       {"command_type": "multiuser_update"}          |   []user_update   
       {"command_type": "multiuser_update_biophoto"} |   []user_update_biophoto     


2. MCI_SERVICE слушает ReceiveEvents) => events_$device.      
  `{sn: str, time:2000-01-01:21:00:00, status:str, pin: int,str}`  
  sn: $device или номер камеры).  
  status = '1' (Успешный проход)   
  (pin Тоже самое, что и id) (Идентификатор человека)