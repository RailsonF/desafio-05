"""Testes de regressão dos três chamados do Desafio Final.

Cada teste reproduz o sintoma descrito no chamado e confere o
comportamento definido em REGRAS.md. Rode com: python -m unittest
"""
import unittest

from loja.banco import criar_conexao
from loja.precos import calcular_total
from loja.relatorios import relatorio_clientes
from loja.clientes import buscar_por_email


class TestChamado1TotalDoPedido(unittest.TestCase):
    def setUp(self):
        self.conn = criar_conexao()

    def tearDown(self):
        self.conn.close()

    def test_cupom_maior_que_subtotal_nao_zera_frete(self):
        # 102: subtotal 70, cupom 120 (para em 70), frete 20 -> 20
        self.assertEqual(calcular_total(self.conn, 102), 20.0)
        # 107: subtotal 50, cupom 200 (para em 50), frete 30 -> 30
        self.assertEqual(calcular_total(self.conn, 107), 30.0)

    def test_resto_do_calculo_continua_igual(self):
        esperado = {
            101: 70.0,   # sem cupom, com frete
            103: 150.0,  # frete grátis (subtotal 200) e cupom 50
            104: 75.0,   # dois estornos (30 + 10) subtraídos uma vez cada
            105: 85.0,   # cupom menor que o subtotal
            106: 78.0,   # pedido de 2025, cálculo normal
        }
        for pedido_id, total in esperado.items():
            with self.subTest(pedido=pedido_id):
                self.assertEqual(calcular_total(self.conn, pedido_id), total)

    def test_frete_gratis_usa_subtotal_antes_do_cupom(self):
        # subtotal 150 (exato), cupom 60: frete continua grátis -> 90
        self.conn.execute("INSERT INTO pedidos VALUES (900, 1, 20, 60, '2026-06-01')")
        self.conn.execute("INSERT INTO itens VALUES (900, 900, 'x', 3, 50.0)")
        self.assertEqual(calcular_total(self.conn, 900), 90.0)

    def test_cupom_nao_desconta_frete_com_estorno(self):
        # subtotal 60, cupom 100 (para em 60), frete 20, estorno 5 -> 15
        self.conn.execute("INSERT INTO pedidos VALUES (901, 1, 20, 100, '2026-06-01')")
        self.conn.execute("INSERT INTO itens VALUES (901, 901, 'x', 1, 60.0)")
        self.conn.execute("INSERT INTO estornos VALUES (901, 901, 5.0)")
        self.assertEqual(calcular_total(self.conn, 901), 15.0)


class TestChamado2RelatorioDeClientes(unittest.TestCase):
    def setUp(self):
        self.conn = criar_conexao()

    def tearDown(self):
        self.conn.close()

    def test_relatorio_completo_em_ordem_de_nome(self):
        self.assertEqual(relatorio_clientes(self.conn), [
            ("Ana Batista", "Juazeiro do Norte", 2),
            ("Bruno Callado", "Crato", 1),
            ("Célia Marques", "Barbalha", 1),
            ("Davi Nogueira", "Juazeiro do Norte", 0),   # nunca comprou
            ("Lara Vidal", "Juazeiro do Norte", 0),      # só comprou em 2025
            ("Ort O'Brien", "Crato", 0),                 # nunca comprou
            ("Steve Alex", "Missão Velha", 2),
        ])

    def test_limite_da_janela_de_datas(self):
        self.conn.execute("INSERT INTO pedidos VALUES (910, 7, 0, 0, '2026-01-01')")
        self.conn.execute("INSERT INTO pedidos VALUES (911, 4, 0, 0, '2025-12-31')")
        qtd = {nome: q for nome, _cidade, q in relatorio_clientes(self.conn)}
        self.assertEqual(qtd["Lara Vidal"], 1)      # 01/01/2026 conta
        self.assertEqual(qtd["Davi Nogueira"], 0)   # 31/12/2025 não conta


class TestChamado3BuscaPorEmail(unittest.TestCase):
    def setUp(self):
        self.conn = criar_conexao()

    def tearDown(self):
        self.conn.close()

    def test_email_com_apostrofo(self):
        self.assertEqual(
            buscar_por_email(self.conn, "o'brien@cariri.test"),
            (6, "Ort O'Brien", "Crato"),
        )

    def test_email_forjado_nao_traz_ninguem(self):
        forjados = [
            "x' OR '1'='1",
            "' OR 1=1 --",
            "ana@cariri.test' --",
            "' UNION SELECT id, email, nome FROM clientes --",
            "'; DROP TABLE clientes; --",
        ]
        for email in forjados:
            with self.subTest(email=email):
                self.assertIsNone(buscar_por_email(self.conn, email))
        total = self.conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        self.assertEqual(total, 7)

    def test_email_inexistente_ou_invalido(self):
        for email in ["nao@existe.test", "", None, 123, ["ana@cariri.test"]]:
            with self.subTest(email=email):
                self.assertIsNone(buscar_por_email(self.conn, email))


if __name__ == "__main__":
    unittest.main()
