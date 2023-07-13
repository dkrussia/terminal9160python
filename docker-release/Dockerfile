FROM rabbitmq:3.12-management

RUN apt update && apt install -y \
    unzip \
	curl \
	git \
	wget
	
RUN wget https://www.emqx.com/en/downloads/broker/5.1.0/emqx-5.1.0-ubuntu22.04-amd64.deb
RUN apt install ./emqx-5.1.0-ubuntu22.04-amd64.deb

ADD init.sh /init.sh
RUN chmod +x /init.sh
CMD ["/init.sh"]