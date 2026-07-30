# Multi-Agent Chatroom — Análisis y Visión

## Concepto

Un chatroom experimental donde **múltiples agentes de IA y usuarios humanos** interactúan en un mismo espacio. Cada agente tiene su propia personalidad, configuración de modelo, y capacidad de responder autónomamente o cuando es mencionado.

## Stack de Protocolos (2026)

La industria ha convergido en un modelo de **tres capas** para comunicación de agentes:

```
┌──────────────────────────────────────┐
│   AG-UI: Agent → User Interface      │  Presentación
├──────────────────────────────────────┤
│   A2A: Agent → Agent Communication   │  Coordinación
├──────────────────────────────────────┤
│   MCP: Agent → Tool Integration      │  Capacidades
└──────────────────────────────────────┘
```

| Protocolo | Capa | Creador | Estado 2026 |
|-----------|------|---------|-------------|
| **MCP** | Agent → Tools | Anthropic (2024) | Producción masiva — 97M descargas/mes |
| **A2A** | Agent → Agent | Google (2025) | Madurando — 150+ orgs, v1.0 |
| **ACP** | Agent → Agent (interno) | IBM (2024) | Fusionado con A2A (2025) |
| **AG-UI** | Agent → Frontend | Comunidad | Emergente |
| **ANP** | Red P2P descentralizada | Comunidad | Nicho |

## Implicaciones para OHM

OHM ya usa **MCP** indirectamente (el propio OpenCode/Claude lo usa para tool calling). Lo que falta es la capa **A2A** para comunicación entre agentes.

### Arquitectura propuesta

```
Usuario 1 ──┐
             ├── OHM Chatroom ──┬── Agente A (Claude Sonnet)
Usuario 2 ──┘                  ├── Agente B (GPT-4 Turbo)
                                ├── Agente C (Local Ollama)
                                └── Sistema de orquestación
```

### Comandos sugeridos para el futuro

| Comando | Descripción |
|---------|-------------|
| `/room create <nombre>` | Crear un nuevo chatroom multi-agente |
| `/room list` | Listar chatrooms activos |
| `/room join <id>` | Unirse a un chatroom existente |
| `/room leave` | Salir del chatroom actual |
| `/room invite <agent>` | Invitar un agente al chatroom |
| `/room kick <agent>` | Expulsar un agente |
| `/room agents` | Listar agentes en el chatroom actual |
| `/room whisper <agent> <msg>` | Mensaje privado a un agente específico |

## Referencias

- [A2A Protocol Specification](https://a2a-protocol.org/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP vs A2A: 2026 Comparison](https://pickaxe.co/post/mcp-vs-a2a-protocol)
- [Agent Interoperability Protocols 2026](https://zylos.ai/research/2026-02-15-agent-to-agent-communication-protocols/)
- [A2A Protocol 2026 Guide](https://niteagent.com/blog/a2a-protocol-guide-2026/)

## Riesgos

- **Madurez**: A2A está en v1.0 pero el ecosistema aún es temprano
- **Complejidad**: Orquestar múltiples agentes concurrentes es más difícil que un agente único
- **Costo**: Cada agente activo consume tokens continuamente
- **Colisión**: Múltiples agentes respondiendo al mismo tiempo requieren un sistema de turnos o prioridades
