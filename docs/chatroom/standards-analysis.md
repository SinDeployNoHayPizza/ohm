# Análisis de Estándares de Comunicación entre Agentes (2026)

## Resumen Ejecutivo

La guerra de protocolos ha terminado. El consenso de la industria es **coexistencia multi-protocolo**, similar a cómo HTTP, WebSocket y gRPC coexisten en la web moderna. Para OHM, la estrategia correcta es:

1. **MCP** para integración con herramientas (ya lo usamos indirectamente)
2. **A2A** para comunicación entre agentes (lo que necesitamos implementar)
3. **WebSocket** para comunicación en tiempo real con el frontend TUI

---

## 1. MCP (Model Context Protocol)

| Dato | Valor |
|------|-------|
| **Creador** | Anthropic (Nov 2024) |
| **Gobernanza** | Linux Foundation / AAIF |
| **Arquitectura** | Cliente-Servidor |
| **Transporte** | JSON-RPC 2.0 sobre stdio o HTTP |
| **Adopción** | 97M descargas/mes, 10K+ servidores públicos |
| **SDKs** | Python, TypeScript, Java, C#, Go |

**¿Qué resuelve?** Conexión de un agente a herramientas externas (APIs, bases de datos, Slack, GitHub).

**Analogía**: USB-C para IA.

**Relevancia para OHM**: OHM ya usa MCP internamente a través de OpenCode/Claude para tool calling. No necesitamos implementarlo directamente, sino asegurarnos de que los agentes del chatroom puedan usar herramientas MCP.

## 2. A2A (Agent-to-Agent Protocol)

| Dato | Valor |
|------|-------|
| **Creador** | Google (Abr 2025) |
| **Gobernanza** | Linux Foundation / AAIF |
| **Arquitectura** | Peer-like (Cliente-Remoto) |
| **Transporte** | HTTP, gRPC, SSE |
| **Adopción** | 150+ organizaciones, v1.0, SDKs en 5 lenguajes |
| **SDKs** | Python (`pip install a2a-sdk`), JS, Go, Java, .NET |

**¿Qué resuelve?** Comunicación entre agentes de diferentes proveedores y frameworks. Permite:
- **Agent Cards**: Descubrimiento automático de capacidades de agentes
- **Task Lifecycle**: Ciclo de vida de tareas (submitted → working → completed → failed → input-required)
- **Streaming**: Notificaciones en tiempo real via SSE
- **Artifact Sharing**: Intercambio de artefactos entre agentes

**Analogía**: La capa IP de internet para agentes.

**Relevancia para OHM**: Este es el protocolo clave para el chatroom multi-agente. Podemos modelar cada agente del chatroom como un A2A peer.

## 3. ACP (Agent Communication Protocol)

| Dato | Valor |
|------|-------|
| **Creador** | IBM (2024) |
| **Gobernanza** | Linux Foundation |
| **Estado** | Fusionado con A2A (Ago 2025) |

**¿Qué resuelve?** Comunicación entre agentes dentro del mismo runtime/framework.

Ya no es relevante como estándar independiente — IBM lo fusionó con A2A. Es mencionado aquí solo para contexto histórico.

## 4. ANP (Agent Network Protocol)

| Dato | Valor |
|------|-------|
| **Creador** | Comunidad |
| **Gobernanza** | Comunidad |
| **Arquitectura** | P2P Descentralizada |
| **Transporte** | HTTPS, JSON-LD |

**¿Qué resuelve?** Mercados descentralizados de agentes con identidad basada en W3C DIDs.

**Relevancia para OHM**: Demasiado temprano y nicho. Monitorear pero no implementar.

---

## Recomendación para OHM

### Prioridad Inmediata
1. Investigar integración con **A2A Python SDK** (`pip install a2a-sdk`)
2. Modelar cada agente del chatroom como un peer A2A con su propio **Agent Card**
3. Usar **WebSocket** para comunicación en tiempo real con la TUI (ya tenemos Textual)

### Arquitectura Propuesta

```
┌──────────────────────────────────────────┐
│            OHM Chatroom                   │
│                                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ Agente  │  │ Agente  │  │ Agente  │   │
│  │ Claude  │  │ GPT-4   │  │ Local   │   │
│  │ A2A     │  │ A2A     │  │ A2A     │   │
│  └────┬────┘  └────┬────┘  └────┬────┘   │
│       │            │            │         │
│  ┌────┴────────────┴────────────┴────┐    │
│  │      Orchestrador (A2A Hub)       │    │
│  │  - Descubrimiento (Agent Cards)   │    │
│  │  - Enrutamiento de mensajes       │    │
│  │  - Control de concurrencia        │    │
│  └────────────────┬──────────────────┘    │
│                   │                        │
│  ┌────────────────┴──────────────────┐    │
│  │     WebSocket / TUI Frontend      │    │
│  │     (Textual)                     │    │
│  └───────────────────────────────────┘    │
└──────────────────────────────────────────┘
```

### Mecanismo de Colisión

Cuando múltiples agentes compiten por responder en un chatroom:

1. **Turn-based**: Round-robin entre agentes activos
2. **Mention-based**: Solo responde cuando es @mencionado
3. **Priority-based**: Agentes con mayor prioridad responden primero
4. **Coordinator pattern**: Un agente orquestador decide quién responde

Para OHM recomiendo empezar con **mention-based + coordinator pattern**: los agentes solo responden cuando se les menciona explícitamente, y un orquestador ligero gestiona el flujo.

### Prevención de Colisiones en Estado Compartido

Basado en investigación de sistemas multi-agente en producción:

- **Límites de ownership claros**: Cada agente tiene su dominio de datos
- **Locking**: Mecanismo de bloqueo para recursos compartidos
- **Estado inmutable**: El estado compartido es solo lectura; las mutaciones pasan por el orquestador
- **Audit trail**: Cada interacción queda registrada para depuración

---

## Referencias

- [A2A Specification v1.0](https://a2a-protocol.org/)
- [MCP Specification 2026-07-28](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate)
- [A2A Protocol 2026 Guide (NiteAgent)](https://niteagent.com/blog/a2a-protocol-guide-2026/)
- [MCP vs A2A Comparison (Pickaxe)](https://pickaxe.co/post/mcp-vs-a2a-protocol)
- [Zylos Research: Agent Interoperability Protocols 2026](https://zylos.ai/research/2026-02-15-agent-to-agent-communication-protocols/)
- [Presenc AI: A2A vs MCP Standards 2026](https://presenc.ai/research/a2a-vs-mcp-agent-communication-2026)
- [SkillGen: MCP and A2A Standardization](https://skillgen.io/mcp-a2a-protocols-standardization-2026)
- [LLM Fallback Patterns 2026 (TrueFoundry)](https://www.truefoundry.com/blog/what-is-llm-fallback)
- [LLM Fallback Strategies (BuildMVPFast)](https://www.buildmvpfast.com/blog/llm-fallback-strategies-primary-model-secondary-model-2026)
