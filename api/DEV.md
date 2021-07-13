
Документация по [fastapi](https://fastapi.tiangolo.com/)


## Запуск API сервера в режиме разработки
```shell
uvicorn main:app --reload
```

### Получить access_token можно [здесь](https://vkhost.github.io/)


## Получение токена
[Инструкция](https://vk.com/dev/auth_sites)

https://oauth.vk.com/authorize?client_id=7898476&redirect_uri=http://localhost:8000/verify/&scope=0&response_type=code

Запрос на получения токена и vk id
```shell
https://oauth.vk.com/access_token?client_id=7898476&client_secret=VOlOMVKWwkCMxP6PrEBQ&code=1acd5527f4762506cd&redirect_uri=http://localhost:8000/verify/
```