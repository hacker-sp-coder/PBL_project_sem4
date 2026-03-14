# Django settings.py snippet for database configuration
# Add this to your Django project's settings.py file

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',  # Replace with your actual database name
        'USER': 'your_username',       # Replace with your MySQL username
        'PASSWORD': 'your_password',   # Replace with your MySQL password
        'HOST': 'localhost',           # Replace with your MySQL host if different
        'PORT': '3306',                # Replace with your MySQL port if different
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Ensure you have the mysqlclient package installed: pip install mysqlclient
# For Windows, you might need to install it via conda or use pymysql instead