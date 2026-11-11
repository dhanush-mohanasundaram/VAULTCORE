# VAULTCORE Roadmap (V2)

## Postponed Features

| Feature | Reason | Priority |
|---------|--------|----------|
| Real payment gateway | Requires PCI compliance, external integration | High |
| Redis + background workers | For async tasks, email, rate limiting at scale | Medium |
| Email notifications | Requires SMTP integration, templates | Medium |
| Internal wallet | Requires double-entry ledger, audit | Medium |
| Double-entry ledger | Complex accounting, audit requirements | Low |
| Microservices | Monolith is sufficient for current scale | Low |
| AI recommendations | Not core to e-commerce | Low |
| Advanced analytics | Basic stats sufficient for MVP | Low |
| Real-time inventory updates | Polling sufficient for MVP | Low |

## Not Planned
- Java/Spring Boot stack — team is Python/TypeScript focused.
- Microservices architecture — adds operational complexity without current need.
