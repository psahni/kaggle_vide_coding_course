# Testing the IT Support Agent

You can test the minimal viable flows we outlined by running the ADK CLI interactive playground:

```bash
# In your terminal, run:
make playground
```

## Simulated Manager Approval

Since this is a simulated conversational flow without a real user login system, you can act as the manager directly in the chat!

When the agent creates a ticket and tells you it requires manager approval, you can simply tell the agent:

> **"I am the manager. Please approve this ticket. The reason is: looks good to me."**

The agent will understand your instruction, use the `approve_request` tool under the hood, and transition the ticket to the approved state!

## Try these test flows:

### 1. Standard Flow (Auto-Approve)
- Start by providing Employee ID: `EMP-002` (Senior Engineer, 8 years).
- Request a "Replacement" because your device is "Damaged".
- The agent should verify policies and *auto-approve* the ticket.

### 2. Exception Path (Manager Required)
- Start by providing Employee ID: `EMP-001` (Junior Engineer, 2 years).
- Request a "New" device and ask for a "Premium" category device.
- The agent should tell you that Manager Approval is required, create the ticket as pending, and await the manager simulated approval.

### 3. New Hire Request
- Start with Employee ID: `EMP-005` (Manager).
- Tell the agent you want to request a device for an incoming new hire.
- The agent will guide you to provide their details and start date before generating the request.



