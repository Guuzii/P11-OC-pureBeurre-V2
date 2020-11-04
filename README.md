# Projet-11-PurBeurre

Web app made with Django that uses OpenFoodFacts API to find substitute to some product through a research by name.
This programm has been developped for a python course.

OpenFoodFacts : https://world.openfoodfacts.org/

## Requirements

    - Python 3.7
    - Pip
    - Pipenv
    - PostgreSQL 12.0

## Installation

    - Clone the project
    - Creat new database
    - Change database credentials in pureBeurreOC/settings/__init__.py
    - Setup virtual env : pipenv --python 3.7
    - Get into your virtual env : pipenv shell
    - Install requirements : pipenv install
    - Collect static, create DB and create superuser using manage.py
    - Insert datas in DB using custom command : python manage.py database_update
    - Start project : python manage.py runserver

When executing the command database_update, the app needs access to OpenFoodFacts API.

## Usage

Get to the url where your app is deploy.
From now you can search for a product and the system will give you a list of substitute that have a better nutrition score than the one searched.
If you are authenticated you can add products to your favorites and post comments on products.