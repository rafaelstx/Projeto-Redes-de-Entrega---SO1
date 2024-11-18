import threading
import queue
import time
import random
from tkinter import Tk, Label, Button, Frame, StringVar, Text, Scrollbar, RIGHT, Y, END, BOTH
from tkinter import ttk

# Configurações do sistema
CONFIG = {
    "numero_pontos": 5,      # Número de pontos de redistribuição
    "numero_veiculos": 5,    # Número de veículos
    "numero_encomendas": 20, # Número total de encomendas
    "capacidade_veiculo": 2  # Capacidade de carga de cada veículo
}

# Classe que representa uma encomenda
class Encomenda:
    def __init__(self, id, origem, destino):
        self.id = id  # ID único da encomenda
        self.origem = origem  # Ponto de origem da encomenda
        self.destino = destino  # Ponto de destino da encomenda
        self.horario_criacao = time.time()  # Momento em que a encomenda foi criada
        self.horario_carregado = None  # Quando foi carregada em um veículo
        self.horario_descarregado = None  # Quando foi descarregada no destino
        self.veiculo_id = None  # ID do veículo que transportou a encomenda

# Classe que representa um veículo
class Veiculo(threading.Thread):
    def __init__(self, id, pontos, capacidade, lock_pontos, encomendas_restantes, monitoramento_lock, interface):
        super().__init__()
        self.id = id  # ID do veículo
        self.pontos = pontos  # Lista de pontos de redistribuição
        self.capacidade = capacidade  # Capacidade máxima de carga
        self.carga = []  # Lista de encomendas carregadas
        self.local_atual = random.randint(0, len(pontos) - 1)  # Ponto inicial aleatório
        self.lock_pontos = lock_pontos  # Lista de locks para sincronizar acesso aos pontos
        self.encomendas_restantes = encomendas_restantes  # Controle de encomendas pendentes
        self.monitoramento_lock = monitoramento_lock  # Lock para sincronização de monitoramento
        self.interface = interface  # Referência para a interface gráfica
        self.historico = []  # Histórico de ações do veículo

    def run(self):
        # Loop principal do veículo
        while True:
            # Verifica se todas as encomendas foram entregues
            if self.encomendas_restantes[0] <= 0:
                self.interface.update_status(f"Veículo {self.id} terminou as entregas.")
                break

            # Acessa o ponto atual com lock para evitar conflitos
            with self.lock_pontos[self.local_atual]:
                ponto_atual = self.pontos[self.local_atual]

                # Carrega encomendas no veículo enquanto houver espaço e encomendas no ponto
                while len(self.carga) < self.capacidade and not ponto_atual.fila_encomendas.empty():
                    encomenda = ponto_atual.fila_encomendas.get()
                    encomenda.horario_carregado = time.time()
                    encomenda.veiculo_id = self.id
                    self.carga.append(encomenda)
                    self.historico.append(f"Carregou encomenda {encomenda.id} no ponto {self.local_atual}")
                    self.interface.update_status(f"Veículo {self.id} carregou encomenda {encomenda.id} no ponto {self.local_atual}.")

                # Descarrega encomendas que chegaram ao destino
                for encomenda in self.carga[:]:
                    if encomenda.destino == self.local_atual:
                        encomenda.horario_descarregado = time.time()
                        self.carga.remove(encomenda)
                        self.encomendas_restantes[0] -= 1
                        self.historico.append(f"Entregou encomenda {encomenda.id} no ponto {self.local_atual}")
                        self.interface.update_status(f"Veículo {self.id} entregou encomenda {encomenda.id} no ponto {self.local_atual}.")

            # Atualiza a posição do veículo na interface
            self.interface.update_vehicle(self.id, self.local_atual, [e.id for e in self.carga])

            # Move para o próximo ponto (cíclico)
            self.local_atual = (self.local_atual + 1) % len(self.pontos)
            time.sleep(random.uniform(0.1, 0.3))  # Simula tempo de viagem

# Classe que representa um ponto de redistribuição
class Ponto:
    def __init__(self, id):
        self.id = id  # ID do ponto
        self.fila_encomendas = queue.Queue()  # Fila de encomendas no ponto

