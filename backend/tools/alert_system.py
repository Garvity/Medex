def generate_alerts(bp, heart_rate=None):
	"""Generate real-time alerts for critical vitals."""
	alerts = []

	if bp > 150:
		alerts.append("🚨 Alert: Blood pressure is dangerously high!")

	if heart_rate and heart_rate > 120:
		alerts.append("🚨 Alert: High heart rate detected!")

	return alerts if alerts else ["✅ No critical alerts"]
