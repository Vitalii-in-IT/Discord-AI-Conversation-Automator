# ai.py
import requests
import json
import logging

logger = logging.getLogger("BotLogger")

DEEPSEEK_KEY = "sk- Your API dipsika!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

def get_ai_answer(full_prompt):
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a Lineage 2 player. Communication takes place on Discord. Respond without repeating chat messages."},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1000
    }


    print("\n" + "!"*30 + " JSON in AI " + "!"*30)
    print(json.dumps(body, indent=4, ensure_ascii=False))
    print("!"*85 + "\n")




    try:
        logger.info("Sending a request to DeepSeek...")
        response = requests.post(url, json=body, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()
            
            answer = answer.replace('"', '').replace('«', '').replace('»', '')
            
            return answer
        else:
            logger.error(f"Error API DeepSeek: {response.status_code} - {response.text}")
            return ""
            
    except Exception as e:
        logger.error(f"Critical error in ai.py: {e}")
        return ""