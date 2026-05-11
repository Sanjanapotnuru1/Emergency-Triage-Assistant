from llm_engine import analyze_patient

# ==========================================
# MAIN FUNCTION
# ==========================================

def main():

    print("\n===== Emergency Triage Assistant =====\n")

    # ======================================
    # USER INPUTS
    # ======================================

    name = input("Enter Patient Name: ")

    age = input("Enter Age: ")

    gender = input("Enter Gender: ")

    symptoms = input("Enter Symptoms: ")

    duration = input("Enter Duration of Symptoms: ")

    conditions = input(
        "Enter Existing Medical Conditions (Diabetes/Blood Pressure/Asthma/etc): "
    )

    # ======================================
    # OPTIONAL HEALTH DATA
    # ======================================

    sugar_level = "Not Provided"

    bp_level = "Not Provided"

    if "diabetes" in conditions.lower():

        sugar_level = input(
            "Enter Blood Sugar Level: "
        )

    if "blood pressure" in conditions.lower():

        bp_level = input(
            "Enter Blood Pressure Reading: "
        )

    pain_scale = input(
        "Enter Pain Level (1-10): "
    )

    # ======================================
    # PATIENT DATA
    # ======================================

    patient_data = {

        "name": name,

        "age": age,

        "gender": gender,

        "symptoms": symptoms,

        "duration": duration,

        "conditions": conditions,

        "sugar_level": sugar_level,

        "bp_level": bp_level,

        "pain_scale": pain_scale

    }

    # ======================================
    # AI ANALYSIS
    # ======================================

    print("\nAnalyzing symptoms using AI...\n")

    result = analyze_patient(patient_data)

    # ======================================
    # OUTPUT
    # ======================================

    print("\n===== AI TRIAGE ANALYSIS =====\n")

    print(result)

    print("\n================================\n")


# ==========================================
# RUN MAIN
# ==========================================

if __name__ == "__main__":

    main()