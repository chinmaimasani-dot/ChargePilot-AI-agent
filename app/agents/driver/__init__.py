"""Driver LangGraph workflow.

Composed from the shared framework (Member 4). The booking subworkflow
(collect details -> search slots -> propose -> explicit confirm) runs on the
shared confirmation machinery in `app.agents.shared.runtime`; Member 3's
booking tools slot in via the MCP manager with
`requires_confirmation=True` on `confirm_booking`.
"""
