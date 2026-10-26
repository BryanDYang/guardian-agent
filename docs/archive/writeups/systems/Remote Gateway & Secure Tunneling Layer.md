> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../../architecture.md) for implementation and [the roadmap](../../milestone_3/roadmap.md) for current work.

The Remote Gateway & Secure Tunneling Layer bridges the native iOS client over cellular or Wi-Fi to the local FastAPI backend running on your M4 Mac. By deploying an outbound-only daemon like Cloudflare Tunnel (`cloudflared`) or a Tailscale mesh VPN, it provides an encrypted gateway without cloud server costs, port forwarding, or dynamic DNS configuration.

**1. Outbound Encrypted Ingress**

- **Zero Inbound Port Exposure:** Runs a lightweight daemon on macOS that connects outbound to edge nodes, exposing `localhost:8000` via a public HTTPS hostname (such as `[https://api.yourlab.dev](https://api.yourlab.dev)`) or a private Tailscale IP.
- **Public IP Abstraction:** Allows field iPhones to reliably hit the workstation regardless of changing residential IP addresses, NAT boundaries, or router firewalls.

**2. Real-Time Full-Duplex WebSockets**

- **Persistent Status Streaming:** Transparently proxies WebSocket upgrades (`starlette.websockets` on FastAPI to `URLSessionWebSocketTask` in SwiftUI).
- **Pipeline Feedback:** Streams live stage transitions (*"Transcribing..."*, *"Diarizing..."*, *"Extracting Tasks..."*) to the UI while the sequential worker processes audio on Apple Silicon.

**3. Resilient Background Media Transport**

- **Large Audio Ingestion:** Facilitates multi-megabyte MP3 and M4A file transfers dispatched via iOS `URLSessionConfiguration.background`. Uploads persist and complete reliably even if the iOS app is suspended or the iPhone is locked.
- **Byte-Range Scrubbing Passthrough:** Relays HTTP `206 Partial Content` headers smoothly, enabling `AVPlayer` to stream rational `CMTime` byte-slices for citation proof checks without downloading full recording files.

**4. Edge Protection & Access Policy Gateway**

- **Compute Insulation:** Serves as the first barrier shielding local hardware (M4 GPU, Neural Engine, unified memory) from malicious internet traffic, DDOS attacks, and unauthenticated scrapers before reaching FastAPI's project access guards.
- **Managed TLS Termination:** Automatically handles modern HTTPS/TLS certificate generation and renewal at the edge, guaranteeing secure transit for sensitive meeting dialogue.



## API Specification


| **Endpoint** | **Method** | **Auth Required**                                                                                                 | **Request Body / Query** | **Status Codes**                                     | **Description**                                                                                                                                          |
| ------------ | ---------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/health`    | `GET`      | Requires HTTP Header `Authorization: Bearer <STATIC_PRE_SHARED_SECRET>` validated at the FastAPI dependency layer | None                     | `200 OK` `502 Bad Gateway` `503 Service Unavailable` | Lightweight heartbeat probe to verify that the tunnel daemon is active and FastAPI is accepting connections before dispatching heavy pipeline workloads. |


