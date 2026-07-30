def check_drug_interaction(drug1, drug2):

	interactions = {
		("aspirin", "ibuprofen"):
		"Increased risk of stomach bleeding.",
		("paracetamol", "alcohol"):
		"Risk of liver damage.",
	}

	key = (drug1.lower(), drug2.lower())
	reverse_key = (drug2.lower(), drug1.lower())

	if drug1.lower() == drug2.lower():
		return f"{drug1.title()} was provided twice. Please provide two different medicines to check interactions."

	return interactions.get(
		key,
		interactions.get(reverse_key, "No known interaction found."),
	)