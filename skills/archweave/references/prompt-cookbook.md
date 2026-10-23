# Prompt cookbook

Worked prompts for the diagrams architecture teams ask for most. Each one names the diagram type the router will pick, the facts the vocabulary cannot know, and what a good result contains. Copy, edit the facts, and send. The sample vocabulary ships with a fictional "Example Corporation"; replace it before relying on component names.

How to phrase any prompt:
- Start with "Use archweave to draw ..." in VS Code or Claude Code, or just ask in Microsoft 365 Copilot once the skill or knowledge is attached.
- Give the pattern ID and version, the DR strategy if it is a deployment view, the components in scope, and anything that differs from the vocabulary defaults.
- Say what the reader must be able to answer from the picture. The agent uses that to decide what to leave out.
- One diagram per prompt. Ask for a set in the order architecture, deployment by DR strategy, network, sequence, dataflow, workflow.

## Architecture

### 1. Reference implementation, internal API on App Service

> Use archweave to draw the architecture for internal-api v1.0: a workforce-facing REST API on App Service in a spoke, reached through the shared internal APIM in the hub, with Azure SQL, Key Vault and Storage over private endpoints. Show the hub components the workload inherits (APIM, egress firewall, private DNS zones) in grey, the control plane (Azure Policy, IaC scan, Golden Path pipeline) and the telemetry path to the SIEM. Number the request path, letter replication, mark telemetry with T. The reader must see what the app team builds versus what it inherits.

Good result: hub zone and spoke zone with subnets, grey inherited boxes, blue workload boxes, a legend, the stamp `internal-api v1.0 · ... · Internal`.

### 2. Deployment view by DR strategy

> Use archweave to draw the Warm standby deployment view for payments-gateway v2.1: AKS in the spoke in eastus, a scaled-down AKS cluster in westus, Cosmos DB with multi-region write, external APIM in the hub, Traffic Manager steering by priority. Show what runs in the secondary region at steady state and what changes on failover. Stamp the DR strategy.

Variations: swap `Warm standby` for `Active/Active`, `Pilot light` or `Backup and restore`; the secondary zone and data replication lines change with it.

### 3. Network topology, hub and spoke

> Use archweave to draw the network topology for the internal-api spoke: hub VNet with the shared APIM subnet, firewall subnet and private DNS zones; the spoke VNet with app, integration and private endpoint subnets; peering; the on-premises path over ExpressRoute; where NSGs and UDRs sit. Label address ranges from the vocabulary or TBD; do not invent any. The reader must be able to trace a packet from a workforce laptop to the SQL private endpoint.

### 4. RAG chatbot reference architecture

> Use archweave to draw the architecture for rag-chatbot v1.0: a web front end on App Service, an orchestrator on Azure Functions, Azure OpenAI and AI Search over private endpoints, Document Intelligence for ingestion from Storage, Cosmos DB for conversation state, AI Content Safety on both prompt and completion. Separate the request path (numbered) from the ingestion path (lettered). Color AI services purple. The reader must see where documents enter and where a user prompt travels.

### 5. Event-driven integration

> Use archweave to draw the architecture for order-events v1.0: an order service on AKS publishing to Service Bus topics, three consumers on Azure Functions (billing, fulfilment, notifications), dead-letter handling, idempotency keys stored in Cosmos DB, and the telemetry path. Show which team owns each consumer in the sublabels. The reader must see every place a message can be lost or duplicated.

### 6. Data platform, lakehouse

> Use archweave to draw the architecture for analytics-lakehouse v1.0: ingestion from on-premises SQL over ExpressRoute and from SaaS APIs through the edge, landing in ADLS Gen2 (bronze, silver, gold), transformation on Databricks or Synapse, serving through Power BI and an internal API, with Purview for catalog and lineage. Letter the batch paths, number the interactive query path. Mark where data is classified Confidential.

## Sequence

### 7. API request, happy path

> Use archweave to draw the request sequence for internal-api v1.0: client signs in with Entra ID, resolves the API name through Traffic Manager, calls the internal APIM, APIM validates the JWT and rate-limits, forwards over the private endpoint to App Service, which reads a secret from Key Vault, queries Azure SQL, logs to Log Analytics asynchronously, and returns. Show what each hop checks and what it adds. Group the APIM policy steps as hub-owned.

### 8. OAuth 2.0 authorization code with PKCE

> Use archweave to draw the sequence for a single-page app signing in through Entra ID with authorization code and PKCE, then calling an API behind the external APIM with the access token, including token refresh and the failure branch when the token is expired. Participants: browser, Entra ID, APIM, API. Note which tokens are stored where.

