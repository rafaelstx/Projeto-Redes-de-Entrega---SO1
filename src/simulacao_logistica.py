from datetime import datetime
import os
import shutil  # Importa o módulo shutil
import threading
import queue
import time
import random
from tkinter import Tk, Label, Button, Frame, StringVar, Text, Scrollbar, RIGHT, Y, END, BOTH, Entry, E
from tkinter import ttk
from tkinter import messagebox

# Configurações do sistema (inicialmente vazias)
CONFIG = {
    "numero_pontos": None,      # Número de pontos de redistribuição (S)
    "numero_veiculos": None,    # Número de veículos (C)
    "numero_encomendas": None,  # Número total de encomendas (P)
    "capacidade_veiculo": None  # Capacidade de carga de cada veículo (A)
}

# Classe que representa uma encomenda
class Encomenda(threading.Thread):
    def __init__(self, id, origem, destino, pontos, interface):
        super().__init__()
        self.id = id  # ID único da encomenda
        self.origem = origem  # Ponto de origem da encomenda
        self.destino = destino  # Ponto de destino da encomenda
        self.pontos = pontos  # Referência aos pontos
        self.horario_criacao = time.time()  # Momento em que a encomenda foi criada
        self.horario_carregado = None  # Quando foi carregada em um veículo
        self.horario_descarregado = None  # Quando foi descarregada no destino
        self.veiculo_id = None  # ID do veículo que transportou a encomenda
        self.delivered_event = threading.Event()  # Evento para sinalizar entrega
        self.interface = interface  # Referência para a interface

    def run(self):
        # Enfileira-se no ponto de origem
        self.pontos[self.origem].enqueue_encomenda(self)
        # Atualiza a interface do ponto
        self.interface.update_point(self.origem, self.pontos[self.origem].get_cargas())
        # Aguarda ser carregada no veículo
        while self.horario_carregado is None:
            time.sleep(0.1)
        # Aguarda ser entregue
        self.delivered_event.wait()
        # Registra o horário de descarregamento
        self.horario_descarregado = time.time()
        # Escreve o arquivo de rastro
        self.gerar_rastro()
        # Thread finaliza após entrega

    def gerar_rastro(self):
        # Formata os horários
        horario_criacao = time.strftime('%H:%M:%S', time.localtime(self.horario_criacao))
        horario_carregado = time.strftime('%H:%M:%S', time.localtime(self.horario_carregado))
        horario_descarregado = time.strftime('%H:%M:%S', time.localtime(self.horario_descarregado))

        # Conteúdo do arquivo de rastro
        conteudo = (
            f"Encomenda ID: {self.id}\n"
            f"Origem: {self.origem}\n"
            f"Destino: {self.destino}\n"
            f"Horário de Chegada ao Ponto de Origem: {horario_criacao}\n"  # Assumindo que chegou ao ponto ao ser criada
            f"Horário de Carregamento no Veículo: {horario_carregado}\n"
            f"ID do Veículo: {self.veiculo_id}\n"
            f"Horário de Descarregamento no Destino: {horario_descarregado}\n"
        )

        # Nome do arquivo de rastro
        nome_arquivo = f"rastros/encomenda_{self.id}.txt"

        # Escreve o arquivo
        with open(nome_arquivo, 'w') as arquivo:
            arquivo.write(conteudo)

