import sqlite3


def db_connect(func):
    def inner(*args, **kwargs):
        with sqlite3.connect("bot.db") as conn:
            res = func(*args, conn=conn, **kwargs)
            return res
    return inner


@db_connect
def init_bot_db(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS role_reaction (
        guild_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL,
        message_id INTEGER NOT NULL,
        emoji TEXT NOT NULL,
        role_id INTEGER NOT NULL)""")
    conn.commit()


class RolesDatabase:
    def __int__(self):
        pass

    @db_connect
    def role_insert(self, conn, guild_id: int, channel_id: int, message_id: int, emoji: str, role_id: int):
        c = conn.cursor()
        c.execute('INSERT INTO role_reaction (guild_id, channel_id, message_id, emoji, role_id) VALUES (?, ?, ?, ?, ?)', (guild_id, channel_id, message_id, emoji, role_id))
        conn.commit()

    @db_connect
    def db_channel_id(self, conn):
        c = conn.cursor()
        c.execute('SELECT channel_id, message_id, emoji FROM role_reaction')
        res = c.fetchall()
        return res

    @db_connect
    def db_role_delete(self, conn, role_id: int):
        c = conn.cursor()
        c.execute('SELECT message_id, channel_id, emoji FROM role_reaction WHERE role_id = ?', (role_id, ))
        res = c.fetchone()
        c.execute('DELETE FROM role_reaction WHERE role_id = ?', (role_id, ))
        return res

    @db_connect
    def db_role_get(self, conn, guild_id: int, emoji: str):
        c = conn.cursor()
        c.execute('SELECT role_id, channel_id, message_id FROM role_reaction WHERE guild_id = ? AND emoji = ?', (guild_id, emoji))
        res = c.fetchone()
        return res