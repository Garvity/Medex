import json

guidelines = [

{"type":"guideline","name":"Handwashing","section":"prevention","text":"Wash hands with soap and water for at least 20 seconds before eating, after using the restroom and after touching contaminated surfaces."},

{"type":"guideline","name":"Flu Prevention","section":"prevention","text":"Get vaccinated annually, avoid close contact with sick individuals and cover your mouth when coughing or sneezing."},

{"type":"guideline","name":"COVID-19 Prevention","section":"prevention","text":"Maintain good hygiene, wear masks in crowded places, stay home if sick and keep vaccinations up to date."},

{"type":"guideline","name":"Hypertension Prevention","section":"prevention","text":"Reduce salt intake, exercise regularly, maintain a healthy weight and limit alcohol consumption."},

{"type":"guideline","name":"Diabetes Lifestyle Management","section":"treatment","text":"Maintain a balanced diet, exercise regularly, monitor blood sugar levels and follow medical advice for medication."},

{"type":"guideline","name":"Heart Disease Prevention","section":"prevention","text":"Avoid smoking, maintain a healthy weight, exercise regularly and follow a balanced diet."},

{"type":"guideline","name":"Obesity Prevention","section":"prevention","text":"Follow a balanced diet, limit high-calorie foods and maintain regular physical activity."},

{"type":"guideline","name":"Malaria Prevention","section":"prevention","text":"Use mosquito nets, apply insect repellents and eliminate standing water around homes."},

{"type":"guideline","name":"Dengue Prevention","section":"prevention","text":"Remove stagnant water, use mosquito repellents and wear protective clothing."},

{"type":"guideline","name":"Tuberculosis Prevention","section":"prevention","text":"Ensure proper ventilation in living spaces and seek early medical evaluation for persistent cough."},

{"type":"guideline","name":"Healthy Diet","section":"nutrition","text":"Eat fruits, vegetables, whole grains and lean protein while limiting sugar and processed foods."},

{"type":"guideline","name":"Physical Activity","section":"lifestyle","text":"Engage in at least 150 minutes of moderate exercise per week such as walking or cycling."},

{"type":"guideline","name":"Smoking Cessation","section":"prevention","text":"Avoid tobacco products and seek counseling or nicotine replacement therapy if needed."},

{"type":"guideline","name":"Alcohol Consumption","section":"prevention","text":"Limit alcohol intake and avoid excessive drinking to reduce risk of liver disease."},

{"type":"guideline","name":"Vaccination","section":"prevention","text":"Follow recommended vaccination schedules to prevent infectious diseases."},

{"type":"guideline","name":"Mental Health Care","section":"lifestyle","text":"Maintain social connections, practice stress management and seek professional help when needed."},

{"type":"guideline","name":"Sleep Hygiene","section":"lifestyle","text":"Maintain a regular sleep schedule and ensure a quiet comfortable sleeping environment."},

{"type":"guideline","name":"Food Safety","section":"prevention","text":"Cook foods thoroughly, wash produce properly and avoid cross contamination during food preparation."},

{"type":"guideline","name":"Clean Water","section":"prevention","text":"Drink safe water and ensure proper sanitation to prevent waterborne diseases."},

{"type":"guideline","name":"Child Immunization","section":"prevention","text":"Follow national immunization schedules to protect children from infectious diseases."},

{"type":"guideline","name":"Asthma Management","section":"treatment","text":"Avoid triggers, use prescribed inhalers and follow medical treatment plans."},

{"type":"guideline","name":"Allergy Prevention","section":"prevention","text":"Identify allergens and reduce exposure to substances that trigger allergic reactions."},

{"type":"guideline","name":"Sun Protection","section":"prevention","text":"Use sunscreen, wear protective clothing and avoid prolonged sun exposure."},

{"type":"guideline","name":"Eye Health","section":"prevention","text":"Take breaks from screens and ensure proper lighting to protect vision."},

{"type":"guideline","name":"Dental Hygiene","section":"prevention","text":"Brush teeth twice daily and visit dentists regularly for oral health checkups."},

{"type":"guideline","name":"Stress Management","section":"lifestyle","text":"Practice relaxation techniques such as meditation, breathing exercises or yoga."},

{"type":"guideline","name":"Healthy Pregnancy","section":"treatment","text":"Attend prenatal checkups regularly and maintain a healthy diet during pregnancy."},

{"type":"guideline","name":"Balanced Nutrition","section":"nutrition","text":"Consume a variety of foods including vegetables, fruits, proteins and grains."},

{"type":"guideline","name":"Bone Health","section":"prevention","text":"Ensure adequate calcium and vitamin D intake and maintain physical activity."},

{"type":"guideline","name":"Kidney Health","section":"prevention","text":"Drink adequate water, limit salt intake and control blood pressure."},

{"type":"guideline","name":"Liver Health","section":"prevention","text":"Avoid excessive alcohol consumption and maintain healthy body weight."},

{"type":"guideline","name":"Cancer Screening","section":"prevention","text":"Undergo recommended screening tests such as mammograms or colonoscopies."},

{"type":"guideline","name":"Blood Pressure Monitoring","section":"treatment","text":"Check blood pressure regularly and follow medical advice if elevated."},

{"type":"guideline","name":"Healthy Aging","section":"lifestyle","text":"Maintain physical activity, balanced diet and social engagement."},

{"type":"guideline","name":"Cold Prevention","section":"prevention","text":"Practice good hygiene and avoid close contact with infected individuals."},

{"type":"guideline","name":"Heat Stroke Prevention","section":"prevention","text":"Stay hydrated and avoid prolonged exposure to extreme heat."},

{"type":"guideline","name":"Injury Prevention","section":"prevention","text":"Use protective equipment and follow safety guidelines during physical activities."},

{"type":"guideline","name":"Respiratory Health","section":"prevention","text":"Avoid air pollution exposure and maintain good indoor ventilation."},

{"type":"guideline","name":"Hydration","section":"nutrition","text":"Drink adequate water daily to maintain proper body function."},

{"type":"guideline","name":"Immunity Support","section":"nutrition","text":"Eat a nutrient rich diet including fruits vegetables and proteins."},

{"type":"guideline","name":"Healthy Weight","section":"lifestyle","text":"Maintain energy balance through diet and regular physical activity."},

{"type":"guideline","name":"Infection Control","section":"prevention","text":"Use proper hygiene practices and disinfect frequently touched surfaces."},

{"type":"guideline","name":"Travel Health","section":"prevention","text":"Follow vaccination requirements and practice food and water safety while traveling."},

{"type":"guideline","name":"Food Portion Control","section":"nutrition","text":"Eat moderate portions and avoid overeating to maintain healthy weight."},

{"type":"guideline","name":"Cholesterol Control","section":"prevention","text":"Reduce saturated fats and increase fiber intake to maintain healthy cholesterol levels."},

{"type":"guideline","name":"Physical Fitness","section":"lifestyle","text":"Incorporate aerobic exercise strength training and flexibility activities into weekly routine."},

{"type":"guideline","name":"Community Health Awareness","section":"prevention","text":"Promote vaccination hygiene and preventive healthcare practices in communities."},

{"type":"guideline","name":"Safe Medication Use","section":"treatment","text":"Follow prescription instructions carefully and avoid self medication without guidance."},

{"type":"guideline","name":"Post Illness Recovery","section":"treatment","text":"Ensure adequate rest hydration and gradual return to normal activity."}

]

with open("guideline_rag.json","w") as f:
    json.dump(guidelines,f,indent=2)

print("Guideline dataset created")
print("Total guidelines:",len(guidelines))