# Classe que representa um veículo
class Veiculo(threading.Thread):
    def __init__(self, id, pontos, capacidade, lock_pontos, encomendas_restantes, monitoramento_lock, interface):
        super().__init__()
        self.id = id  # ID do veículo
        self.pontos = pontos  # Lista de pontos de redistribuição
        self.capacidade = capacidade  # Capacidade máxima de carga
        self.carga = []  # Lista de encomendas carregadas
        self.carga_semaphore = threading.Semaphore(capacidade)  # Semáforo para controlar a capacidade
        self.local_atual = random.randint(0, len(pontos) - 1)  # Ponto inicial aleatório
        self.lock_pontos = lock_pontos  # Locks para sincronizar acesso aos pontos
        self.encomendas_restantes = encomendas_restantes  # Controle de encomendas pendentes
        self.monitoramento_lock = monitoramento_lock  # Lock usado para sincronizar operações que alteram o número de encomendas restantes. Garante que dois veículos não reduzam o contador simultaneamente.
        self.interface = interface  # Referência para a interface gráfica
        self.historico = []  # Histórico de ações do veículo

    def run(self):
        # Loop principal do veículo
        while True:
            # Verifica se todas as encomendas foram entregues
            with self.monitoramento_lock:
                if self.encomendas_restantes[0] <= 0:
                    self.interface.update_status(f"Veículo {self.id} terminou as entregas.")
                    break

            # Acessa o ponto atual com lock para evitar conflitos
            with self.lock_pontos[self.local_atual]: # O lock do ponto atual impede que outro veículo acesse o mesmo ponto simultaneamente.
                ponto_atual = self.pontos[self.local_atual]

                # Carrega encomendas no veículo enquanto houver encomendas no ponto
                while len(self.carga) < self.capacidade:
                    encomenda = ponto_atual.get_encomenda()
                    if encomenda is None:
                        break
                    self.carga_semaphore.acquire()  # Adquire um espaço de carga
                    encomenda.horario_carregado = time.time() # Informações sobre a encomenda são atualizadas
                    encomenda.veiculo_id = self.id # Informações sobre a encomenda são atualizadas
                    self.carga.append(encomenda) # A encomenda é adicionada à lista de carga do veículo
                    self.historico.append(f"Carregou encomenda {encomenda.id} no ponto {self.local_atual}")
                    self.interface.update_status(f"Veículo {self.id} carregou encomenda {encomenda.id} no ponto {self.local_atual}.")
                    # Atualiza a interface do ponto
                    self.interface.update_point(self.local_atual, ponto_atual.get_cargas())

            # Descarrega encomendas que chegaram ao destino
            for encomenda in self.carga[:]:  # Feito com a cópia da lista para não causar problemas com a modificação da própria lista
                if encomenda.destino == self.local_atual:
                    # Simula tempo aleatório de descarregamento
                    time.sleep(random.uniform(1, 1.9))
                    encomenda.horario_descarregado = time.time() #Atualiza o horário de descarregamento
                    self.carga.remove(encomenda) # Remove a encomenda da carga do veículo
                    self.carga_semaphore.release()  # Libera um espaço de carga
                    with self.monitoramento_lock:
                        self.encomendas_restantes[0] -= 1 # Reduz o contador global de encomendas restantes 
                    encomenda.delivered_event.set()  # Sinaliza que a encomenda foi entregue
                    self.historico.append(f"Entregou encomenda {encomenda.id} no ponto {self.local_atual}")
                    self.interface.update_status(f"Veículo {self.id} entregou encomenda {encomenda.id} no ponto {self.local_atual}.")

            # Atualiza a posição do veículo na interface
            self.interface.update_vehicle(self.id, self.local_atual, [e.id for e in self.carga])

            # Move para o próximo ponto (cíclico)
            self.local_atual = (self.local_atual + 1) % len(self.pontos)
            time.sleep(random.uniform(0.1, 0.6))  # Simula tempo de viagem

# Classe que representa um ponto de redistribuição
class Ponto(threading.Thread):
    def __init__(self, id):
        super().__init__()
        self.id = id  # ID do ponto
        self.fila_encomendas = queue.Queue()  # Fila de encomendas no ponto
        self.fila_lock = threading.Lock()  # Lock para acesso à fila. Garante que apenas um thread (veículo ou encomenda) possa modificar a fila por vez, evitando condições de corrida.
        self.running = True  # Controle para finalizar o thread, enquanto for True, o método run continuará em execução

    def enqueue_encomenda(self, encomenda): # Adicionar uma encomenda na fila do ponto
        with self.fila_lock:
            self.fila_encomendas.put(encomenda)

    def get_encomenda(self): # Retirar uma encomenda da fila para que um veículo possa carregá-la
        with self.fila_lock:
            if not self.fila_encomendas.empty(): # Verifica se a fila não está vazia
                return self.fila_encomendas.get() # Se houver encomendas disponíveis, remove e retorna a encomenda
            else:
                return None

    def get_cargas(self): # Retornar uma lista com os IDs das encomendas atualmente na fila do ponto
        with self.fila_lock:
            return [encomenda.id for encomenda in list(self.fila_encomendas.queue)]

    def run(self):
        # O ponto pode realizar operações adicionais se necessário
        while self.running:
            time.sleep(0.1)  # Simula alguma atividade

