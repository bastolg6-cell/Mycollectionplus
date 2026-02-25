import pymysql

# 1. On active PyMySQL
pymysql.version_info = (2, 2, 7, "final", 0)
pymysql.install_as_MySQLdb()

# 2. ON FORCE DJANGO À IGNORER LA COMMANDE 'RETURNING'
from django.db.backends.mysql.features import DatabaseFeatures
DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)

# 3. On garde aussi ton ancienne triche pour la version MariaDB si besoin
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.check_database_version_supported = lambda self: None