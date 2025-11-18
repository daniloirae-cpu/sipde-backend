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
CORS(app, resources={r"/*": {"origins": "*"}})

# Configura a API do Gemini
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("--- ERRO FATAL: A chave GEMINI_API_KEY não foi encontrada! ---")
    exit()

genai.configure(api_key=api_key)

# Configurações de segurança
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Configuração do modelo (pedindo JSON)
generation_config = {
    "temperature": 0.7,
    "response_mime_type": "application/json",
}

# Define o tempo limite para a chamada da API
request_options = {"timeout": 60} 

# Carrega o modelo (Usando a sugestão do seu irmão)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",  
    generation_config=generation_config,
    safety_settings=safety_settings
)

print("--- Modelo da IA (Python/Flask) carregado com sucesso ---")


# Rota da API
@app.route('/gerar-plano', methods=['POST'])
def gerar_plano():
    try:
        dados_cliente = request.get_json()
        print(f"Recebido pedido para gerar plano: {dados_cliente.get('nome')}")

        # ***** PROMPT FINAL ATUALIZADO *****
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
            - Custo da Dieta: {dados_cliente['custo_dieta']}

            == PERFIL DE TREINO ==
            - Nível de Experiência: {dados_cliente['nivel_treino']}
            - Local de Treino: {dados_cliente['local_treino']}
            - Dias por Semana: {dados_cliente['dias_treino']}
            - Lesões ou Limitações: {dados_cliente['lesoes']}

            == SUA TAREFA ==
            1. Gere um plano de dieta detalhado (dividido pelo número de refeições pedido e respeitando o custo).
            2. Gere um plano de treino detalhado (dividido pelos dias disponíveis, adequado ao local e nível).
            3. Calcule os macronutrientes totais aproximados da dieta (proteína, carboidrato, gordura, fibras) em gramas.
            
            Responda ESTRITAMENTE no seguinte formato JSON, sem nenhum texto antes ou depois:
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

        # 6. Chamar a IA (AGORA COM O TIMEOUT)
        response = model.generate_content(
            prompt,
            request_options=request_options # <-- Aplica o timeout de 60s
        )
        
        print("Resposta da IA recebida.")
        
        # 7. Limpar e enviar o JSON (A CORREÇÃO PARA O ERRO DE SINTAXE)
        json_string = response.text
        
        try:
            # Tenta limpar o JSON (caso a IA adicione "```json")
            match = re.search(r'\{.*\}', json_string, re.DOTALL)
            if match:
                json_string = match.group(0)
            else:
                json_start = json_string.find('{')
                json_end = json_string.rfind('}')
                if json_start != -1 and json_end != -1:
                    json_string = json_string[json_start:json_end+1]

            # Converte a STRING JSON em um DICIONÁRIO PYTHON
            dados_plano = json.loads(json_string)
            
            # Envia o DICIONÁRIO PYTHON como uma RESPOSTA JSON de verdade
            return jsonify(dados_plano)
            
        except json.JSONDecodeError as e:
            print(f"--- ERRO: IA retornou um JSON inválido ---")
            print(f"Erro: {e}")
            print(f"Resposta bruta da IA: {json_string}")
            return jsonify({{"error": "A IA retornou uma resposta malformada."}}), 500
    
    except Exception as e:
        print(f"Erro ao gerar plano: {e}")
        return jsonify({{"error": f"Falha ao gerar o plano: {e}"}}), 500

# Iniciar o Servidor
if __name__ == '__main__':
    app.run(port=3000, debug=True)