from typing import List, Callable
import mysql.connector
from mysql.connector.cursor_cext import CMySQLCursor
from mysql.connector import errorcode
from webstkdatafetcher import utility
from webstkdatafetcher import constants


class MySqlHelper:
    """help some simple mysql operation"""

    def __init__(self, db_config_dict: dict = None):
        if not db_config_dict:
            print('db_config_dict not supplied, going to use default db prop')
            db_config_dict = utility.get_propdict_file(constants.default_db_prop_path)
        if not isinstance(db_config_dict, dict):
            raise ValueError("db_config_dict should be supplied")
        self.__user = db_config_dict['user']
        self.__password = db_config_dict['password']
        self.__host = db_config_dict['host']
        self.__database = db_config_dict['database']

    def execute_update(self, stmt: str, values=None, schema: str = None,
                       callback_on_cursor: Callable[[CMySQLCursor], None] = None, *args, **kwarg):
        """
        for UPDATE, INSERT, DELETE statements
        :param stmt: statement string
        :param values values
        :param schema: schema name
        :param callback_on_cursor callback on cursor
        :return: how many records are affected
        """
        if not schema:
            schema = self.__database
        cnx = None
        cursor = None
        try:
            cnx = mysql.connector.connect(user=self.__user,
                                          password=self.__password,
                                          database=schema,
                                          host=self.__host)

            cursor = cnx.cursor()
            print("stmt: {}".format(stmt))
            if values:
                cursor.execute(stmt, values if isinstance(values, tuple) else tuple(values))
            else:
                cursor.execute(stmt)
            if callable(callback_on_cursor):
                callback_on_cursor(cursor, *args, **kwarg)
            elif stmt.lower().strip().startswith("select ") and not callback_on_cursor:
                # service as default callback
                row = cursor.fetchone()
                while row is not None:
                    print(row)
                    row = cursor.fetchone()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
            raise err
        finally:
            if cursor:
                cursor.close()
            if cnx:
                cnx.commit()
                cnx.close()

    def insert_one_record(self, table: str, schema: str=None, col_val_dict: dict = None,
                          col_names: List[str] = None,
                          values: List[str] = None):
        if not schema:
            schema = self.__database
        if (not isinstance(col_val_dict, dict)) and (not isinstance(col_names, list) or not isinstance(values, list)):
            raise TypeError('Should either supply colname_val_dict or (colnames and values)')
        if (col_names and not values) or (not col_names and values):
            raise ValueError("colnames and values should both be supplied")
        if col_names and len(col_names) != len(values):
            raise ValueError("lengths of colnames and values should be equal.")
        if isinstance(col_val_dict, dict):
            col_names = []
            values = []
            for key, value in col_val_dict.items():
                col_names.append(key)
                values.append(value)
        insert_statement = "INSERT INTO `{}`.`{}` ({}) VALUES ({})".format(
            schema, table, ", ".join(col_names), ", ".join(['%s'] * len(col_names)))
        self.execute_update(insert_statement, values)

    def delete_table(self, table: str, schema: str=None, col_val_dict: dict = None):
        if not schema:
            schema = self.__database
        if not table:
            raise ValueError("table should be supplied")
        small_equal_conditions = []
        if col_val_dict:
            for col_name in col_val_dict.keys():
                if col_name == 'vol_percent' or col_name == 'price':
                    small_equal_conditions.append("ROUND({}, 6) = %s".format(col_name))
                else:
                    small_equal_conditions.append("{} = %s".format(col_name))
        where = " AND ".join(small_equal_conditions)
        if where:
            delete_statements = "DELETE FROM `{}`.`{}` WHERE {}".format(schema, table, where)
        else:
            delete_statements = "DELETE FROM `{}`.`{}`".format(schema, table)
        self.execute_update(delete_statements, tuple(col_val_dict.values()))

    def select(self, table, schema=None, col_names=None,
               col_val_dict: dict=None,
               callback_on_cursor: Callable[[CMySQLCursor], None] = None,  *args, **kwarg):
        if not schema:
            schema = self.__database

        if not table:
            raise ValueError("table should be supplied")

        cols = "*" if not col_names else ", ".join(col_names)
        small_equal_conditions = []
        if col_val_dict:
            for col_name in col_val_dict.keys():
                if col_name == 'vol_percent' or col_name == 'price':
                    small_equal_conditions.append("ROUND({}, 6) = %s".format(col_name))
                else:
                    small_equal_conditions.append("{} = %s".format(col_name))
        where = " AND ".join(small_equal_conditions)
        if where:
            select_statements = "SELECT {} FROM `{}`.`{}` WHERE {}".format(cols, schema, table, where)
        else:
            select_statements = "SELECT {} FROM `{}`.`{}`".format(cols, schema, table,)
        self.execute_update(select_statements,
                            tuple(col_val_dict.values()) if col_val_dict else None,
                            callback_on_cursor=callback_on_cursor, *args, **kwarg)









