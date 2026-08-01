# Integración de Engram y Gentle-AI en OHM

Guía de referencia para usuarios y desarrolladores sobre cómo integrar **Engram** (memoria persistente) y **Gentle-AI** (orquestación, persona, SDD y skills) en el framework OHM.

---

## 1. Engram (Memoria Persistente)

### Configuración MCP (Sin modificar código)

Para integrar Engram como servidor MCP a nivel de proyecto, crea o edita `.mcp.json` en la raíz del proyecto:

```json
{
  "mcpServers": {
    "engram": {
      "command": "engram",
      "args": [
        "mcp",
        "--tools=agent",
        "--project=ohm"
      ]
    }
  }
}
```

Si tu harness OHM ya soporta carga de servidores MCP, el agente dispondrá automáticamente de las herramientas `mem_save`, `mem_search`, `mem_context`, etc., sin escribir una sola línea de código Python.

### Modificación ligera en OHM (Opcional para hooks automáticos)

Si quieres que OHM guarde contexto o resúmenes de sesión automáticamente en Engram al cerrar o en cada prompt sin depender de que el LLM decida invocar la herramienta, puedes agregar hooks en `src/ohm/core/agent.py` o `app.py` que hagan peticiones HTTP al servidor local de Engram (`http://127.0.0.1:7437`) o invoquen la CLI (`engram save ...`).

---

## 2. Gentle-AI (Configuración, Persona, SDD y Skills)

### Uso directo sin modificar código

Gentle-AI actúa como un orquestador y formateador de entorno:

1. **Reglas y Persona**: Copias las reglas de estilo/persona o directivas SDD a tu archivo de reglas (`AGENTS.md` o prompt del sistema de OHM).
2. **Skills**: Ubicas los paquetes de habilidades en `.agents/skills/` o `.ohm/skills/`.

### Ajuste en OHM

En tu aplicación OHM solo necesitas asegurarte de que `OHMConfig` / `Agent` lean el prompt de sistema (que incluye la persona y directivas de Gentle-AI) y que tu registro de skills cargue las carpetas de `.agents/skills/`.

---

## Resumen

Puedes aplicar ambos directamente mediante configuración y argumentos CLI/MCP. No requiere modificar las herramientas de terceros. En OHM solo editas código si deseas automatizar disparadores internos (*lifecycle hooks*) para Engram o personalizar la carga de prompts/skills de Gentle-AI.
