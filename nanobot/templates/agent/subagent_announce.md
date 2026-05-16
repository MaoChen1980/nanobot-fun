[Subagent '{{ label }}' {{ status_text }}]

Task: {{ task }}
{% if duration_s %}Duration: {{ "%.1f"|format(duration_s) }}s{% endif %}
{% if tools_used %}Tools used: {{ tools_used }}{% endif %}
{% if iteration_count %}Iterations: {{ iteration_count }}{% endif %}

Result:
{{ result }}

Summarize the result and process steps naturally for the user. Keep it brief (1-4 sentences). Do not mention technical details like "subagent" or task IDs.
