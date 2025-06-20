# Тестовове задание

## Задача
Требуется разработать микросервис для Службы международной доставки. Сервис должен получать данные о посылках и рассчитывать им стоимость доставки.


Сервис должен содержать роуты:
Зарегистрировать посылку. Информация о посылке должна содержать: название, вес, тип, стоимость содержимого в долларах.  Входные данные должны быть в формате json. При получении нужно их валидировать. Если валидация прошла успешно — выдать индивидуальный id посылки, доступный только пользователю, подавшему запрос на регистрацию посылки, в рамках его сессии.
Получить все типы посылок и id типов. Посылки бывают 3х типов: одежда, электроника, разное. Типы должны храниться в отдельной таблице в базе данных.
Получить список своих посылок со всеми полями, включая имя типа посылки и стоимость доставки (если она уже рассчитана). Также должна быть пагинация и возможность фильтровать посылки по типу и факту наличия рассчитанной стоимости доставки. 
Получить данные о посылке по ее id. Данные включают: название, вес, тип посылки, ее стоимость, стоимость доставки.

Периодические задачи:
Раз в 5 минут выставлять всем необработанным посылкам стоимости  доставки в рублях.
Стоимость доставки вычисляется по формуле:
	 Стоимость = (вес в кг * 0.5 + стоимость содержимого в долларах * 0.01 ) * курс доллара к рублю
Курс доллара к рублю брать тут https://www.cbr-xml-daily.ru/daily_json.js и кешировать в redis.

Примечание: 
Если стоимость доставки еще не рассчитана - выводить “Не рассчитано”.
Добавить возможность запуска периодических задач вне расписания для нужд отладки.

Обязательные требования:
Приложение НЕ содержит авторизации.
Приложение отслеживает пользователей по сессии, т.е. у каждого пользователя свой список посылок.
Данные хранятся в MySQL.
Реализация на выбор: на Django или на FastAPI (с валидацией через pydantic).
Описание API через Swagger.
Докеризация результата (docker-compose up для запуска сервиса и всех зависимостей).
Особое внимание нужно уделить:
Стандартизации ошибок и ответов.
Логированию.
Кэшированию.
Обработке ошибок.
Чистоте и понятности кода.
Следованию общепринятым стандартам программирования на python.
Документированию основных методов.

Плюсом будет:
В случае выбора Django - реализация через DjangoRestFramework. 
Использование асинхронности (если используем FastAPI).
Покрытие API тестами.
Веб-интерфейс к приложению.
Выполнение одного из дополнительных заданий:
Предположим, у нас в день бывает миллион посылок. Есть техническое условие - хранить лог расчётов стоимостей доставок в MongoDB. Предложите и реализуйте способ подсчета суммы стоимостей доставок всех посылок по типам за день, используя информацию из этого лога.
Реализовать регистрацию посылок используя RabbitMQ. Посылки из роута регистрации попадают не напрямую в БД, а через брокер сообщений и воркеры, которые попутно сразу же рассчитают стоимость доставки. Периодическая задача расчета стоимость доставки больше не нужна.
Создать роут привязки посылки к транспортной компании (добавить id компании - любое положительное число - к записи посылки), которая ее будет доставлять. Одну посылку могут попытаться привязать разные компании, поэтому необходимо обеспечить гарантию, что 1-й обратившаяся компания закрепит посылку за собой. У нас высоконагруженная система - запросы могут прилетать несколько раз в секунду.

Если в процессе выполнения задания возникли какие-либо затруднения в решениях, то необходимо задокументировать обоснование этих решений, либо указать это в сопроводительном письме при передаче решения тестового задания.



# Сделанно

Основной функционал:
Разработка микросервиса на FastAPI с использованием асинхронных обработчиков. - **реализовано**

Регистрация посылок с валидацией входных данных через Pydantic. - **реализовано**

Привязка посылок к сессии пользователя (без авторизации). - **реализовано**

Хранение данных в базе данных MySQL. - **реализовано**

Выдача уникального ID посылки в рамках сессии пользователя. - **реализовано**

