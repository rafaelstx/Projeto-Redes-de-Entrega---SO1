# 🏢 Simulação de Logística com Threads em Python
Rafael Teixeira e Luan Diniz

Este projeto implementa uma simulação de logística utilizando threads em Python. O objetivo é modelar a interação entre encomendas, veículos e pontos de redistribuição em um sistema logístico, onde veículos transportam encomendas entre diferentes pontos, seguindo determinadas regras e restrições.


## Índice
- [Descrição](#descrição)
- [Funcionalidades](#funcionalidades)
- [Requisitos do Sistema](#requisitos-do-sistema)
- [Instalação](#instalação)
- [Uso](#uso)
- [Parâmetros da Simulação](#parâmetros-da-simulação)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Estrutura do Código](#estrutura-do-código)
- [Notas Importantes](#notas-importantes)
- [Exemplo de Uso](#exemplo-de-uso)

## 💬​Descrição

A simulação envolve os seguintes componentes principais:

- **Encomendas**: Representadas por threads, têm origem e destino e esperam em filas nos pontos de redistribuição até serem coletadas por veículos.
- **Veículos**: Também representados por threads, circulam entre os pontos, coletando e entregando encomendas.
- **Pontos de Redistribuição**: Locais onde as encomendas aguardam para serem coletadas e para onde os veículos se dirigem.
- **Capacidade de Carga**: A capacidade que cada veículo tem para carregar as encomendas.

A interface gráfica desenvolvida com **Tkinter** permite ao usuário inserir os parâmetros da simulação, acompanhar o status dos veículos e dos pontos e visualizar o histórico final das operações.

## 🎮Funcionalidades

- Interface gráfica para entrada de parâmetros e acompanhamento em tempo real.
- Geração de arquivos de rastro para cada encomenda, contendo detalhes do trajeto.
- Controle de concorrência utilizando threads e locks para sincronização.
- Validação dos parâmetros para garantir condições específicas (e.g., \(P > A > C\)).

## 📄​Requisitos do Sistema

- Python 3.x
- Biblioteca Tkinter (normalmente já incluída nas instalações padrão do Python)
- Sistema operacional compatível com Python (Windows, macOS, Linux)

## 🛠Instalação

1. Clone o repositório ou baixe o código fonte:
  - git clone https://github.com/rafaelstx/Projeto-Redes-de-Entrega---SO1.git
  - cd seu_repositorio
  - python simulacao_logistica.py

## ▶​Uso

### Entrada de Parâmetros

Ao executar o programa, a interface gráfica será exibida. Insira os seguintes parâmetros:

- **Número de pontos de redistribuição (S):** Inteiro positivo.
- **Número de veículos (C):** Inteiro positivo.
- **Capacidade de carga de cada veículo (A):** Inteiro positivo maior que `C`.
- **Número total de encomendas (P):** Inteiro positivo maior que `A`.

> **Importante:** As condições `P > A > C` devem ser satisfeitas para o correto funcionamento da simulação.

---

### Iniciar Simulação

Clique no botão **"Iniciar Simulação"** para começar.

---

### Acompanhamento

- **Status dos Veículos:** A interface exibirá o status de cada veículo, incluindo o ponto atual e as encomendas carregadas.
- **Status dos Pontos:** A interface exibirá o status de cada ponto de redistribuição, mostrando as encomendas armazenadas.
- **Histórico Final:** Ao término da simulação, um histórico detalhado das operações será mostrado na área de histórico.

---

### Arquivos de Rastro

- Os arquivos de rastro para cada encomenda serão gerados na pasta `rastros`, contendo informações detalhadas sobre o trajeto da encomenda.

---

## 📈​Parâmetros da Simulação

- **S (Número de Pontos de Redistribuição):**  
  Representa a quantidade de pontos onde as encomendas podem ser coletadas ou entregues.

- **C (Número de Veículos):**  
  Quantidade de veículos que estarão circulando entre os pontos.

- **A (Capacidade de Carga de Cada Veículo):**  
  Número máximo de encomendas que um veículo pode transportar simultaneamente.

- **P (Número Total de Encomendas):**  
  Quantidade total de encomendas que serão geradas na simulação.

---

## 🗂​Estrutura do Projeto

```plaintext
simulacao-logistica/
├── src/
│   ├── simulacao_logistica.py    # Código principal do projeto
├── rastros
├── README.md                     # Documentação do projeto
├── .gitignore                    # Arquivos ignorados pelo Git
└── LICENSE                       # Licença do projeto
```

---

## 📚​Estrutura do Código

### Classes Principais

- **Encomenda:**  
  Representa uma encomenda que será transportada. Cada encomenda é um thread que espera ser coletada e entregue.

- **Veículo:**  
  Representa um veículo que transporta encomendas entre os pontos. Também é implementado como um thread.

- **Ponto:**  
  Representa um ponto de redistribuição, com uma fila de encomendas aguardando coleta.

- **Interface:**  
  Responsável pela interface gráfica com o usuário, construída com `Tkinter`.

---


### Sincronização

- Utiliza `locks` (`threading.Lock`) para controlar o acesso aos pontos e evitar condições de corrida.
- Os veículos tentam adquirir o lock de um ponto antes de carregar ou descarregar encomendas. Se não conseguirem, prosseguem para o próximo ponto.
- Utiliza `semaforos` (`semaphore`) para controlar a capacidade máxima de carga de cada veículo.
- Os semáforos ajudam a evitar conflitos e violações de lógica ao lidar com a capacidade.

---

### Geração de Arquivos de Rastro

- Os arquivos são gerados na pasta `rastros`, que é limpa e recriada a cada execução para evitar conflitos.
- Cada arquivo contém informações sobre a encomenda, incluindo horários de criação, carregamento e entrega.

---

## 🗒Notas Importantes

### Deleção da Pasta `rastros`

- A pasta `rastros` é deletada e recriada no início de cada simulação.  
  Certifique-se de que ela não contenha arquivos importantes antes de iniciar.

---

### Condições para os Parâmetros

- É fundamental que os parâmetros inseridos atendam às condições `P > A > C` para garantir que:
  - A simulação funcione corretamente.
  - Todos os veículos trabalhem como esperado.

---

### Execução em Sistemas Diferentes

- O código foi escrito para **Python 3.x**. Certifique-se de estar utilizando uma versão compatível.
- A biblioteca **Tkinter** é necessária para a interface gráfica.  
  Caso encontre problemas, verifique se o Tkinter está instalado corretamente em seu sistema.

---

## ​​🏃Exemplo de Uso

### Entrada de Parâmetros

- **S:** 5  
- **C:** 2  
- **A:** 5  
- **P:** 15  

---

### Iniciando a Simulação

1. Após inserir os valores acima, clique no botão **"Iniciar Simulação"**.

---

### Acompanhamento

- **Status dos Veículos:**  
  Os veículos iniciarão suas rotas, carregando e entregando encomendas.  
  O status dos veículos será atualizado em tempo real na interface gráfica.

- **Status dos Pontos:**  
  Os pontos serão iniciados com as encomendas, que serão distribuidas aleatoriamente.  
  O status dos pontos será atualizado em tempo real na interface gráfica, mudando sempre que um veículo pegar uma das encomendas 
  presentes no ponto.

---

### Resultados

- **Histórico Final:**  
  Ao final da simulação, o histórico detalhado será exibido na interface.

- **Arquivos de Rastro:**  
  Os arquivos de rastro estarão disponíveis na pasta `rastros`.
