FROM rabbitmq:3.12-management

RUN apt update && apt install -y \
    unzip \
	curl \
	git \
	wget \
    vim
	
RUN wget https://www.emqx.com/en/downloads/broker/5.1.0/emqx-5.1.0-ubuntu22.04-amd64.deb
RUN apt install ./emqx-5.1.0-ubuntu22.04-amd64.deb

RUN apt install -y python3-pip

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ADD assets/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/init.sh"]