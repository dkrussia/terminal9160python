FROM rabbitmq:3.12-management

RUN apt update && apt install -y \
    unzip \
	curl \
	git \
	wget \
    vim \
    lsb-release
	
RUN wget https://www.emqx.com/en/downloads/broker/5.1.0/emqx-5.1.0-ubuntu22.04-amd64.deb
RUN apt install ./emqx-5.1.0-ubuntu22.04-amd64.deb

# https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver16&tabs=ubuntu18-install%2Calpine17-install%2Cdebian8-install%2Credhat7-13-install%2Crhel7-offline
RUN curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
RUN apt update
ENV ACCEPT_EULA=Y
RUN apt  install -y msodbcsql18
RUN apt install -y unixodbc-dev
RUN apt install -y python3-pip

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ADD assets/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]