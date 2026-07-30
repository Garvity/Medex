from html import escape


def medication_reminder_email(*, medicine: str, scheduled_time: str, frequency: str) -> tuple[str, str, str]:
    safe_medicine = escape(medicine)
    safe_time = escape(scheduled_time)
    recurrence = escape(frequency.replace("_", " ").title())
    subject = f"Medication reminder: take {medicine}"
    text = (
        f"Medication reminder\n\nTime to take: {medicine}\nScheduled time: {scheduled_time}\n"
        f"Recurrence: {recurrence}\n\nThis is an automated reminder from MedAssist AI."
    )
    html = f"""<div style="font-family:Arial,sans-serif;max-width:520px;color:#1f2937">
  <h2 style="color:#0f766e">Medication reminder</h2>
  <p>It is time to take your scheduled medication:</p>
  <p style="padding:16px;border:1px solid #ccfbf1;border-radius:8px;background:#f0fdfa;font-size:22px;font-weight:700;color:#0f766e">{safe_medicine}</p>
  <p>Scheduled time: <strong>{safe_time}</strong><br/>Recurrence: <strong>{recurrence}</strong></p>
  <hr style="border:0;border-top:1px solid #e5e7eb"/>
  <p style="font-size:12px;color:#6b7280">This is an automated reminder from MedAssist AI. General medical information only.</p>
</div>"""
    return subject, text, html
