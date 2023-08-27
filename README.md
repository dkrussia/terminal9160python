*Swagger UI Доступен по пути: `/docs`*

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
MCI_SERVICE Отправляет данные в очередь команд RABBIT_MQ (`/command_[device_sn]`)   
PYTHON_TERMINAL_SERVICE Получает данные из RABBIT_MQ (`/command_[device_sn]`)    
PYTHON_TERMINAL_SERVICE Отправляет полученные данные в очередь команд MQTT (`/_dispatch/command/[device_sn]`)  
PYTHON_TERMINAL_SERVICE Получает результат выполнения команды из MQTT (`/_report/received`)
PYTHON_TERMINAL_SERVICE Отправляет результат выполнения команды в RABBIT_MQ (`/reply_to`)  
MCI_SERVICE Получает данные результата выполнение команды на терминале из RABBIT_MQ (`/reply_to`)     
MCI_SERVICE Отправляет результаты выполнение команды на терминале в ПО Matrix
_______________________

*EMQX, RABBIT in Docker*


`docker run -d --name emqx -p 8086:1883 -p 8085:18083 emqx/emqx:latest`    
`docker run -p 15672:15672 -p 5672:5672 rabbitmq:3.10.7-management`

        Build Image Production
        kuznetsovsergey/Dormakaba2020

* docker build . -t terminal9160
* docker tag terminal9160:latest kuznetsovsergey/9160:v1
* docker push kuznetsovsergey/9160:v1

Импорт\Экспорт контейнера

* docker save -o 9160-batch.tar terminal9160-async | Export to FILE
* docker load -i 9160-batch.tar | Import from file

!!! Если rabbit не запускается в demon, проверить Line Separator в файла init.sh

_______________________
**Launcher exe for Windows(Launcher9160.exe)**

GUI(dearpygui)  
To exe (pyconsole)

Сборка командой  
`pyinstaller .\main_exe.py --name=Launcher9160 --noconsole --onefile --windowed --icon=favicon.ico`

**Установка**  
Устанавливаем Docker.

    Windows Enable Hyper-V using PowerShell  
    Open a PowerShell console as Administrator.  
    Run the following command PowerShell:  
    
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
    
    https://www.coretechnologies.com/products/AlwaysUp/Apps/StartDockerDaemonAsAWindowsService.html
    https://learn.microsoft.com/ru-ru/virtualization/windowscontainers/manage-docker/configure-docker-daemon

    Run this command to install the Docker Daemon service:
      dockerd --register-service
    
    Заходим в учетную запись Docker, с правами только на чтение.
    Нажимаем Pull на доступной версии Image.

    Если интернета нету на компьютере тогда:
    Загрузить файл образа в ручную по ссылке
    Передать в Runner по кнопочке [Добавить образ]

    docker save -o имя_архива.tar имя_образа:тег
    docker save -o myimage.tar myimage:latest
    docker load -i имя_архива.tar

-----------------------
  
PIP Скачать библиотеки в папку packages  
`pip download  -r .\requirements.txt  -d . \packages\` 
`pip install -r requirements.txt --no-index --find-links .\packages\`
  

RabbitMQ == `3.11.8`    
Erlang == `25.2.2`   
EMQX == `5.0.24`      
TERMINAL Firmware == `1.4.15C_DBG`

EMQX install service:  
`.../bin/emqx install` 

Set ENV windows variables:  
  
RABBIRMQ_BASE  
RABBIRMQ_LOG_BASE  
  
`rabbitmq-service.bat remove`  
`rabbitmq-service.bat install`  
`rabbitmq-plugins enable rabbitmq_management`    

------------------------
*Заметки*

!При назначении/изменении Server IP возможно требуется сделать Restart Terminal

`[update_person/create] userName = firstName + lastName`  
`???MQTT команда update_user создает персону`

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

1. MCI_SERVICE отправляет команды на выполнения для устройства в очередь => commands_$device.

                      Header                                      Body
       {"command_type": "user_update"}               |   {id, firsName, lastName}
       {"command_type": "user_delete"}               |   {id}
       {"command_type": "user_update_biophoto"}      |   {id, picture}  
       {"command_type": "multiuser_update"}          |   []user_update   
       {"command_type": "multiuser_update_biophoto"} |   []user_update_biophoto     


2. MCI_SERVICE слушает события в очереди => events_$device.      
   `{sn: str, time:2000-01-01T21:00:00, status:str, pin: int,str}`

        status: 
        IN: 2
        OUT: 3
        TRIP: 4 + REMARK

   sn: номер устройства.  
   pin === id_person (Идентификатор человека)


3. MCI_SERVICE слушает очередь Ping => events_$device.
   `{sn: str}`    
   sn: номер устройства.