# Interface gráfica
class Interface:
    def __init__(self, master, num_veiculos):
        self.master = master  # Janela principal do Tkinter
        self.master.title("Simulação de Logística")  # Título da janela
        self.master.geometry("800x600")  # Dimensões da janela
        self.master.configure(bg="#f5f5f5")  # Cor de fundo

        self.status_var = StringVar()  # Variável para exibir mensagens de status
        self.status_var.set("Clique em 'Iniciar Simulação' para começar.")  # Mensagem inicial
        self.results = []  # Lista para armazenar o histórico final

        # Área de Status
        status_frame = Frame(master, bg="#f5f5f5", pady=10)
        status_frame.pack(fill=BOTH, pady=5)
        Label(status_frame, text="Simulação de Logística", font=("Arial", 18, "bold"), bg="#f5f5f5").pack()
        self.status_label = Label(status_frame, textvariable=self.status_var, font=("Arial", 12), bg="#f5f5f5", fg="#333333")
        self.status_label.pack()

        # Botão de Iniciar
        button_frame = Frame(master, bg="#f5f5f5")
        button_frame.pack(fill=BOTH, pady=10)
        self.start_button = ttk.Button(button_frame, text="Iniciar Simulação", command=self.start_simulation)
        self.start_button.pack(pady=5)

        # Área de Veículos
        vehicles_frame = Frame(master, bg="#ffffff", relief="groove", bd=2)
        vehicles_frame.pack(fill=BOTH, padx=10, pady=5, expand=True)
        Label(vehicles_frame, text="Status dos Veículos", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=5)

        self.vehicle_frames = []
        for i in range(num_veiculos):
            frame = Frame(vehicles_frame, bg="#ffffff", pady=2)
            frame.pack(fill=BOTH)
            Label(frame, text=f"Veículo {i}:", font=("Arial", 10, "bold"), bg="#ffffff").pack(side="left", padx=10)
            label = Label(frame, text="Aguardando...", font=("Arial", 10), bg="#ffffff")
            label.pack(side="left")
            self.vehicle_frames.append(label)

        # Área do Histórico
        history_frame = Frame(master, bg="#f5f5f5")
        history_frame.pack(fill=BOTH, padx=10, pady=10, expand=True)
        Label(history_frame, text="Histórico Final", font=("Arial", 14, "bold"), bg="#f5f5f5").pack(pady=5)

        self.history_text = Text(history_frame, wrap="word", height=15, font=("Arial", 10), bg="#ffffff")
        scrollbar = Scrollbar(history_frame, command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.history_text.pack(fill=BOTH, expand=True)

    # Atualiza o status na interface
    def update_status(self, message):
        self.master.after(0, lambda: self.status_var.set(message))

    # Atualiza a posição e carga do veículo
    def update_vehicle(self, vehicle_id, location, carga):
        self.master.after(0, lambda: self.vehicle_frames[vehicle_id].config(text=f"No ponto {location}, Carga: {carga}"))

    # Exibe o histórico final
    def display_results(self, results):
        self.master.after(0, lambda: [
            self.history_text.delete(1.0, END),
            [self.history_text.insert(END, result + "\n") for result in results]
        ])

    # Inicia a simulação
    def start_simulation(self):
        self.start_button.config(state="disabled")  # Desativa o botão
        threading.Thread(target=main, args=(self,)).start()  # Inicia a simulação em um thread separado

# Função principal que organiza e executa a simulação
def main(interface):
    
    S = CONFIG["numero_pontos"]  # Número de pontos de redistribuição
    C = CONFIG["numero_veiculos"] # Número de veículos
    P = CONFIG["numero_encomendas"]  # Número de encomendas
    A = CONFIG["capacidade_veiculo"]  # Capacidade de cada veículo

    # Cria os pontos
    pontos = [Ponto(i) for i in range(S)]
    lock_pontos = [threading.Lock() for _ in range(S)]  # Locks para sincronizar acesso aos pontos

    # Cria as encomendas
    encomendas = []
    for i in range(P):
        origem = random.randint(0, S - 1)
        destino = random.randint(0, S - 1)
        while destino == origem:  # Garante que origem e destino sejam diferentes
            destino = random.randint(0, S - 1)
        encomenda = Encomenda(i, origem, destino)
        pontos[origem].fila_encomendas.put(encomenda)
        encomendas.append(encomenda)

    encomendas_restantes = [P]  # Contador global de encomendas pendentes
    monitoramento_lock = threading.Lock()  # Lock para sincronização de monitoramento

    # Cria os veículos
    veiculos = [Veiculo(i, pontos, A, lock_pontos, encomendas_restantes, monitoramento_lock, interface) for i in range(C)]
    for veiculo in veiculos:
        veiculo.start()
    for veiculo in veiculos:
        veiculo.join()

    # Gera o histórico final
    results = []
    for veiculo in veiculos:
        results.append(f"Veículo {veiculo.id}:")
        results.extend(veiculo.historico)
        results.append("")

    for encomenda in encomendas:
        results.append(
            f"Encomenda {encomenda.id} - Origem: {encomenda.origem}, Destino: {encomenda.destino}, "
            f"Carregada: {time.ctime(encomenda.horario_carregado)}, Entregue: {time.ctime(encomenda.horario_descarregado)}"
        )
    interface.display_results(results)  # Exibe o histórico final
    interface.update_status("Simulação concluída!")  # Atualiza o status final

# Execução do programa
if __name__ == "__main__":
    root = Tk()
    app = Interface(root, num_veiculos=6)  # Inicializa a interface com 6 veículos
    root.mainloop()
