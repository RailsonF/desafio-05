"""Busca de clientes."""


def buscar_por_email(conn, email):
    """Devolve (id, nome, cidade) do cliente com aquele e-mail, ou None."""
    if not isinstance(email, str):
        return None
    
    sql = "SELECT id, nome, cidade FROM clientes WHERE email = ?"
    linha = conn.execute(sql, (email,)).fetchone()
    return tuple(linha) if linha else None
