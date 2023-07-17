import docker
import dearpygui.dearpygui as dpg
from docker.errors import APIError

client = docker.from_env()

global text_container
global info
global input_host


def set_text_info(text):
    dpg.set_value(text_info, text)


def docker_is_installed():
    return client.version()["Platform"]["Name"]


def get_docker_images():
    images = []
    docker_images = client.images.list()
    matching_images = [image for image in docker_images if
                       any('terminal9160' in tag for tag in image.tags)]
    for image in matching_images:
        for tag in image.tags:
            images.append(tag)

    return images


def any_container_is_running():
    # Получаем список всех контейнеров
    containers = client.containers.list(all=True)

    # Проверяем, запущен ли хотя бы один контейнер с именем, содержащим подстроку
    matching_containers = [container.name for container in containers if
                           'terminal9160' in container.name and container.status == "running"]
    dpg.set_value(text_container, matching_containers)
    return matching_containers


def start_container_by_image_name(image_name, button):
    # Получаем список всех контейнеров
    containers = client.containers.list(all=True)

    # Проверяем наличие контейнера для выбранного имени образа
    container_exists = any(container.image.tags[0] == image_name for container in containers)

    # Выводим результат
    if container_exists:
        set_text_info(f"Контейнер для образа {image_name} существует")
    else:
        set_text_info(f"Контейнер для образа {image_name} не  существует")

    container_name = image_name.replace(':', '') + '-container'

    if not container_exists:
        try:
            # Создаем контейнер на основе образа
            client.containers.create(
                image_name,
                name=container_name,
                ports={
                    '15672/tcp': 15672,
                    '5672/tcp': 5672,
                    '18083/tcp': 18083,
                    '1883/tcp': 1883,
                    '8080/tcp': 8080,
                },
                environment={
                    'HOST': dpg.get_value(input_host),
                    'TZ': 'Europe/Moscow',
                }
            )
            set_text_info(f"Контейнер {container_name} создан")

        except APIError as e:
            set_text_info(f"Ошибка создания контейнера: {e}")
            return

    if any_container_is_running():
        return

    container = client.containers.get(container_name)
    if container.status == "running":
        return

    set_text_info(f"Запуск контейнера {container_name}...")
    container.start()
    any_container_is_running()
    set_text_info(f"Контейнера {container_name} запущен")


def stop_container_by_image_name():
    pass


def start_container(sender, app_data, user_data):
    image_name = dpg.get_value(user_data)
    if not image_name:
        return
    if any_container_is_running():
        return
    start_container_by_image_name(image_name, button=sender)


def stop_container(sender, app_data, user_data):
    image_name = dpg.get_value(user_data)
    if not image_name:
        return
    container_name = image_name.replace(':', '') + '-container'
    container = client.containers.get(container_name)
    if container.status == "running":
        set_text_info(f'Останавливаю контейнер {container_name}...')
        container.stop()
        set_text_info(f'Остановился контейнер {container_name}')
    any_container_is_running()


docker_version = docker_is_installed()
docker_images = get_docker_images()

dpg.create_context()
dpg.create_viewport(width=600, height=600)
dpg.setup_dearpygui()

with dpg.window(label="Example Window", width=600, height=600):
    if docker_version:
        dpg.add_text(docker_version)
    else:
        dpg.add_text("DOCKER VERSION undefined", color=(255, 160, 122))

    text_container = dpg.add_text(docker_version)
    text_info = dpg.add_text("Wait for a acton")
    combo_version = dpg.add_combo(docker_images, label="Choose version", width=200)
    input_host = dpg.add_input_text(label="HOST IP ADDRESS")

    dpg.add_button(label="Start", callback=start_container, user_data=combo_version, enabled=True, )
    dpg.add_button(label="Stop", callback=stop_container, user_data=combo_version, enabled=True)

any_container_is_running()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
