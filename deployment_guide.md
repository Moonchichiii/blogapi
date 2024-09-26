# Deployment Guide for BlogClient Backend

## Pre-Deployment Settings

Before deploying your BlogClient Backend to Heroku, ensure you've configured the following settings:

1. In `settings.py`:
   - Update `ALLOWED_HOSTS` to include your Heroku app's domain:
     ```python
     ALLOWED_HOSTS = ['yourappdomain.herokuapp.com', 'localhost', '127.0.0.1']
     ```
   - Set `DEBUG = False` for production:
     ```python
     DEBUG = False
     ```
   - Configure your database to use the `dj_database_url` package:
     ```python
     import dj_database_url
     
     DATABASES = {
         'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
     }
     ```
   - Set up whitenoise for static files:
     ```python
     MIDDLEWARE = [
         # ...
         'whitenoise.middleware.WhiteNoiseMiddleware',
     ]
     
     STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
     ```

2. Create a `Procfile` in your project root:
   ```
   web: gunicorn your_project_name.wsgi
   ```

3. Create a `runtime.txt` file specifying your Python version:
   ```
   python-3.9.7
   ```

4. Update `requirements.txt`:
   ```
   pip freeze > requirements.txt
   ```

## Heroku Deployment

1. Create a Heroku account and install the Heroku CLI.

2. Login to Heroku:
   ```
   heroku login
   ```

3. Create a new Heroku app:
   ```
   heroku create your-app-name
   ```

4. Add PostgreSQL addon:
   ```
   heroku addons:create heroku-postgresql:hobby-dev
   ```

5. Configure environment variables:
   ```
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set DJANGO_SETTINGS_MODULE=your_project.settings
   ```

6. Push your code to Heroku:
   ```
   git push heroku main
   ```

7. Run migrations:
   ```
   heroku run python manage.py migrate
   ```

8. Create a superuser:
   ```
   heroku run python manage.py createsuperuser
   ```

## Post-Deployment

1. Visit your app: `https://your-app-name.herokuapp.com`
2. Check the admin interface: `https://your-app-name.herokuapp.com/admin`
3. Monitor your app logs: `heroku logs --tail`

## Troubleshooting

- If you encounter any issues, check the Heroku logs: `heroku logs --tail`
- Ensure all required environment variables are set
- Verify that your `Procfile` and `runtime.txt` are correctly configured

For more detailed information on Heroku deployment, visit the [Heroku Dev Center](https://devcenter.heroku.com/categories/python-support).