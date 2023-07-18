import docker
import dearpygui.dearpygui as dpg
from docker.errors import APIError

client = docker.from_env()


def set_proces_info(text):
    dpg.set_value('proces_info', text)


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


def check_container_is_running():
    # Получаем список всех контейнеров
    containers = client.containers.list(all=True)

    # Проверяем, запущен ли хотя бы один контейнер с именем, содержащим подстроку
    matching_containers = [container for container in containers if
                           'terminal9160' in container.name
                           and container.status == "running"]

    if matching_containers:
        c = matching_containers[0]
        dpg.set_value('container_started', c.name)
        dpg.set_value('combo_version', c.attrs['Config']['Image'])
        dpg.set_value('input_host', c.attrs['Config']['Env'][0].split("=")[-1])

    return matching_containers


def start_container_by_image_name(image_name, button):
    # Получаем список всех контейнеров
    containers = client.containers.list(all=True)

    # Проверяем наличие контейнера для выбранного имени образа
    container_exists = any(container.image.tags[0] == image_name for container in containers)

    # Выводим результат
    if container_exists:
        set_proces_info(f"Container {image_name} found")
    else:
        set_proces_info(f"Container {image_name} not found")

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
                    'HOST': dpg.get_value('input_host'),
                    'TZ': 'Europe/Moscow',
                }
            )
            set_proces_info(f"Container {container_name} created")

        except APIError as e:
            set_proces_info(f"Error create container: {e}")
            return

    if check_container_is_running():
        return

    container = client.containers.get(container_name)
    if container.status == "running":
        return

    set_proces_info(f"Start container {container_name}...")
    container.start()
    check_container_is_running()
    set_proces_info(f"Container {container_name} started")


def stop_container_by_image_name():
    pass


def start_container(sender, app_data, user_data):
    image_name = dpg.get_value('combo_version')
    if not image_name:
        return
    if check_container_is_running():
        return
    start_container_by_image_name(image_name, button=sender)


def stop_container(sender, app_data, user_data):
    image_name = dpg.get_value('combo_version')

    if not image_name:
        return

    container_name = image_name.replace(':', '') + '-container'
    container = client.containers.get(container_name)

    if container.status == "running":
        set_proces_info(f'Stopping container {container_name}...')
        container.stop()
        dpg.set_value('container_started', "")
        set_proces_info(f'Stopped container {container_name}')

    check_container_is_running()


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

    dpg.add_text("Not container started", tag='container_started')
    dpg.add_text("Wait for a action", tag="proces_info")
    dpg.add_combo(docker_images, label="Choose version", width=200, tag='combo_version')
    dpg.add_input_text(label="HOST IP ADDRESS", tag='input_host')

    dpg.add_button(label="Start", callback=start_container, enabled=True, )
    dpg.add_button(label="Stop", callback=stop_container, enabled=True)

check_container_is_running()

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
