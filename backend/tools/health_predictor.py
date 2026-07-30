def predict_health_risk(age, bp):
	"""Return a simple risk tier based on age and blood pressure."""
	score = 0

	if age > 50:
		score += 1

	if bp > 140:
		score += 2

	if bp > 160:
		score += 3

	if score >= 4:
		return "⚠️ High risk: Severe hypertension"

	if score >= 2:
		return "⚠️ Moderate risk: Hypertension"

	if age > 50 and bp > 130:
		return "⚠️ Risk due to age + BP"

	return "✅ Low risk"
