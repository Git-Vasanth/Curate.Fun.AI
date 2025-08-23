import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY not found in environment variables in ai.py.")
    print("Please ensure your .env file is correctly configured and loaded.")

llm_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def get_ai_response(user_query: str) -> str:
    """
    Generates an AI response using a 'React-style' prompt engineering technique,
    where the LLM performs internal reasoning before producing the final answer.
    RAG functionality is completely removed.
    """
    print(f"\n--- Agentic (React-Style) Process Started for query: '{user_query}' ---")


    # --- React-Style Prompting ---
    # The prompt guides the LLM to think step-by-step
    prompt_content = f"""
    Your name is Kara , a Representative , helpful and informative AI assistant for Curate.Fun.
    Your task is to answer the user's question. Follow a structured thought process to derive your final answer.
    You only have access to your general knowledge. There is no external knowledge base (RAG) or Internet Web Search available.

    Here's your thought process for responding:

    Thought: Analyze the user's question. Consider if this question would typically require specific external information (like from a knowledge base). Even though no RAG is available, acknowledge this and decide on the best approach using only general knowledge.

    Action: State whether this question *would have hypothetically* benefited from a RAG lookup (e.g., "Consider_RAG_Hypothetically" if it's a specific factual query) or if it's purely Needs internet (Ex consider_internet_web_search) or if it's purely general knowledge ("Answer_Directly_General_Knowledge").

    Observation: Based on the Action, summarize that since RAG is not available, you will proceed to answer using only your general knowledge. If the question is truly unanswerable from general knowledge and would only come from a specific knowledge base, state that you cannot provide information on that topic.

    Final Answer: Provide a concise and helpful answer to the user's question based *only* on your general knowledge. If you cannot answer, politely state so.

    User's question: {user_query}


    """

    try:
        print("Sending React-style prompt to LLM for reasoning and answer generation...")
        completion = llm_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Curate.Fun Agentic (React-Style) Chatbot",
            },
            extra_body={},
            model="deepseek/deepseek-chat-v3-0324:free", # Your chosen LLM
            messages=[
                {
                    "role": "user",
                    "content": prompt_content
                }
            ],
            temperature=0.6, # Keep low for structured reasoning
            max_tokens=600 # Limit the response length
        )

        ai_response_content = completion.choices[0].message.content
        print(f"Received AI response:\n{ai_response_content}")
        
        # Extract the "Final Answer" part if the LLM followed the structure
        final_answer_tag = "Final Answer:"
        if final_answer_tag in ai_response_content:
            extracted_content = ai_response_content.split(final_answer_tag, 1)[1].strip()
            # **FIX: Remove any leading markdown bolding characters from the extracted content**
            while extracted_content.startswith('**'):
                extracted_content = extracted_content[2:].strip() # Remove '**' and re-strip
            return extracted_content
        else:
            return ai_response_content # Return full content if tag not found

    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return "I'm sorry, I couldn't get a response from the AI at the moment. Please try again later."