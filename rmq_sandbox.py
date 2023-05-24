import time

from amqpstorm import Connection
import threading


def process_message(message):
    # Обработка сообщения из очереди
    print(f"Received message: {message}")


def bind_queue_to_exchange(channel, exchange_name, queue_name, routing_key):
    # Объявление обменника
    channel.exchange.declare(exchange_name, "direct")

    # Создание очереди
    channel.queue.declare(queue_name)

    # Связывание обменника с очередью с использованием routing_key
    channel.queue.bind(queue_name, exchange_name, routing_key)

    # Подписка на очередь и обработка сообщений
    channel.basic.consume(process_message, queue_name)


def consume_messages(channel):
    # Запуск прослушивания
    channel.start_consuming()


RMQ_HOST = "151.248.125.126"
RMQ_USER = "admin"
RMQ_PASSWORD = "Dormakaba2020"


def main():
    connection = Connection(RMQ_HOST, RMQ_USER, RMQ_PASSWORD)
    channel = connection.channel()
    exchange_name = "my_exchange"

    # Привязка и обработка первой очереди
    queue_name1 = "queue1"
    routing_key1 = "group1"
    bind_queue_to_exchange(channel, exchange_name, queue_name1, routing_key1)

    # Запуск потока для прослушивания
    print(0)
    consume_thread = threading.Thread(target=consume_messages, args=(channel,))
    consume_thread.start()
    # Привязка и обработка второй очереди
    queue_name2 = "queue2"
    routing_key2 = "group1"
    bind_queue_to_exchange(channel, exchange_name, queue_name2, routing_key2)
    print(1)
    # Другие действия в основном потоке

    # Ожидание завершения потока прослушивания
    consume_thread.join()
    print(2)

    # Закрытие соединения
    channel.close()
    connection.close()


if __name__ == "__main__":
    main()