# Interface gráfica
class Interface:
    def __init__(self, master):
        self.master = master  # Janela principal do Tkinter
        self.master.title("Simulação de Logística")  # Título da janela
        self.master.geometry("800x800")  # Dimensões da janela
        self.master.configure(bg="#f5f5f5")  # Cor de fundo

        self.status_var = StringVar()  # Variável para exibir mensagens de status
        self.status_var.set("Insira os parâmetros e clique em 'Iniciar Simulação'.")  # Mensagem inicial
        self.results = []  # Lista para armazenar o histórico final

        # Área de Status
        status_frame = Frame(master, bg="#f5f5f5", pady=10)
        status_frame.pack(fill=BOTH, pady=5)
        Label(status_frame, text="Simulação de Logística", font=("Arial", 18, "bold"), bg="#f5f5f5").pack()
        self.status_label = Label(status_frame, textvariable=self.status_var, font=("Arial", 12), bg="#f5f5f5", fg="#333333")
        self.status_label.pack()

        # Área de Entrada de Parâmetros
        params_frame = Frame(master, bg="#f5f5f5")
        params_frame.pack(fill=BOTH, pady=10)

        # Labels e Entradas para S, C, P e A
        Label(params_frame, text="Número de pontos de redistribuição (S):", bg="#f5f5f5").grid(row=0, column=0, sticky=E, padx=5, pady=2)
        self.entry_S = Entry(params_frame)
        self.entry_S.grid(row=0, column=1, padx=5, pady=2)

        Label(params_frame, text="Número de veículos (C):", bg="#f5f5f5").grid(row=1, column=0, sticky=E, padx=5, pady=2)
        self.entry_C = Entry(params_frame)
        self.entry_C.grid(row=1, column=1, padx=5, pady=2)

        Label(params_frame, text="Capacidade de carga de cada veículo (A):", bg="#f5f5f5").grid(row=2, column=0, sticky=E, padx=5, pady=2)
        self.entry_A = Entry(params_frame)
        self.entry_A.grid(row=2, column=1, padx=5, pady=2)

        Label(params_frame, text="Número total de encomendas (P):", bg="#f5f5f5").grid(row=3, column=0, sticky=E, padx=5, pady=2)
        self.entry_P = Entry(params_frame)
        self.entry_P.grid(row=3, column=1, padx=5, pady=2)

        # Botão de Iniciar
        button_frame = Frame(master, bg="#f5f5f5")
        button_frame.pack(fill=BOTH, pady=10)
        self.start_button = ttk.Button(button_frame, text="Iniciar Simulação", command=self.start_simulation)
        self.start_button.pack(pady=5)

        # Área de Veículos
        self.vehicles_frame = Frame(master, bg="#ffffff", relief="groove", bd=2)
        self.vehicles_frame.pack(fill=BOTH, padx=10, pady=5, expand=True)

        # Área dos Pontos
        self.points_frame = Frame(master, bg="#ffffff", relief="groove", bd=2)
        self.points_frame.pack(fill=BOTH, padx=10, pady=5, expand=True)

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

    # Atualiza o status de um ponto
    def update_point(self, point_id, cargas):
        self.master.after(0, lambda: self.point_frames[point_id].config(text=f"Cargas: {cargas}"))

    # Exibe o histórico final
    def display_results(self, results):
        self.master.after(0, lambda: [
            self.history_text.delete(1.0, END),
            [self.history_text.insert(END, result + "\n") for result in results]
        ])

    # Inicia a simulação
    def start_simulation(self):
        # Obter os valores dos parâmetros
        try:
            S = int(self.entry_S.get())
            C = int(self.entry_C.get())
            A = int(self.entry_A.get())
            P = int(self.entry_P.get())

            # Validações
            if S <= 0 or C <= 0 or A <= 0 or P <= 0:
                raise ValueError("Todos os valores devem ser inteiros positivos.")

            if A <= C:
                raise ValueError("A capacidade A deve ser maior que o número de veículos C.")
            if P <= A:
                raise ValueError("O número de encomendas P deve ser maior que a capacidade A.")

            # Atualiza o CONFIG
            CONFIG["numero_pontos"] = S
            CONFIG["numero_veiculos"] = C
            CONFIG["capacidade_veiculo"] = A
            CONFIG["numero_encomendas"] = P

            # Criação de pasta caso não exista
            if os.path.exists('rastros'):
                shutil.rmtree('rastros')
            os.makedirs('rastros')

            # Remove a área de entrada de parâmetros
            self.entry_S.config(state='disabled') # Impede o usuário de alterar os parâmetros após o início da simulação
            self.entry_C.config(state='disabled')
            self.entry_A.config(state='disabled')
            self.entry_P.config(state='disabled')
            self.start_button.config(state="disabled")  # Desativa o botão Iniciar Simulação

            # Atualiza a interface para mostrar os veículos
            Label(self.vehicles_frame, text="Status dos Veículos", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=5)

            self.vehicle_frames = []
            for i in range(C):
                frame = Frame(self.vehicles_frame, bg="#ffffff", pady=2)
                frame.pack(fill=BOTH)
                Label(frame, text=f"Veículo {i}:", font=("Arial", 10, "bold"), bg="#ffffff").pack(side="left", padx=10)
                label = Label(frame, text="Aguardando...", font=("Arial", 10), bg="#ffffff")
                label.pack(side="left")
                self.vehicle_frames.append(label)

            # Atualiza a interface para mostrar os pontos
            Label(self.points_frame, text="Status dos Pontos", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=5)

            self.point_frames = []
            for i in range(S):
                frame = Frame(self.points_frame, bg="#ffffff", pady=2)
                frame.pack(fill=BOTH)
                Label(frame, text=f"Ponto {i}:", font=("Arial", 10, "bold"), bg="#ffffff").pack(side="left", padx=10)
                label = Label(frame, text="Cargas: []", font=("Arial", 10), bg="#ffffff")
                label.pack(side="left")
                self.point_frames.append(label)

            # Inicia a simulação em um thread separado
            # Passa a interface atual como argumento para que possa ser atualizada durante a simulação
            # E o uso de daemon=True garante que o thread da simulação será encerrado automaticamente quando o programa for fechado.
            threading.Thread(target=main, args=(self,), daemon=True).start() 
        except ValueError as ve:
            messagebox.showerror("Erro de Entrada", str(ve))
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")

