# Face verification demo

## Description

Реализация графического интерфейса для системы лицевой верификации. В данном приложении эмулируется система цифрового онбординга,
использующая технологию лицевой верификации. 

## Installation
### With Docker

```bash
docker install -t fv_telegram_ui .
```
### With poetry
```bash
poetry install .
```
### With PIP
```bash
pip install .
```

## Start telegram bot 
### With Docker
```bash
docker run -e TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN fv_telegram_ui
```
### With python
```bash
python telegram_ui/run.py $TELEGRAM_BOT_TOKEN
```
