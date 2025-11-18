import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import json 
import re 

# Carrega a chave de API
load_dotenv()

app = Flask(__name__)

# 1. CORS SIMPLES E ROBUSTO
# Isso permite que o Netlify (e qualquer um) acesse sua API sem bloqueios
CORS(app, resources={r"/*": {"origins": "*"}})

# Configura a API do Gemini
api_key = os.getenv('GEMINI_API_KEY')

# Configurações de segurança e modelo
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

generation_config = {
    "temperature": 0.7,
    "response_mime_type": "application/json",
}

# Se a chave não existir, não quebra o app na hora, mas avisa
if api_key:
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",  
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        print("--- Modelo Gemini carregado ---")
    except Exception as e:
        print(f"Erro ao carregar modelo: {e}")
else:
    print("--- AVISO: Chave de API não encontrada no .env ---")


# 2. NOVA ROTA DE TESTE (Para você ver no navegador)
@app.route('/', methods=['GET'])
def home():
    return "O Backend SIPDE está ONLINE e funcionando! 🚀"


# Rota Principal
@app.route('/gerar-plano', methods=['POST'])
def gerar_plano():
    # Proteção extra: Se a chave falhou
    if not api_key:
        return jsonify({"error": "Configuração do servidor incompleta (API Key faltando)."}), 500

    try:
        dados_cliente = request.get_json()
        if not dados_cliente:
            return jsonify({"error": "Nenhum dado recebido."}), 400
            
        print(f"Recebido pedido para: {dados_cliente.get('nome')}")

        prompt = f"""
            Você é um nutricionista esportivo e personal trainer de elite.
            Seu cliente forneceu os seguintes dados:

            == DADOS ==
            - Nome: {dados_cliente.get('nome')}
            - Idade: {dados_cliente.get('idade')} anos
            - Sexo: {dados_cliente.get('sexo')}
            - Objetivo: {dados_cliente.get('objetivo')}
            - Altura: {dados_cliente.get('alturaCm')} cm
            - Peso: {dados_cliente.get('pesoKg')} kg
            - IMC: {dados_cliente.get('imc')}
            - % Gordura: {dados_cliente.get('bodyFat')} % ({dados_cliente.get('metodo_calculo')})
            
            == PREFERÊNCIAS ==
            - Restrições: {dados_cliente.get('restricoes')}
            - Alergias: {dados_cliente.get('alergias')}
            - Não come: {dados_cliente.get('alimentos_odiados')}
            - Refeições/dia: {dados_cliente.get('refeicoes')}
            - Custo: {dados_cliente.get('custo_dieta')}

            == TREINO ==
            - Nível: {dados_cliente.get('nivel_treino')}
            - Local: {dados_cliente.get('local_treino')}
            - Frequência: {dados_cliente.get('dias_treino')}
            - Lesões: {dados_cliente.get('lesoes')}

            == TAREFA ==
            1. Gere dieta detalhada.
            2. Gere treino detalhado.
            3. Calcule macros totais (proteina, carbo, gordura, fibras).
            
            Responda APENAS em JSON:
            {{
              "dieta": "...",
              "macros": {{ "proteina_g": "..", "carboidrato_g": "..", "gordura_g": "..", "fibras_g": ".." }},
              "treino": "..."
            }}
        """

        # Timeout de 60s para não travar
        response = model.generate_content(prompt, request_options={"timeout": 60})
        
        # Limpeza do JSON
        json_string = response.text
        match = re.search(r'\{.*\}', json_string, re.DOTALL)
        if match:
            json_string = match.group(0)
        
        return jsonify(json.loads(json_string))
    
    except Exception as e:
        print(f"Erro no backend: {e}")
        # Retorna o erro como JSON para o frontend entender
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True)