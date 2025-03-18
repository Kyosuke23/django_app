# django_app
## 起動方法
#### コンテナイメージ作成
```
docker compose build --no-cache && docker-compose up -d --force-recreate
```
#### ディレクトリ移動(コンテナ内)
```
cd <srcディレクトリのパス>
```

#### DBの初期化(コンテナ内)
```
python manage.py migrate
```

#### DBに初期データを投入(コンテナ内)
```
python manage.py loaddata init.json
```

#### Djangoアプリの起動(コンテナ内)
```
python manage.py runserver 0.0.0.0:8000
```