Получение всех типов посылок из отдельной таблицы. - **реализовано**

Получение списка посылок пользователя с пагинацией и фильтрацией по типу и наличию стоимости доставки. - **реализовано**

Получение полной информации о посылке по её ID. - **реализовано**

Расчёт стоимости доставки по формуле, заданной в техническом задании. - **реализовано**

Периодическая задача, автоматически рассчитывающая стоимость доставки раз в 5 минут. - **не нужно**

Поддержка принудительного запуска расчёта доставки вручную (для отладки). - **реализовано**

Кеширование курса USD → RUB через Redis. - **реализовано**

Логирование всех ключевых действий и ошибок через Loguru. - **реализовано**

Документирование API через OpenAPI/Swagger. - **реализовано**

Докеризация сервиса и всех зависимостей (docker-compose). - **реализовано**

Обработка и стандартизация ошибок. - **реализовано**

Поддержка переменных окружения и конфигураций через Pydantic Settings. - **реализовано**

Поддержка миграций базы данных через Alembic. - **реализовано**

Дополнительно реализовано:
Логирование расчётов стоимости доставки в MongoDB. - **реализовано**

Подсчёт суммы доставок по типам за день на основе логов в MongoDB. - **реализовано**

Использование aiohttp и асинхронной работы с Redis для максимальной производительности. - **реализовано**

Подготовка тестов на ключевые компоненты приложения.  - **не полность  реализовано**

Чистая архитектура проекта: разделение логики на слои, использование паттернов Repository и Unit of Work. **реализовано**


Что не успел реализовать в проекте:

- реализовать middelware для проверки ключа индепотентности
- покрыть код тестами (тестировал в ручную)
- внедрить grafanna + Loki для сбора метрик и логов 
- разделить deocker контейнер на build и prod 
- выправить код с mypy + ruff
- сегенировать документацию sphinx
- допилить кастомную докумментацию для сокрытия технических тегов 

Для более детального разбора в папке `docs` хранится png изображение архитетуры, там есть схемы и описание принятых решений,
упор был сделан на устойчивость системы. Схему можно загрузить на этом сайте и посмотреть более детально `https://app.diagrams.net/`, 
закинул одним коммитом, так как не успевал их делать во время работы.

Запустить приложение можно через `docker-compose up -d build` мигрцаии и иницализация rabbit mq собраны через init-containers

Для тестирования используйте сперва ручку session-id для получения x-session-id. 

Пример env файла
```
# === App ===
APP_API_VERSION=v1
APP_DEBUG=false

# === Meta App ===
META_TITLE_APP=Deliviry Service
META_VERSION_APP=1.0.0
META_DESCRIPTION_APP=Сервис международной доставки
META_DOCS_URL_APP=/docs
META_REDOC_URL_APP=/redoc
META_OPENAPI_URL_APP=/openapi.json

# === Logging ===
LOGGING_ENABLED=true
LOGGING_LEVEL=DEBUG
LOGGING_FRIENDLY_ASC=true
LOGGING_BACKTRACE=true

# === Database ===
DATABASE_TYPE=mysql
DATABASE_HOST=mysql
DATABASE_PORT=3306
DATABASE_USER=parcel_user
DATABASE_PASSWORD=parcel_pass
DATABASE_NAME=parcel_db

# === Redis ===
REDIS_URL=redis://redis:6379
REDIS_MAX_CONNECTIONS=20

# === RabbitMQ ===
RABBITMQ_URL= amqp://guest:guest@rabbitmq:5672/
RABBITMQ_ROUTING_KEY= parcel.*
RABBITMQ_EXCHANGE= parcel_exchange
RABBITMQ_QUEUE= parcel_registry_queue
RABBITMQ_PREFETCH_COUNT= 10
RABBITMQ_CONSUMER_TAG= delivery_worker
RABBITMQ_DURABLE= "true"
RABBITMQ_AUTO_ACK= "false"


# === MongoDB ===
MONGO_URI = mongodb://root:rootpass@mongo:27017
MONGO_DB_NAME = delivery_logs
MONGO_COLLECTION_NAME = calculations
```