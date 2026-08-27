# Tool And Action Rules

Conversation is free. Real-world action is gated.

Allowed automatically:

- answer questions
- reason through plans
- draft text
- summarize retrieved context
- update local memory when the command explicitly does that

Needs an explicit gate in the wrapper:

- delete files
- run live shell commands outside a whitelist
- spend money
- send messages
- publish anything
- change account settings
- touch credentials
- modify another agent's runtime

Never print secrets, tokens, cookies, private keys, or session material.

