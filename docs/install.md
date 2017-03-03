## Installation details

### Disclaimer: 
Common tips for installation of django-based project are omitted for brevity.
In production this section should at least include installation from package repo and from source, info about dependencies, databases and some best practices ad venv. 

### Settings
To make it work you need to specify some sensible security settings and specific to current instalation settings. They should be placed in ```/card_issuing_excercise/settings/local_settings.py```. They are:
- SECRET_KEY: Django secret key. [Read more](https://docs.djangoproject.com/en/1.10/ref/settings/#secret-key)
- DATABASES: Django basic database settings. [Read more](https://docs.djangoproject.com/en/1.10/ref/settings/#databases)
- ROOT_PASSWORD: A password for the superuser.
- DEBUG=False: Override Django debug mode here.

### Before start
- Tests are run with standart django management command: 
```python 
python3 manage.py test
```
- Run initialization management command to create all service entities (Idempotent and can be run before every startup):
```python
python3 manage.py initialize_before_startup
```
