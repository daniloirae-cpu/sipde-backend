import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import json 
import re 

# Carrega a chave de API do arquivo .env
load_dotenv()

# Configura o app Flask
app = Flask(__name__)

# CORS Básico
CORS(app) 

# ***** CORS NUCLEAR (A CORREÇÃO) *****
# Isso força o cabeçalho em TODAS as respostas, sem exceção
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
# *************************************

# Configura a API do Gemini
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("--- ERRO FATAL: A chave GEMINI_API_KEY não foi encontrada! ---")
    # Em produção, não queremos derrubar o app, apenas logar
    # exit() 

if api_key:
    genai.configure(api_key=api_key)

# Configurações de segurança
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Configuração do modelo
generation_config = {
    "temperature": 0.7,
    "response_mime_type": "application/json",
}

# Define o tempo limite para a chamada da API
request_options = {"timeout": 60} 

# Carrega o modelo
try:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",  
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    print("--- Modelo da IA (Python/Flask) carregado com sucesso ---")
except Exception as e:
    print(f"Erro ao carregar modelo: {e}")


# Rota da API
@app.route('/gerar-plano', methods=['POST'])
def gerar_plano():
    try:
        dados_cliente = request.get_json()
        print(f"Recebido pedido para gerar plano: {dados_cliente.get('nome')}")

        # Prompt
        prompt = f"""
            Você é um nutricionista esportivo e personal trainer de elite.
            Seu cliente forneceu os seguintes dados:

            == DADOS BÁSICOS ==
            - Nome: {dados_cliente['nome']}
            - Idade: {dados_cliente['idade']} anos
            - Sexo: {dados_cliente['sexo']}
            - Objetivo Principal: {dados_cliente['objetivo'].replace("_", " ")}

            == AVALIAÇÃO CORPORAL ==
            - Altura: {dados_cliente['alturaCm']} cm
            - Peso: {dados_cliente['pesoKg']} kg
            - IMC: {dados_cliente['imc']:.2f}
            - Percentual de Gordura (%GC) Estimado: {dados_cliente['bodyFat']:.2f} % 
            - (Método de Cálculo Usado: {dados_cliente['metodo_calculo']})

            == PERFIL ALIMENTAR ==
            - Restrições: {dados_cliente['restricoes']}
            - Alergias: {dados_cliente['alergias']}
            - Alimentos que NÃO come: {dados_cliente['alimentos_odiados']}
            - Número de Refeições Desejadas: {dados_cliente['refeicoes']}
            - Custo da Dieta: {dados_cliente.get('custo_dieta', 'Padrão')}

            == PERFIL DE TREINO ==
            - Nível de Experiência: {dados_cliente['nivel_treino']}
            - Local de Treino: {dados_cliente['local_treino']}
            - Dias por Semana: {dados_cliente['dias_treino']}
            - Lesões ou Limitações: {dados_cliente['lesoes']}

            == SUA TAREFA ==
            1. Gere um plano de dieta detalhado (dividido pelo número de refeições pedido e respeitando o custo).
            2. Gere um plano de treino detalhado (dividido pelos dias disponíveis, adequado ao local e nível).
            3. Calcule os macronutrientes totais aproximados da dieta (proteína, carboidrato, gordura, fibras) em gramas.
            
            Responda ESTRITAMENTE no seguinte formato JSON:
            {{
              "dieta": "...",
              "macros": {{
                "proteina_g": "...",
                "carboidrato_g": "...",
                "gordura_g": "...",
                "fibras_g": "..."
              }},
              "treino": "..."
            }}
        """

        # 6. Chamar a IA
        response = model.generate_content(
            prompt,
            request_options=request_options
        )
        
        print("Resposta da IA recebida.")
        
        # 7. Limpar e enviar o JSON
        json_string = response.text
        
        try:
            match = re.search(r'\{.*\}', json_string, re.DOTALL)
            if match:
                json_string = match.group(0)
            else:
                json_start = json_string.find('{')
                json_end = json_string.rfind('}')
                if json_start != -1 and json_end != -1:
                    json_string = json_string[json_start:json_end+1]

            dados_plano = json.loads(json_string)
            return jsonify(dados_plano)
            
        except json.JSONDecodeError as e:
            print(f"--- ERRO: IA retornou um JSON inválido ---")
            return jsonify({"error": "A IA retornou uma resposta malformada."}), 500
    
    except Exception as e:
        print(f"Erro ao gerar plano: {e}")
        return jsonify({"error": f"Falha ao gerar o plano: {e}"}), 500

# Iniciar o Servidor
if __name__ == '__main__':
    app.run(port=3000, debug=True)