# Função principal que organiza e executa a simulação
def main(interface):

    S = CONFIG["numero_pontos"]  # Número de pontos de redistribuição
    C = CONFIG["numero_veiculos"]  # Número de veículos
    P = CONFIG["numero_encomendas"]  # Número de encomendas
    A = CONFIG["capacidade_veiculo"]  # Capacidade de cada veículo

    # Cria os pontos
    pontos = [Ponto(i) for i in range(S)]
    lock_pontos = [threading.Lock() for _ in range(S)]  # Cria uma lista de locks (threading.Lock) para garantir que apenas um veículo acesse um ponto de redistribuição por vez

    # Inicia os threads dos pontos
    for ponto in pontos:
        ponto.start()

    encomendas_restantes = [P]  # Contador global de encomendas pendentes
    monitoramento_lock = threading.Lock()  # Um lock para evitar condições de corrida durante a atualização do contador de encomendas pendentes

    # Cria os veículos
    veiculos = [Veiculo(i, pontos, A, lock_pontos, encomendas_restantes, monitoramento_lock, interface) for i in range(C)]
    for veiculo in veiculos:
        veiculo.start()

    # Cria as encomendas
    encomendas = []
    # Distribui as primeiras encomendas de forma que cada veículo tenha pelo menos uma encomenda para carregar
    for i, veiculo in enumerate(veiculos):
        origem = veiculo.local_atual  # Garante que o veículo encontre uma encomenda em seu local atual
        destino = random.randint(0, S - 1) # O destino é gerado aleatoriamente, mas diferente da origem
        while destino == origem:
            destino = random.randint(0, S - 1)
        encomenda = Encomenda(i, origem, destino, pontos, interface)
        encomendas.append(encomenda)
        encomenda.start() # Inicia os threads das encomendas

    # Cria as demais encomendas (de C até P-1)
    for i in range(C, P):
        origem = random.randint(0, S - 1)
        destino = random.randint(0, S - 1)
        while destino == origem:
            destino = random.randint(0, S - 1)
        encomenda = Encomenda(i, origem, destino, pontos, interface)
        encomendas.append(encomenda)
        encomenda.start()

    # Espera que todos os threads de encomendas sejam concluídos
    for encomenda in encomendas:
        encomenda.join()

    # Espera que todos os threads dos veículos sejam encerrados
    for veiculo in veiculos:
        veiculo.join()

    # Finaliza os threads dos pontos
    for ponto in pontos:
        ponto.running = False
    for ponto in pontos:
        ponto.join()

    # Gera o histórico final
    results = []
    for veiculo in veiculos:
        results.append(f"Veículo {veiculo.id}:")
        results.extend(veiculo.historico)
        results.append("")

    for encomenda in encomendas:
        results.append(
            f"Encomenda {encomenda.id} - Origem: {encomenda.origem}, Destino: {encomenda.destino}, "
            f"Carregada: {time.strftime('%H:%M:%S', time.localtime(encomenda.horario_carregado))}, Entregue: {time.strftime('%H:%M:%S', time.localtime(encomenda.horario_descarregado))}"
        )
    interface.display_results(results)  # Exibe o histórico final
    interface.update_status("Simulação concluída!")  # Atualiza o status final

# Execução do programa
if __name__ == "__main__":
    root = Tk() # Criação da Interface Gráfica
    app = Interface(root)  # Inicialização da Interface
    root.mainloop() # Inicia o loop principal da interface gráfica
 
