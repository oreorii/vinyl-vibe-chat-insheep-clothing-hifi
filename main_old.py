# main.py

import openai
import os
from my_web_scraper import fetch_all_articles, save_articles, load_articles, search_articles, fetch_article_content
from flask import Flask, render_template, request, session
from dotenv import load_dotenv
load_dotenv()

from embedchain import App
chat_bot_app = App()
bot_name="Jazz GPT"

app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = 'embedchain'
def load_app():
    # chat_bot_app.add("web_page", "https://nav.al/feedback")
    chat_bot_app.add("web_page", "https://nav.al/agi")

# Set your OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')  # Ensure this environment variable is set

    
def get_response(messages):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response.choices[0].message.content

def main():
    system_message = {
        "role": "system",
        "content": (
            "Your role is an assitant in summarize content about jazz and music"
            "You are an expert in HiFi jazz music, with a deep understanding of the genre's history, key artists, and technical aspects of high-fidelity audio. "
            "Whenever a question is asked, you will first search your knowledge base from web scrape of 'In Sheep's Clothing HiFi'."
            "You will search using search_articles(), and the response format after if search_results:, providing the user with the title, link, and summary of the article. "
            "If the user ask follow up of the question, you will search using fetch_article_content(), and use that context to asnwer the question"
            "If you don't find an answer, you will provide your own prior knowledge about the question, but state that you are not an expert in the topic."
            "If the users ask question irrelevant to music, you will respond with 'I'm sorry, we only discuss music today and I don't know the answer"
            "Ensure your responses are accurate, well-researched, and reflect the high-quality content found "
        )
    }
    messages = [system_message]

    welcome_message = (
        "Welcome! You reached this website because you have a good taste in audio.\n"
        "This website is built by a Hi-Fi and music enthusiast who believes in providing quality information about music culture.\n"
        "My answers will primarily be based on the content from https://insheepsclothinghifi.com, just their curated playlist is amazing, and the website provides quality information.\n"
        "What would you like to learn about music and HiFi today? Give me one keyword.\n\n"
    )

    print(f"Agent: {welcome_message}")

    articles = load_articles()  # Load the pre-fetched articles
    # articles are already pre-scraped 
    # if not articles:
    #     # Fetch and save articles if they are not pre-fetched
    #     base_url = "https://insheepsclothinghifi.com/category/interview/"
    #     articles = fetch_all_articles(base_url)
    #     save_articles(articles)
    #     print(f"Saved {len(articles)} articles to articles.json")

    # Prompt the user for the initial keyword
    keyword = input("User: ").strip()

    # Search the articles for relevant information
    search_results = search_articles(keyword, articles)

    if search_results:
        response = "Here are some articles I found relevant" 
        for i, result in enumerate(search_results, 1):
            article_content = fetch_article_content(result['link'])
            messages.append({"role": "system", "content": result['title'] + article_content})
            response += f"\n\n{i}. {result['title']}\nLink: {result['link']}\n\n"            
                       
        response += "Ask me anything about the topic, my answer will be primarily from the articles."
        
    else:
        response = f"No articles found with the keyword '{keyword}'."
        
    print(f"Agent: {response}")
    messages.append({"role": "assistant", "content": response})

    while True:
        user_input = input("User: ").strip()

        if user_input.lower() == 'exit':
            break

        # Add the user's message to the conversation history
        messages.append({"role": "user", "content": user_input})

        # Get the assistant's response
        assistant_response = get_response(messages)

        # Add the assistant's response to the conversation history
        messages.append({"role": "assistant", "content": assistant_response})

        # Print the assistant's response
        print(f"Agent: {assistant_response}")

messages = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get('message')
    messages.append({"role": "user", "content": user_input})

    # Get the assistant's response
    assistant_response = get_response(messages)

    # Add the assistant's response to the conversation history
    messages.append({"role": "assistant", "content": assistant_response})

    return jsonify({"response": assistant_response})
    
# if __name__ == "__main__":
#     main()
if __name__ == "__main__":
    app.run(host="0.0.0.0")
