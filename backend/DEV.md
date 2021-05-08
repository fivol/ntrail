# Как запускать на сервере

1. Создать сертификаты, инструкция https://certbot.eff.org/lets-encrypt/ubuntufocal-webproduct
```shell
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot certonly --standalone
```
**Внимание: вводим ntrail.fivol.space в качестве домена**
2. Копируем сертификаты
```shell
cp /etc/letsencrypt/live/ntrail.fivol.space/fullchain.pem ./nginx/certs/fullchain.pem
cp /etc/letsencrypt/live/ntrail.fivol.space/privkey.pem ./nginx/certs/privkey.pem
```   
2. Выполнить
```shell
./start.sh
```
