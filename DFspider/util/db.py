#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import logging
import time
import uuid
import functools
from ..util.log import logger

engine = None


class DBError(Exception):
    pass


class MultiColumnsError(Exception):
    pass


def next_id(t=None):
    """
    用于创建写一个唯一的id
    :param t:
    :return:
    """
    if t is None:
        t = time.time()
    return "%015d%s000" % (int(t * 1000), uuid.uuid4().hex)


class _Engine(object):
    def __init__(self, connect):
        self._connect = connect

    def connect(self):
        return self._connect()


class _LazyConnection(object):
    def __init__(self):
        self.connection = None

    def cursor(self):
        if self.connection is None:
            _connection = engine.connect()
            logger.info("Open connection <%s>" % hex(id(_connection)))
            self.connection = _connection
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def cleanup(self):
        if self.connection:
            _connection = self.connection
            self.connection = None
            logger.info('close connection <%s>' % hex(id(_connection)))
            _connection.close()


class _DbCtx(threading.local):
    def __init__(self):
        self.connection = None
        self.transactions = 0

    def is_init(self):
        return self.connection is not None

    def init(self):
        self.connection = _LazyConnection()

    def cleanup(self):
        self.connection.cleanup()
        self.connection = None

    def cursor(self):
        return self.connection.cursor()


_db_ctx = _DbCtx()


def create_engine(user, password, database, host='127.0.0.1', port=3306, **kw):
    import mysql.connector
    global engine

    if engine is not None:
        raise DBError("Engine is already initaialized")

    params = dict(user=user, password=password, database=database, host=host, port=port)
    default = dict(use_unicode=True, charset='utf8', collation='utf8_general_ci', autocommit=False)

    for k, v in default.items():
        params[k] = v

    params.update(kw)
    params['buffered'] = True

    engine = _Engine(lambda: mysql.connector.connect(**params))

    logger.info("Init mysql engine <%s> ok." % hex(id(engine)))


class _ConnectionCtx(object):
    def __enter__(self):
        global _db_ctx
        self.should_cleanup = False

        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_cleanup = True

        return self

    def __exit__(self, exctype, excvalue, traceback):
        global _db_ctx
        if self.should_cleanup:
            _db_ctx.cleanup()


def connection():
    return _ConnectionCtx()


def with_connection(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        with _ConnectionCtx():
            return func(*args, **kw)

    return _wrapper

    # @functools.wraps(func)
    # def _wrapper(*args, **kw):
    #     with _ConnectionCtx():
    #         return func(*args, **kw)
    #
    # return _wrapper


class Dict(dict):
    """
    自定义一个字典，实现可以通过  dict.attr取出其中的值
    """

    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, k, v):
        self[k] = v


def _select(sql, first, *args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    logger.info("SQL:%s , ARGS: %s" % (sql, args))

    try:
        cursor = _db_ctx.cursor()
        cursor.execute(sql, args)
        names = []
        if cursor.description:
            names = [x[0] for x in cursor.description]
        if first:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(names, values)
        return [Dict(names, x) for x in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()


@with_connection
def select_one(sql, *args):
    return _select(sql, True, *args)


@with_connection
def select_int(sql, *args):
    d = _select(sql, True, *args)

    if len(d) != 1:
        raise MultiColumnsError('Expect only one column')


@with_connection
def select(sql, *args):
    return _select(sql, False, *args)


@with_connection
def _update(sql, *args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    logger.info("sql : %s ,args : %s" % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql, args)
        r = cursor.rowcount
        if _db_ctx.transactions == 0:
            logger.info("auto commit")
            _db_ctx.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()


@with_connection
def page_select(page_size: int, table: str, fields: (list, tuple) = None, where_clause=None):
    if where_clause is None:
        where_clause = ""
    elif not isinstance(where_clause, str):
        raise ValueError("where_clause must be str")
    count = select('select count(*) as count_num from ' + table + " " + where_clause)[0]["count_num"]
    # print(count)
    num = int(count / page_size)
    fields_str = "`" + "`,`".join(fields) + "`" if fields and isinstance(fields, (list, tuple)) else "*"
    for i in range(num + 1):
        if i < num:
            start = i * page_size
        else:
            start = num * page_size
        sql = "select " + fields_str + " from `" + table + "` " + where_clause + " limit ?,?"
        items = select(sql, start, page_size)
        for item in items:
            yield item


def insert(table, **kw):
    cols, args = list(zip(*iter(kw.items())))
    # sql='insert into %s(%s) values(%s)'%(table,','.join(cols))
    sql = 'insert into `%s` (%s) values (%s)' % (
        table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)


def update(sql, *args):
    return _update(sql, *args)


class _TransactionCtx(object):
    def __enter__(self):
        global _db_ctx
        self.should_close_conn = False

        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_cleanup = True

        _db_ctx.transactions = _db_ctx.transactions + 1
        return self

    def __exit__(self, exctype, excvalue, traceback):
        global _db_ctx
        _db_ctx.transactions = _db_ctx.transactions - 1
        try:
            if _db_ctx.transactions == 0:
                if exctype is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            if self.should_close_conn:
                _db_ctx.cleanup()

    def commit(self):
        global _db_ctx
        try:
            _db_ctx.connection.commit()
        except:
            _db_ctx.connection.rollback()
            raise

    def rollback(self):
        global _db_ctx
        _db_ctx.connection.rollback()


def transaction():
    return _TransactionCtx()


def _profiling(start, sql=''):
    t = time.time() - start
    if t > 0.1:
        logger.warn("[PROFILING] [DB] %s:%s" % (t, sql))
    else:
        logger.info("[PROFILING] [DB] %s:%s" % (t, sql))


def with_transaction(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        _start = time.time()
        with _TransactionCtx():
            return func(*args, **kw)
        _profiling(_start)

    return _wrapper


if __name__ == '__main__':
    print(("?" * 5))

    logging.basicConfig(level=logging.DEBUG)
    create_engine("root", 'password', 'test09')
    print(engine == None)
    # update("drop table if exists user")
    # update("create table user (id int primary key, name text, email text, passwd text, last_modified real)")
    # insert('user', **{'id': 2, 'name': 'miaodongfang', 'email': 'dongfang@12', 'passwd': 'pwd'})
    import doctest

    doctest.testmod()
