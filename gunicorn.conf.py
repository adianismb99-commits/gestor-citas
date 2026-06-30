# gunicorn.conf.py
import multiprocessing

# Timeout más largo (5 minutos para páginas lentas)
timeout = 300

# Número de workers (1 es suficiente para el plan gratuito)
workers = 1

# Threads por worker
threads = 2

# Mantener la conexión viva
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'