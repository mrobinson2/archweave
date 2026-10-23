# Vocabulary

Names, positions and defaults for your organization's platform components. This file is the single place the skill learns organization facts. Everything else in ArchWeave is generic; this file is what makes a diagram yours.

**Replace the sample values.** The values below describe a fictional "Example Corporation" running a hub-and-spoke Azure landing zone with mostly Azure-native platform services. They are realistic in shape so the examples render well, and wrong for your organization by construction. Keep the table structure, change the facts, delete rows you do not have, add rows you do.

Rules the agent follows when reading this file:
- Use these names exactly. Where a value is unknown for the workload, use the default here and say so in the reply.
- Never invent an address, hostname or SKU that is not here or in the prompt.
- If this file still carries the sample values, say "vocabulary is the sample" in the reply.

## Zones (architecture and dataflow)

| Zone id | Kind | Label | Default content |
|---|---|---|---|
| `internet` | trust | Internet / users | customers, partners, workforce (via the identity provider) |
| `edge` | trust, third party | Edge | CDN and WAF (Cloudflare in the sample), origin IP allow-list, rotating origin header |
| `hub` | network, platform owned | Hub VNet | shared APIM, egress firewall, Private DNS zones, hub Key Vault, Bastion |
| `spoke` | network, workload owned | Spoke VNet | app subnet, integration subnet, private endpoint subnet |
| `data` | persistence | Data services | Cosmos DB, Azure SQL, Storage, AI Search, Redis |
| `ai` | service | AI services | Azure OpenAI, Document Intelligence, Speech, AI Content Safety |
| `secondary` | region | Secondary region | warm, pilot-light or restore-only copy per DR strategy |
| `observability` | platform owned | Observability | Log Analytics, Event Hubs, SIEM (Microsoft Sentinel in the sample), alert collections |
| `control` | platform owned | Control plane | Azure Policy (DINE), IaC policy scan, PAM and PIM, CMDB, EA repository, developer portal |
| `onprem` | network | On-premises | data centers, ExpressRoute, core services |

## Components and positions

