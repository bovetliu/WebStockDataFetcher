from typing import List, Callable, Set
import logging
import mysql.connector
from mysql.connector.cursor_cext import CMySQLCursor
from mysql.connector import errorcode
from webstkdatafetcher import utility
from webstkdatafetcher import constants


class MySqlHelper:
    """help some simple mysql operation"""

    def __init__(self, db_config_dict: dict = None, reuse_connection=False):
        if not db_config_dict:
            logging.warning('db_config_dict not supplied, going to use default db prop')
            db_config_dict = utility.get_propdict_file(constants.default_db_prop_path)
        if not isinstance(db_config_dict, dict):
            raise ValueError("db_config_dict should be supplied")
        self.__user = db_config_dict['user']
        self.__password = db_config_dict['password']
        self.__host = db_config_dict['host']
        logging.info("MySqlHelper#__init__(), host : {}".format(self.__host))
        self.__database = db_config_dict['database']
        self.__reuse_connection = reuse_connection
        self.__cnx = None

        # in case if it is a new run
        cnx = None
        cursor = None
        try:
            cnx = mysql.connector.connect(user=self.__user, password=self.__password,
                                          host=self.__host,
                                          connection_timeout=10000)
            cursor = cnx.cursor()
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET 'utf8'".format(self.__database))
        finally:
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()

    def execute_update(self, stmt: str, values=None, schema: str = None,
                       callback_on_cursor: Callable[[CMySQLCursor], None] = None,
                       multi=False,
                       *args, **kwarg):
        """
        for UPDATE, INSERT, DELETE statements
        :param stmt: statement string
        :param values values
        :param schema: schema name
        :param callback_on_cursor callback on cursor
        :param multi whether cursor is enable to execute multiple sql statements at one time
        :return: how many records are affected
        """
        if not schema:
            schema = self.__database
        cnx = None
        cursor = None
        retry = 0
        need_retry = True  # this should be set to True, so following while loop can execute at least once
        while retry < 3 and need_retry:
            try:
                need_retry = False  # set need_retry back to False
                if self.__reuse_connection and self.__cnx and self.__cnx.is_connected():
                    cnx = self.__cnx
                else:
                    cnx = mysql.connector.connect(user=self.__user,
                                                  password=self.__password,
                                                  database=schema,
                                                  host=self.__host,
                                                  connection_timeout=10000)
                if self.__reuse_connection:
                    self.__cnx = cnx

                cursor = cnx.cursor()
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    logging.debug("stmt: %s", stmt)
                else:
                    logging.info("stmt: %s", stmt[:10])
                cursor.execute("SET SESSION MAX_EXECUTION_TIME=7000;")
                if values:
                    cursor.execute(stmt, values if isinstance(values, tuple) else tuple(values), multi=multi)
                else:
                    cursor.execute(stmt, multi=multi)
                if callable(callback_on_cursor):
                    callback_on_cursor(cursor, *args, **kwarg)
                elif stmt.lower().strip().startswith("select ") and not callback_on_cursor:
                    # service as default callback
                    row = cursor.fetchone()
                    while row is not None:
                        print(row)
                        row = cursor.fetchone()
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_QUERY_TIMEOUT:
                    logging.error("ER_QUERY_TIMEOUT")
                    need_retry = True
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    logging.error("Something is wrong with your user name or password")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    logging.error("Database does not exist")
                else:
                    logging.error(err)
                if not need_retry:
                    raise err
            finally:
                retry = retry + 1
                if cursor:
                    cursor.close()
                if cnx:
                    cnx.commit()
                    if not self.__reuse_connection:
                        cnx.close()

    def insert_one_record(self, table: str, schema: str=None, col_val_dict: dict = None,
                          col_names: List[str] = None,
                          values: List = None,
                          suppress_duplicate: bool = False):
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
        try:
            self.execute_update(insert_statement, values)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_ENTRY and suppress_duplicate:
                pass  # suppress_duplicate
            else:
                raise err

    def delete_from_table(self, table: str, schema: str=None, col_val_dict: dict = None):
        if not schema:
            schema = self.__database
        if not table:
            raise ValueError("table should be supplied")
        small_equal_conditions = []
        if col_val_dict:
            for col_name, values in col_val_dict.items():
                source = col_name
                if col_name == 'vol_percent' or col_name == 'price':
                    source = "ROUND({}, 6)".format(col_name)
                operation = "="
                if isinstance(values, List) or isinstance(values, Set):
                    operation = "IN"
                target = "%s"
                if isinstance(values, List) or isinstance(values, Set):
                    target = "(" + ', '.join(['%s'] * len(values)) + ")"
                small_equal_conditions.append("{} {} {}".format(source, operation, target))
        where = " AND ".join(small_equal_conditions)
        if where:
            delete_statements = "DELETE FROM `{}`.`{}` WHERE {}".format(schema, table, where)
        else:
            delete_statements = "DELETE FROM `{}`.`{}`".format(schema, table)
        values = []
        for val in col_val_dict.values():
            if isinstance(val, List) or isinstance(val, Set):
                for v in val:
                    values.append(v)
            else:
                values.append(val)
        self.execute_update(delete_statements, tuple(values))

    def select_from(self, table, schema=None, col_names: List[str] = None,
                    col_val_dict: dict = None,
                    callback_on_cursor: Callable[[CMySQLCursor], None] = None, *args, **kwarg):
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

    def set_reuse_connection(self, reuse_connection):
        """
        NOT thread safe
        """
        if type(reuse_connection) != bool:
            raise TypeError("only bool parameter accepted")
        self.__reuse_connection = reuse_connection
        if not reuse_connection:
            if self.__cnx:
                self.__cnx.close()
                self.__cnx = None

    @classmethod
    def default_select_collector(cls, cursor, result_holder: List = None, *args, **kwargs):
        if result_holder is None:
            if len(args) > 0:
                result_holder = args[0]
            else:
                result_holder = kwargs["result_holder"]
        row = cursor.fetchone()
        while row is not None:
            result_holder.append(row[0] if len(row) == 1 else row)
            row = cursor.fetchone()
