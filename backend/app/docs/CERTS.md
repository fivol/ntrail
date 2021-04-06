# Установка сертификатов


Используем https://certbot.eff.org/lets-encrypt/ubuntufocal-other
чтобы сгенерить сертифигаты для домена

После генерации они лежат по слудующим адресам

Сертификат:
```shell
/etc/letsencrypt/live/ntrail.fivol.space/fullchain.pem
```
Ключ:
```shell
/etc/letsencrypt/live/ntrail.fivol.space/privkey.pem
```
Сначала нужно склонить гит реп
```shell
git clone https://github.com/fivol/ntrail-backend.git
```
Перейти в папку с проектом
```shell
cd ntrail-backend
```
Скопировать сертификаты
```shell
cp /etc/letsencrypt/live/ntrail.fivol.space/fullchain.pem nginx/certs/fullchain.pem
cp /etc/letsencrypt/live/ntrail.fivol.space/privkey.pem nginx/certs/privkey.pem
```
Готово. Можно запускать докер
```shell
docker-compose up -d --build
```
И проверить результат

https://ntrail.fivol.space/
