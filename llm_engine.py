from groq import Groq
from prompts import TRIAGE_PROMPT
import streamlit as st
# ==========================================
# GROQ CLIENT
# =====================================
client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)
# ==========================================
# AI ANALYSIS FUNCTION
# ==========================================

def analyze_patient(data):

    # ======================================
    # HANDLE EMPTY OPTIONAL VALUES
    # ======================================

    sugar_level = data.get("sugar_level", "Not Provided")

    bp_level = data.get("bp_level", "Not Provided")

    pain_scale = data.get("pain_scale", "Not Provided")

    conditions = data.get("conditions", "None")

    # ======================================
    # FINAL PROMPT
    # ======================================

    final_prompt = TRIAGE_PROMPT.format(

        name=data["name"],

        age=data["age"],

        gender=data["gender"],

        symptoms=data["symptoms"],

        duration=data["duration"],

        conditions=conditions,

        sugar_level=sugar_level,

        bp_level=bp_level,

        pain_scale=pain_scale

    )

    # ======================================
    # GROQ API CALL
    # ======================================

    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[

            {
                "role": "system",

                "content": """
                You are a professional AI medical triage assistant.

                Your goals are:
                - Analyze symptoms safely
                - Detect urgency levels
                - Evaluate chronic conditions
                - Assess health risks
                - Provide medical guidance
                - Recommend emergency care if necessary

                Never provide dangerous or guaranteed diagnoses.

                Always include a professional disclaimer.
                """
            },

            {
                "role": "user",

                "content": final_prompt
            }

        ],

        temperature=0.4,

        max_tokens=1000,

        top_p=1

    )

    # ======================================
    # RETURN RESULT
    # ======================================

    result = response.choices[0].message.content

    return result