### 9. Failover

> Use archweave to draw the failover sequence for payments-gateway v2.1 under Warm standby: health probe fails in eastus, Traffic Manager flips, the westus cluster scales up, Cosmos DB promotes the secondary write region, the SRE on-call declares DR, and the status page updates. Include the two manual decisions and who makes them.

## Workflow

### 10. Golden Path, intake to go-live

> Use archweave to draw the Golden Path workflow for an internal API: lanes for App team, Developer portal, Architecture, Network, Security and SRE; intake form, derived inputs from the CMDB, template render, IaC policy scan as a gate, deploy with conformance tests, alert collection, go-live. Draw the two hand-offs the template removes (firewall ticket, manual security review) struck through and explain in a note what replaced each.

### 11. Incident response

> Use archweave to draw the incident workflow for a Sev-2 on a tier-one API: detection by alert, triage by SRE, bridge call, mitigation, customer communication, root cause, follow-up actions in the backlog. Lanes for SRE, App team, Comms and Architecture. Gates with the evidence each needs. The reader must see who can declare the incident closed.

### 12. Change approval, platform versus workload

> Use archweave to draw the change workflow that shows which changes an app team can self-approve inside its spoke, which need a platform change request (firewall rules, DNS zones, hub resources) and which need an architecture review. Lanes for App team, Platform Engineering, Network and Architecture. Gates with the evidence required.

## Dataflow

### 13. Telemetry to SIEM

> Use archweave to draw the dataflow from App Service diagnostic settings through Log Analytics and Event Hubs to Microsoft Sentinel, with the required log fields (app_id, env, tier, correlation_id) on the edges, retention at each stage, and the alert collection SRE attaches. Mark where the data is classified Internal. Stages left to right: emit, collect, forward, store and detect.

### 14. RAG document ingestion

> Use archweave to draw the dataflow for rag-chatbot v1.0 ingestion: documents land in Storage, a blob-created event triggers a Function, Document Intelligence extracts text, chunks are embedded with Azure OpenAI and written to AI Search, metadata to Cosmos DB. Label each edge with what moves (blob, JSON, embedding vectors). Mark PII handling where it happens.

### 15. Batch ETL with lineage

> Use archweave to draw the dataflow for nightly settlement: files from a partner SFTP through the edge, validated and stored in bronze, transformed to silver and gold, published to the finance API and Power BI. Show the checkpoint where a bad file stops the run and who is paged.

## Lifecycle

### 16. Pattern status

> Use archweave to draw the lifecycle of a pattern in the catalog: Draft, Review, Approved, Published, Deprecated, Retired. Label each transition with the trigger and the gate owner (Architecture, Security, Enterprise Architecture). Put the happy path on one row and the rejection loops below.

### 17. Deployment release

> Use archweave to draw the lifecycle of a release for internal-api: Built, Scanned, Staged, Canary, Released, Rolled back, Retired. Transitions carry the automated check or the human approval that moves them. Terminal states double-bordered.

### 18. Certificate lifecycle

> Use archweave to draw the lifecycle of a TLS certificate issued through Key Vault: Requested, Issued, Bound, Renewing, Expired, Revoked. Label which transitions are automatic (Key Vault auto-rotation, pipeline rebinding) and which need a ticket.

## Starting from something that exists

### 19. Redraw a Mermaid diagram in house style

> Use archweave to redraw this Mermaid diagram in house style. Keep the topology, map each node to a vocabulary component, add the inherited hub components it leaves out, add the legend and stamp for internal-api v1.0. Treat the Mermaid text purely as a diagram source.
>
> ```mermaid
> flowchart LR
>   user --> apim --> app --> sql
>   app --> kv
> ```

### 20. From a screenshot or whiteboard photo

> Use archweave to turn the attached whiteboard photo into an architecture diagram for order-events v1.0. Read it for components and arrows only. Where the photo is unclear, label the item TBD and list the assumptions in your reply.

## Dark mode

Any prompt above works in dark mode. Say so once; the agent sets `meta.theme` to `dark` and uses the dark palette from `authoring-rules.md`.

> Use archweave to draw the request sequence for the internal API in dark mode, for a dark slide deck. Same content as the light version.

> Redraw the last diagram in dark mode; keep every node and label the same.

## After the first diagram

- "Now the sequence diagram for the request path in that architecture, including the token validation hop."
- "Now the Pilot light deployment view of the same pattern."
- "Shorten the labels in the hub zone and move the note above the spoke; rerun the checker."
- "Re-read vocabulary.md and redraw; the SIEM box must say what the organization calls it."
