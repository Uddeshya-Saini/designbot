import streamlit as st
import openai
import os
import requests
from airtable import Airtable
import json

# --- Configuration (These will be Railway environment variables) ---
openai.api_key = os.environ["OPENAI_API_KEY"]
AMAZON_API_KEY = os.environ["AMAZON_API_KEY"]
AMAZON_ASSOCIATE_TAG = os.environ["AMAZON_ASSOCIATE_TAG"]
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]

# --- Connect to Airtable product database ---
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# --- System prompt (the bot's "persona") ---
SYSTEM_PROMPT = """
You are Alex, a virtual interior design assistant. You help users design rooms on a budget.
Rules:
- Ask about: room type, dimensions, style (boho/modern/industrial/mid-century/minimalist), budget, existing furniture.
- Suggest 3-5 specific products when appropriate.
- Always explain WHY a suggestion works (color, proportion, function).
- Include measurement warnings: "This sofa is 84 inches – measure your wall first."
- Never recommend structural changes (walls, plumbing).
- Be warm, practical, and confident.
"""

# --- Helper: Search Airtable for products ---
def search_products(style=None, category=None, max_price=None, room=None):
    formula_parts = []
    if style:
        formula_parts.append(f"{{style}} = '{style}'")
    if category:
        formula_parts.append(f"{{category}} = '{category}'")
    if room:
        formula_parts.append(f"{{room}} = '{room}'")
    
    formula = " AND(".join(formula_parts) + ")" if formula_parts else None
    
    try:
        records = airtable.get_all(formula=formula, max_records=10)
        return [{"name": r["fields"]["name"], 
                 "price": r["fields"].get("price", "N/A"),
                 "image": r["fields"].get("image_url", ""),
                 "link": r["fields"].get("affiliate_link", ""),
                 "style": r["fields"].get("style", "")} for r in records]
    except:
        return []

# --- Helper: Search Amazon PAAPI (live products) ---
def search_amazon(query, max_price=None):
    # This is a placeholder – Amazon PAAPI requires specific signature logic
    # I'll provide the full implementation separately
    return []

# --- Streamlit UI ---
st.set_page_config(page_title="DesignBuddy", page_icon="🏠")
st.title("🏠 DesignBuddy – Your AI Interior Designer")
st.caption("Tell me about your room. I'll suggest specific products and layouts.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Example: 'I have a 12x14 living room, grey walls, boho style, £500 budget'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Call OpenAI
    with st.chat_message("assistant"):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Optional: Show product suggestions from Airtable
        if "sofa" in prompt.lower() or "couch" in prompt.lower():
            products = search_products(category="sofa", max_price=500)
            if products:
                st.subheader("🛋️ Sofas in your budget:")
                for p in products[:3]:
                    st.markdown(f"- **{p['name']}** – £{p['price']}  \n  [View on Amazon]({p['link']})")