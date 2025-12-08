#################################################################################################################################
#--------------------------------------- This counts the number of GPTs with Actions capability --------------------------------#
#################################################################################################################################

import json
from collections import Counter
import pandas as pd

input_file = r"C:\Users\XXXXXXX\Healthcare GPT Assessment\gpt_metadata_output_MedLLM.json"
json_output_file = r"C:\Users\XXXXXXXXXXXXXXX\Healthcare GPT Assessment\gpt_metadata_output_MedLLM_actions.json"
excel_output_file = r"C:\Users\XXXXXXXXXXXXXXXXXXXXXXXXXXX\Healthcare GPT Assessment\gpt_metadata_output_MedLLM_actions.xlsx"

with open(input_file, 'r', encoding='utf-8') as f:
    gpts = json.load(f)

target_capabilities = {
    "Web Search",
    "DALL·E Images",
    "Code Interpreter & Data Analysis",
    "Actions\nRetrieves or takes actions outside of ChatGPT",
    "4o Image Generation"
}

capability_count = Counter()
combinations_count = Counter()
actions_retrieves_gpts = []
no_capability_count = 0

for gpt in gpts:
    caps = gpt.get("capabilities", [])
    if not caps:
        no_capability_count += 1
        continue  # skip to next GPT

    caps_set = set(caps)
    matched = caps_set.intersection(target_capabilities)

    for cap in matched:
        capability_count[cap] += 1

    combinations_count[len(matched)] += 1

    if "Actions\nRetrieves or takes actions outside of ChatGPT" in caps_set:
        actions_retrieves_gpts.append(gpt)

print("Capability Counts:")
for cap in target_capabilities:
    print(f"  {cap}: {capability_count[cap]}")

print("\nNumber of GPTs by number of matched capabilities:")
for i in range(1, 6):
    print(f"  GPTs with {i} capability(ies): {combinations_count[i]}")

print(f"\nGPTs with no capabilities: {no_capability_count}")

with open(json_output_file, 'w', encoding='utf-8') as out_f:
    json.dump(actions_retrieves_gpts, out_f, indent=2)

df = pd.DataFrame(actions_retrieves_gpts)
df.to_excel(excel_output_file, index=False)

print(f"\nSaved {len(actions_retrieves_gpts)} GPTs with 'Actions...' capability to:\n- JSON: {json_output_file}\n- Excel: {excel_output_file}")