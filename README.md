# MORINS-Backend

### How to run
```
python -m flask --app app run
```

### How to migrate
#### If folder migrations does NOT exists, first we must use this:
```
python -m flask db init
```
#### Folder migration exists or was created:
```
python -m flask db migrate -m "Example message"
```
#### To apply the change to database
```
python -m flask db upgrade
```