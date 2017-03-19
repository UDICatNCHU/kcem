# KCEM

KCEM的class檔，可以透過 `pip` 直接安裝

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

## Prerequisities

1. OS：Ubuntu / OSX would be nice
2. environment：need `python3`

  - Linux：`sudo apt-get update; sudo apt-get install; python3 python3-dev`
  - OSX：`brew install python3`

## Installing

1. `pip install kcem`

## Running & Testing

## Run

1. `settings.py`裏面需要新增`slothTw`這個app：

  - add this:

    ```
    INSTALLED_APPS=[
    ...
    ...
    ...
    'slothTw',
    ]
    ```

2. `urls.py`需要新增下列代碼 把所有search開頭的request都導向到`slothTw`這個app：

  - add this:

    ```
    import slothTw.urls
    urlpatterns += [
        url(r'^sloth/',include(slothTw.urls,namespace="slothTw") ),
    ]
    ```
    ## Usage

      ```
      from kcem import KCEM

      k = KCEM()
      k.get(keyword, lang, num, kem_topn_num, kcm_topn_num)
      ```

3. `python manage.py runserver`：即可進入頁面測試 `slothTw` 是否安裝成功。

### Break down into end to end tests

目前還沒寫測試...

### And coding style tests

目前沒有coding style tests...

## Deployment

`kcem` is a django-app, so depends on django project.

`kcem` 是一般的django插件，所以必須依存於django專案

## Built With

- simplejson
- djangoApiDec,
- pymongo,

## Contributors

- **張泰瑋** [david](https://github.com/david30907d)

## License

This package use `GPL3.0` License.