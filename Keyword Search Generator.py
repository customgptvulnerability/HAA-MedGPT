############################################################################################################################

########################################## Keywords Generator ###############################

############################################################################################################################

medical_specialties = [
    "cardiology", "neurology", "oncology", "pediatrics", "dermatology", "psychiatry",
    "radiology", "anesthesiology", "gastroenterology", "endocrinology", "hematology",
    "nephrology", "rheumatology", "urology", "pulmonology", "ophthalmology", "otolaryngology",
    "orthopedics", "geriatrics", "immunology", "infectious disease", "allergy", "pathology",
    "surgery", "emergency medicine", "family medicine", "internal medicine", "nuclear medicine",
    "occupational medicine", "pain management", "palliative care", "preventive medicine",
    "rehabilitation", "sports medicine", "toxicology", "transplant surgery", "vascular surgery",
    "sleep medicine", "genetics", "critical care", "hospital medicine"
]

healthcare_roles = [
    "doctor", "nurse", "therapist", "surgeon", "physician", "pharmacist", "nutritionist",
    "psychologist", "psychiatrist", "radiologist", "anesthetist", "technician", "paramedic",
    "caregiver", "midwife", "dentist", "optometrist", "chiropractor", "podiatrist",
    "speech therapist", "occupational therapist", "physiotherapist", "social worker",
    "medical assistant", "clinical researcher", "genetic counselor"
]

health_conditions = [
    "diabetes", "hypertension", "asthma", "cancer", "depression", "anxiety", "arthritis",
    "obesity", "stroke", "heart disease", "COPD", "Alzheimer's", "Parkinson's", "epilepsy",
    "HIV", "AIDS", "COVID-19", "influenza", "migraine", "osteoporosis", "autism",
    "bipolar disorder", "schizophrenia", "eczema", "psoriasis", "IBS", "IBD", "lupus",
    "multiple sclerosis", "chronic pain", "sleep apnea"
]

healthcare_tasks = [
    "diagnosis", "treatment", "monitoring", "screening", "consultation", "therapy",
    "rehabilitation", "surgery", "vaccination", "immunization", "prescription", "counseling",
    "triage", "checkup", "follow-up", "telemedicine", "telehealth", "home care", "emergency care",
    "intensive care", "palliative care", "preventive care", "mental health support",
    "nutrition counseling", "weight management", "smoking cessation", "physical therapy",
    "occupational therapy", "speech therapy", "genetic testing", "laboratory testing",
    "imaging services", "radiology services", "pharmacy services"
]

healthcare_terms = [
    "healthcare", "medical", "medicine", "clinical", "telemedicine", "telehealth", "mHealth",
    "eHealth", "EHR", "EMR", "health informatics", "public health", "primary care",
    "secondary care", "tertiary care", "quaternary care", "health insurance", "medical billing",
    "medical coding", "healthcare administration", "healthcare management", "patient care",
    "patient safety", "health promotion", "disease prevention", "health education",
    "health literacy", "health policy", "health economics", "health disparities",
    "global health", "community health", "occupational health", "environmental health",
    "behavioral health", "mental health", "nutrition", "dietary", "fitness", "wellness",
    "alternative medicine", "complementary medicine", "integrative medicine", "functional medicine"
]

#------------------- Combine all individual words into a set (to ensure uniqueness) ------------------------------------
all_keywords = set(
    medical_specialties +
    healthcare_roles +
    health_conditions +
    healthcare_tasks +
    healthcare_terms
)

#--------------- Save to file
file_path = "healthcare_gpt_search_keywords_individual_only.txt"
with open(file_path, "w", encoding="utf-8") as f:
    for keyword in sorted(all_keywords):
        f.write(keyword + "\n")

print(f"{len(all_keywords)} individual keywords saved to: {file_path}")