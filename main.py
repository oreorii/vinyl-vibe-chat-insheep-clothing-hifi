from flask import Flask, request, jsonify, render_template
import openai
import os
from functions import load_articles, extract_music_keywords, append_relevant_articles, flatten_keywords

app = Flask(__name__)

articles = load_articles()

# Set your OpenAI API key
openai.api_key = os.environ.get(
    'OPENAI_API_KEY')  # Ensure this environment variable is set

system_message = {
    "role":
    "system",
    "content":
    ("You are an expert in HiFi and jazz music, with a deep understanding of the genre's history, key artists, and technical aspects of hi-fi audio system, like speaker,turnable,amplifiers. "
     "Your knowledge is particularly grounded in the interviews and articles found on the website 'In Sheep's Clothing HiFi'. "
     "Provide detailed and insightful responses to questions about HiFi jazz music."
     "If you found relevant context in the context, citing specific articles from the website with links when relevant. "
     "Ensure your responses are accurate, well-researched, and reflect the high-quality content found on 'In Sheep's Clothing HiFi'. "
     "If you don't know the answer, it's okay to say that you don't know."
     "If you are asked about question irrelevant to music, politely decline to answer."
     "Be sure to imit the response to 300g words, unless user specifically ask for long answers"
     )
}
messages = [system_message]


def get_response(messages):
    response = openai.chat.completions.create(model="gpt-4o",
                                              messages=messages)
    return response.choices[0].message.content


@app.route('/')
def index():
    return render_template('index.html', bot_name="Jazz Assistant", chats=[])


@app.route('/chat', methods=['POST'])
def chat():
    print(f"LOG: POSTED CHAT with {request.json.get('message')}")
    user_input = request.json.get('message')
    messages.append({"role": "user", "content": user_input})

    # Extract keywords and flatten them
    keywords = extract_music_keywords(user_input)
    flattened_keywords = flatten_keywords(keywords)

    # Temporarily append relevant articles to the messages
    original_message_length = len(messages)
    print(f"LOG: Original message length: {original_message_length}")
    messages_with_articles = messages.copy()
    append_relevant_articles(flattened_keywords, articles,
                             messages_with_articles)

    print(
        f"LOG: acticles added as context: {len(messages_with_articles)-original_message_length}"
    )

    # Get the assistant's response with the temporary context
    assistant_response = get_response(messages_with_articles)

    # Add the assistant's response to the original conversation history
    messages.append({"role": "assistant", "content": assistant_response})
    print(f"LOG: assistant_response: {assistant_response}")

    return jsonify({"response": assistant_response})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
