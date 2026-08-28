
Документация по [fastapi](https://fastapi.tiangolo.com/)

## Запуск докер стека
```shell
docker build redis -t redis-api
```

## Обновляем тестовый контур

### Повышаем версию тега гитхаба и билдим
```shell
make SERVICE=ntrail-api build
```
Вставляем новый image в `docker-stack.test.yml`
```shell
make deploy-test
```

## Инициализация репозитория
```shell
git clone git@github.com:fivol/ntrail-api.git
```
```shell
git submodule update --init
```
```shell
ln -s ntrail-worker/worker worker
ln -s ntrail-core/core core
```


## Запуск API сервера в режиме разработки
```shell
uvicorn server.main:app --reload --debug
```

### Получить access_token можно [здесь](https://vkhost.github.io/)


## Получение токена
[Инструкция](https://vk.com/dev/auth_sites)

https://oauth.vk.com/authorize?client_id=7898476&redirect_uri=http://localhost:8000/verify/&scope=0&response_type=code

Запрос на получения токена и vk id
```shell
https://oauth.vk.com/access_token?client_id=7898476&client_secret=VOlOMVKWwkCMxP6PrEBQ&code=1acd5527f4762506cd&redirect_uri=http://localhost:8000/verify/
```

