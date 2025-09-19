"""Import pymysql bindings as MySQLdb."""

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
