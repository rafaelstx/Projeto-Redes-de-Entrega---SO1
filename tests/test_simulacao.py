import unittest
from src.simulacao_logistica import Encomenda, Veiculo, Ponto
import queue
import threading


class TestSimulacaoLogistica(unittest.TestCase):

    def test_criacao_encomenda(self):
        """Testa a criação de uma encomenda."""
        encomenda = Encomenda(1, 0, 3)
        self.assertEqual(encomenda.id, 1)
        self.assertEqual(encomenda.origem, 0)
        self.assertEqual(encomenda.destino, 3)
        self.assertIsNone(encomenda.horario_carregado)
        self.assertIsNone(encomenda.horario_descarregado)
        self.assertIsNone(encomenda.veiculo_id)

    def test_adicionar_encomenda_no_ponto(self):
        """Testa se uma encomenda é adicionada ao ponto corretamente."""
        ponto = Ponto(0)
        encomenda = Encomenda(1, 0, 3)
        ponto.fila_encomendas.put(encomenda)
        self.assertFalse(ponto.fila_encomendas.empty())
        self.assertEqual(ponto.fila_encomendas.get().id, 1)

    def test_carregamento_de_encomendas(self):
        """Testa se um veículo carrega encomendas corretamente."""
        ponto = Ponto(0)
        lock_pontos = [threading.Lock() for _ in range(1)]
        encomenda1 = Encomenda(1, 0, 3)
        encomenda2 = Encomenda(2, 0, 2)
        ponto.fila_encomendas.put(encomenda1)
        ponto.fila_encomendas.put(encomenda2)

        veiculo = Veiculo(1, [ponto], 2, lock_pontos, [2], threading.Lock(), None)
        veiculo.local_atual = 0

        with lock_pontos[0]:
            while len(veiculo.carga) < veiculo.capacidade and not ponto.fila_encomendas.empty():
                encomenda = ponto.fila_encomendas.get()
                veiculo.carga.append(encomenda)

        self.assertEqual(len(veiculo.carga), 2)
        self.assertEqual(veiculo.carga[0].id, 1)
        self.assertEqual(veiculo.carga[1].id, 2)

    def test_descarregamento_de_encomendas(self):
        """Testa se um veículo descarrega encomendas no destino."""
        ponto = Ponto(3)
        lock_pontos = [threading.Lock() for _ in range(4)]
        encomenda1 = Encomenda(1, 0, 3)
        encomenda2 = Encomenda(2, 0, 3)

        veiculo = Veiculo(1, [None, None, None, ponto], 2, lock_pontos, [2], threading.Lock(), None)
        veiculo.carga = [encomenda1, encomenda2]
        veiculo.local_atual = 3

        with lock_pontos[3]:
            for encomenda in veiculo.carga[:]:
                if encomenda.destino == veiculo.local_atual:
                    veiculo.carga.remove(encomenda)

        self.assertEqual(len(veiculo.carga), 0)

    def test_fila_encomendas_ponto(self):
        """Testa se o ponto aceita várias encomendas em ordem."""
        ponto = Ponto(0)
        encomendas = [Encomenda(i, 0, 3) for i in range(5)]
        for encomenda in encomendas:
            ponto.fila_encomendas.put(encomenda)

        self.assertEqual(ponto.fila_encomendas.qsize(), 5)

        # Verifica se as encomendas saem na ordem correta
        for i in range(5):
            self.assertEqual(ponto.fila_encomendas.get().id, i)


if __name__ == "__main__":
    unittest.main()
