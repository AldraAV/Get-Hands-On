import asyncio
import json
from PyQt6.QtCore import QThread, pyqtSignal
from ..core.llm_provider import GroqProvider
from ..core.surgeon_client import SurgeonMCPClient

class NonaWorker(QThread):
    """
    Hilo asíncrono para manejar las llamadas a Groq y al cliente MCP de LUCERO
    sin congelar la interfaz de usuario de MeterMano.
    """
    # Señales para comunicarse con la UI principal
    log_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, document_path: str, user_prompt: str, parent=None):
        super().__init__(parent)
        self.document_path = document_path
        self.user_prompt = user_prompt
        
    def run(self):
        """Método principal ejecutado por QThread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.execute_flow())
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            loop.close()
            
    async def execute_flow(self):
        """Flujo lógico de Nona."""
        self.log_signal.emit("⚡ Iniciando conexión con el cerebro de Nona (Groq) y el Décimo Hermano (MCP)...")
        
        llm = GroqProvider()
        mcp_client = SurgeonMCPClient()
        
        try:
            await mcp_client.connect()
            self.log_signal.emit("✅ Conectado a LUCERO.")
            
            tools = await mcp_client.get_available_tools()
            
            # Prompts iniciales
            # Inyectamos el path_del_documento para que el LLM lo conozca.
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres Nona, una IA asistente de la aplicación 'MeterMano'. "
                        "Tu tarea es ayudar al usuario a modificar su documento de Word usando LUCERO. "
                        f"El documento actual con el que estás trabajando es: {self.document_path}\n"
                        "Debes SIEMPRE usar las herramientas disponibles para cumplir el pedido del usuario. "
                        "El usuario te hablará de forma coloquial, responde amigablemente pero prioriza ejecutar las herramientas. "
                        "Si la tarea requiere inyectar imágenes, reemplazar, cambiar estilos de párrafo o títulos, usa la herramienta adecuada pasándole el 'docx_path'. "
                        "Explica brevemente qué herramienta usaste al final."
                    )
                },
                {
                    "role": "user",
                    "content": self.user_prompt
                }
            ]
            
            self.log_signal.emit("🧠 Analizando instrucción humana...")
            response = await llm.get_response(messages, tools=tools)
            
            # Procesar Function Calling
            if response.tool_calls:
                messages.append(response) # Añadir el assistant message
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Forzar el path si no lo puso (o si lo ignoró)
                    if 'docx_path' not in tool_args:
                        tool_args['docx_path'] = self.document_path
                        
                    self.log_signal.emit(f"🔧 Ejecutando herramienta: {tool_name}...")
                    
                    # Llamar al MCP local
                    try:
                        mcp_result = await mcp_client.call_tool(tool_name, tool_args)
                        # Formatear la respuesta
                        content = []
                        if hasattr(mcp_result, 'content'):
                            for item in mcp_result.content:
                                if item.type == 'text':
                                    content.append(item.text)
                        
                        tool_result_str = "\n".join(content) if content else "Ejecución completada sin output de texto."
                        
                        self.log_signal.emit(f"✅ Resultado MCP: {tool_result_str}")
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result_str
                        })
                        
                    except Exception as e:
                        error_msg = f"Error ejecutando la herramienta MCP: {str(e)}"
                        self.error_signal.emit(error_msg)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": error_msg
                        })
                
                # Segunda llamada a Groq con los resultados
                self.log_signal.emit("🧠 Generando reporte final...")
                final_response = await llm.get_response(messages)
                self.log_signal.emit(f"🍒 Nona: {final_response.content}")
                
            else:
                self.log_signal.emit(f"🍒 Nona: {response.content}")
                
            self.finished_signal.emit()
            
        except Exception as e:
            self.error_signal.emit(f"Falla crítica: {str(e)}")
        finally:
            await mcp_client.disconnect()
