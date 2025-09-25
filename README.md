# M-Overlay

Overlay leve e personalizável para **iRacing**, desenvolvido em **Python**, inspirado em ferramentas como iOverlay, RaceLab e Kapps.  
O objetivo do projeto é fornecer informações essenciais de corrida em tempo real sem exigir muito do hardware, tornando-se ideal para quem não possui PCs muito potentes.

---

## 🚀 Funcionalidades

- Exibição de standings (posição dos pilotos em tempo real).  
- Layout personalizável via arquivos JSON (`config.json` e `overlay_layout.json`).  
- Suporte a múltiplas camadas visuais.  
- Ferramentas de debug para integração com o iRacing (`debug_iracing.py`).  

Em versões futuras:  
- Integração direta com a API do iRacing para dados de telemetria.  
- Adição de módulos como relative, delta, fuel, etc.  
- Sistema de **drag & drop** com salvamento automático de posição.  

---

## 📂 Estrutura do Projeto

2. Instalar dependências do projeto

No seu repositório você tem o arquivo requirements.txt. Esse arquivo lista tudo que o projeto precisa.
Para instalar:

Passo 1 – Criar ambiente virtual (opcional, mas recomendado):

python -m venv .venv


Ativar:

Windows PowerShell:

.venv\Scripts\Activate


Linux/Mac:

source .venv/bin/activate

Passo 2 – Instalar dependências:
pip install -r requirements.txt

3. Rodar o projeto

Depois que as dependências estiverem instaladas, você já pode rodar:

Teste de integração com iRacing:
python debug_iracing.py

Rodar o overlay principal:

Se o arquivo de entrada for src/main.py:

python src/main.py