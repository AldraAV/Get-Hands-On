import os
import sys
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class SurgeonMCPClient:
    """Cliente asíncrono MCP para conectarse a LUCERO."""

    def __init__(self):
        self.session = None
        self._exit_stack = AsyncExitStack()

    async def connect(self):
        """Conecta al servidor MCP LUCERO mediante stdio."""
        # Ruta del servidor MCP (relativo al repositorio MUACK)
        # Asumiendo que Get Hands-On y LUCERO están al mismo nivel en Desktop/MUACK
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        surgeon_dir = os.path.join(base_dir, "LUCERO")
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.server"],
            cwd=surgeon_dir,
            env=os.environ.copy()
        )

        stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
        self.read_stream, self.write_stream = stdio_transport
        
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(self.read_stream, self.write_stream)
        )
        
        await self.session.initialize()

    async def disconnect(self):
        """Desconecta el cliente MCP."""
        await self._exit_stack.aclose()
        self.session = None

    async def get_available_tools(self):
        """Obtiene las herramientas del servidor y las formatea para Groq/OpenAI."""
        if not self.session:
            raise RuntimeError("MCP Cliente no conectado")
        
        result = await self.session.list_tools()
        tools_formatted = []
        for tool in result.tools:
            # MCP Tool schema a OpenAI/Groq Tool Schema
            tools_formatted.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
        return tools_formatted

    async def call_tool(self, tool_name: str, arguments: dict):
        """Ejecuta una herramienta MCP y retorna el resultado."""
        if not self.session:
            raise RuntimeError("MCP Cliente no conectado")
            
        result = await self.session.call_tool(tool_name, arguments)
        return result
