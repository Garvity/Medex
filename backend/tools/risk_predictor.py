def predict_risk(age, blood_pressure):

	if blood_pressure > 150:
		return f"High risk: Age {age} with blood pressure {blood_pressure}. Blood pressure is dangerously high."

	if blood_pressure > 130:
		return f"Moderate risk: Age {age} with blood pressure {blood_pressure}. Monitor blood pressure."

	return f"Normal blood pressure range for this simple check: Age {age}, blood pressure {blood_pressure}."