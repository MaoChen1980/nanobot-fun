[Subagent '{{ label }}' {{ status_text }}]

Task: {{ task }}
{% if duration_s %}Duration: {{ "%.1f"|format(duration_s) }}s
{% endif %}{% if tools_used %}Tools used: {{ tools_used }}
{% endif %}{% if iteration_count %}Iterations: {{ iteration_count }}
{% endif %}

Result:
{{ result }}

{% if status == "ok" %}
Summarize the result and process steps naturally for the user. Keep it brief (1-4 sentences). Do not mention technical details like "subagent" or task IDs.
{% else %}
This subagent task failed. The error details are shown in the result above. If the task should be retried (with adjusted approach if needed), you can re-spawn it. Do NOT mention "subagent" or task IDs to the user — just explain the situation naturally and, if appropriate, offer to retry.
{% endif %}