| Component | Icon id | Color | Position and default (sample) |
|---|---|---|---|
| Edge CDN and WAF | `i-edge` | orange | Cloudflare for every internet-exposed endpoint. Origin IP allow-list at APIM, rotating secret header checked by APIM policy. Owned by Network and Security. Alternatives: Akamai, Fastly, Azure Front Door. |
| DNS steering | `i-dns-lb` | orange | Azure Traffic Manager. `api-internal.example.com` resolves via Traffic Manager to the regional APIM by health and priority. Owned by Network. Alternatives: Azure Front Door, a third-party global load balancer. |
| Shared APIM (external) | `i-apim` | grey | Hub, Premium, internal mode, subnet `10.0.4.0/26` in `hub-vnet-eastus`. Workload registers APIs and products; does not deploy its own APIM without an architecture exception. |
| Shared APIM (internal) | `i-apim` | grey | Hub, same instance or internal gateway, workforce traffic via Entra ID. |
| Egress firewall | `i-firewall` | grey | Azure Firewall in the hub, all spoke egress and inter-spoke traffic. Rules requested through a change request. Alternative: a third-party NVA in the hub. |
| Private DNS zones | `i-dns` | grey | Hub owned, linked to every spoke. Workload never creates zones; it creates records through PE auto-registration. |
| Hub VNets | zone | grey | `hub-vnet-eastus 10.0.0.0/21`, `hub-vnet-westus 10.1.0.0/21`. |
| Spoke VNet | zone | blue | Allocated at developer-portal intake from IPAM (Infoblox in the sample). Three subnets minimum: app, integration, private endpoints. |
| App Service | `i-app` | blue | Premium v3, VNet integration on, private endpoint for inbound, public access off. Zone redundant for Active/Active and Warm standby. |
| Azure Functions | `i-func` | blue | Elastic Premium, VNet integrated, same subnet rules as App Service. |
| AKS | `i-aks` | blue | Private cluster, Azure CNI overlay, user node pools per workload class, Workload Identity. Built via Golden Path. |
| Cosmos DB | `i-cosmos` | purple | Private endpoint only, CMK from workload Key Vault, multi-region write for Active/Active, periodic backup for Pilot light and Backup and restore. |
| Azure SQL | `i-sql` | blue | Private endpoint only, Entra auth only, auto-failover group for Active/Active and Warm standby. |
| Storage | `i-storage` | blue | Private endpoint, no public access, CMK, soft delete 14 d, GRS unless the DR strategy is Backup and restore, then LRS. |
| AI Search | `i-search` | purple | Private endpoint, shared private link to Storage, semantic ranker on for RAG. |
| Azure OpenAI | `i-openai` | purple | Regional Standard, private endpoint, content filters on, TPM from capacity request. |
| Document Intelligence | `i-doc` | purple | Private endpoint, same region as Storage. |
| Key Vault | `i-kv` | blue | Premium, per region, purge protection on. Sample decision: access policy model rather than RBAC because platform automation hit RBAC propagation delay (ADR-internal-api-003). |
| Event Hubs | `i-eh` | teal | Platform owned, diagnostic settings target, the SIEM data connector reads from here. |
| Log Analytics | `i-law` | teal | One workspace per workload per environment, 90 d retention default. Alternatives for APM: Datadog, Dynatrace. |
| SIEM | `i-siem` | teal | Microsoft Sentinel is the system of record for logs. Required log fields: app_id, env, tier, correlation_id. Alternatives: Elastic, Datadog. |
| Azure Policy | `i-policy` | grey | DINE assignments at management group deploy diagnostics, PE DNS, tags. Workload cannot opt out. |
| IaC policy scan | `i-ai` | grey | Checkov in the pipeline, drift check after deploy. Findings route to the app team. |
| PAM and PIM | `i-pim` | orange | Service accounts vaulted in the PAM tool, PIM 4 h sessions for contributor, no standing owner. |
| Identity provider | `i-idp` | blue | Entra ID for workforce, managed identities for all service-to-service, no client secrets. Alternative: Okta for workforce SSO. |
| CMDB and EA repository | `i-cmdb` | grey | The CMDB is the source of app ID, DR strategy, owner. Pattern inputs derive from here. |
| Developer portal | `i-repo` | grey | Backstage. Golden Path templates; the intake form collects only the asked inputs. |
| Pipeline | `i-pipeline` | grey | GitHub Actions or Azure DevOps. Terraform from private module registry, policy scan, conformance tests. |
| Change ticket | `i-ticket` | grey | Change request for firewall and DNS changes. The hand-off the Golden Path removes where possible. |

## Owner lanes (workflow)

Top to bottom: App team · Architecture · Platform Engineering · Network · Security · SRE · Enterprise Architecture · FinOps. These are also the only values allowed in `owner` fields; edit `schemas/common.schema.json` if your lanes differ.

## DR strategies (deployment views)

| DR strategy | Topology | Data | RTO/RPO guidance |
|---|---|---|---|
| Active/Active | both regions serve traffic, DNS weighted | multi-region write | minutes / near zero |
| Warm standby | secondary deployed and scaled down, DNS failover | geo-replica, read-only | under 1 h / minutes |
| Pilot light | secondary IaC only, data replicated | GRS or geo-backup | hours / 1 h |
| Backup and restore | single region, zone redundant where free | LRS, backup | day / day |

The DR strategy's source of truth is the resilience standard and the CMDB, not this file. Stamp the DR strategy on the diagram; do not restate RTO/RPO numbers unless the prompt gives them.

## Pattern IDs

Kebab-case slugs: `internal-api`, `internal-api-golden-path`, `rag-chatbot`, `payments-gateway`. An optional `version` such as `1.0` appears in the footer as `v1.0`. ADRs: `ADR-PLT-####` (platform, in the EA repository), `ADR-{pattern-id}-###` (pattern repo), `ADR-APP-{appid}-###` (app repo). Change the regex in `schemas/common.schema.json` if your catalog uses a different form.

## Things never to draw

- Public IPs on PaaS services (all private endpoint).
- Workload-owned APIM, firewall, DNS zone or hub resources.
- Secrets in Key Vault used by code (managed identity instead).
- A direct internet path that bypasses the edge.
