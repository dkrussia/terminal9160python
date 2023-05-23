def handle_mci_command(message):
    type_command = message.properties['headers'].get('command_type')
    reply_to = message.properties.get('reply_to')
    payload = message.json()
    print(type_command, reply_to, payload)

    if type_command == 'user_update':
        pass

    if type_command == 'multiuser_update':
        pass

    if type_command == 'user_delete':
        pass

    if type_command == 'user_update_biophoto':
        pass

    if type_command == 'multiuser_update_biophoto':
        pass
