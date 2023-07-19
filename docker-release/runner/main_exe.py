import json

import docker
import dearpygui.dearpygui as dpg
from docker.errors import APIError
from docker.models.containers import Container

client = docker.from_env()
image_search_string = '9160'
container_search_string = '-9160-container'


class DokerEnv:
    env = {}

    @staticmethod
    def read_env():
        try:
            with open("env.json", "r") as f:
                DokerEnv.env = json.load(f)
                return DokerEnv.env
        except FileNotFoundError:
            DokerEnv.env = {
                "HOST": "127.0.0.1",
                "TZ": "Europe/Moscow",
            }
            DokerEnv.write_env(DokerEnv.env)

    @staticmethod
    def write_env(d):
        with open("env.json", "w") as f:
            f.write(json.dumps(d))
            DokerEnv.env = d

    @staticmethod
    def env_changed(d):
        changed = json.dumps(d, sort_keys=True) != json.dumps(DokerEnv.env, sort_keys=True)
        if changed:
            DokerEnv.write_env(d)
        return changed


DokerEnv.read_env()


def set_proces_info(text):
    dpg.set_value('proces_info', text)


def get_container_name_by_image(image_name: str):
    return image_name.split(':')[-1] + container_search_string


def docker_is_installed():
    return client.version()["Platform"]["Name"]


def get_docker_images():
    images = []
    docker_images = client.images.list()
    matching_images = [image for image in docker_images if
                       any(image_search_string in tag for tag in image.tags)]
    for image in matching_images:
        for tag in image.tags:
            images.append(tag)

    return images


def on_select_images():
    dpg.enable_item('button_start')


def check_container_is_running():
    # Получаем список всех контейнеров
    containers = client.containers.list(all=True)
    # Проверяем, запущен ли хотя бы один контейнер с именем, содержащим подстроку
    matching_containers = [container for container in containers if
                           container_search_string in container.name
                           and container.status == "running"]

    if matching_containers:
        c = matching_containers[0]
        dpg.set_value('container_started', c.name)
        dpg.set_value('combo_version', c.attrs['Config']['Image'])
        dpg.set_value('combo_timezone', DokerEnv.env["TZ"])
        dpg.set_value('input_host', DokerEnv.env["HOST"])
        dpg.enable_item('button_stop')

    return matching_containers


def start_container_by_image_name(image_name, button):
    # Получаем список всех контейнеров
    container_name = get_container_name_by_image(image_name)
    environment = {
        'HOST': dpg.get_value('input_host'),
        'TZ': dpg.get_value('combo_timezone'),
    }
    try:
        container = client.containers.get(container_name)
        if DokerEnv.env_changed(environment):
            container.remove()
            DokerEnv.write_env(environment)
            container = None
            print('remove!')
    except docker.errors.NotFound:
        container = None

    if not container:
        set_proces_info(f"Container {image_name} not found")
        try:
            # Создаем контейнер на основе образа
            print('Создаем', DokerEnv.env)
            container = client.containers.create(
                image_name,
                name=container_name,
                # контейнер_порт / tcp: хост_порт
                ports={
                    '15672/tcp': 15672,
                    '5672/tcp': 5672,
                    '18083/tcp': 18083,
                    '1883/tcp': 1883,
                    '8080/tcp': 8888,
                },
                environment=DokerEnv.env
            )

            set_proces_info(f"Container {container_name} created")

        except APIError as e:
            set_proces_info(f"Error create container: {e}")
            return

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

    container_name = get_container_name_by_image(image_name)
    container = client.containers.get(container_name)
    # docker.errors.NotFound

    if container.status == "running":
        set_proces_info(f'Stopping container {container_name}...')
        container.stop()
        dpg.set_value('container_started', "")
        set_proces_info(f'Stopped container {container_name}')
        dpg.enable_item('button_start')

    check_container_is_running()


docker_version = docker_is_installed()
docker_images = get_docker_images()

dpg.create_context()
dpg.create_viewport(width=600, height=600, title='Terminal9040')
dpg.setup_dearpygui()

with dpg.theme() as disabled_theme:
    with dpg.theme_component(dpg.mvButton, enabled_state=False):
        dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 0, 0])

dpg.bind_theme(disabled_theme)

with dpg.window(label="", width=600, height=600):
    if docker_version:
        dpg.add_text(docker_version)
    else:
        dpg.add_text("DOCKER VERSION undefined", color=(255, 160, 122))

    dpg.add_text("Not container started", tag='container_started')
    dpg.add_text("Wait for a action", tag="proces_info")
    dpg.add_combo(docker_images,
                  callback=on_select_images,
                  label="Choose version", width=200,
                  tag='combo_version',
                  default_value=docker_images[0] if docker_images[0] else '')
    dpg.add_input_text(label="HOST IP ADDRESS",
                       width=200,
                       tag='input_host',
                       default_value=DokerEnv.env["HOST"])
    dpg.add_combo(['Asia/Riyadh', 'Asia/Dubai', 'Europe/Moscow'],
                  callback=on_select_images,
                  label="Choose TimeZone", width=200,
                  tag='combo_timezone',
                  default_value='Europe/Moscow')
    dpg.add_button(label="Start", callback=start_container, tag='button_start', )
    dpg.add_button(label="Stop", callback=stop_container, tag='button_stop', )

check_container_is_running()

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
