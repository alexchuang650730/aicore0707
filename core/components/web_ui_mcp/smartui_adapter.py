"""
SmartUI Adapter for PowerAutomation 4.0

This module provides the core adapter for integrating SmartUI web interface
with PowerAutomation 4.0's MCP architecture.

Features:
- Web UI component management
- MCP protocol integration
- Real-time communication
- Component lifecycle management
- Event handling and routing
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

import websockets
from websockets.server import WebSocketServerProtocol


class ComponentType(Enum):
    """Web UI component types"""
    MONACO_EDITOR = "monaco_editor"
    GITHUB_EXPLORER = "github_explorer"
    FILE_MANAGER = "file_manager"
    AUTH_MODAL = "auth_modal"
    CODE_EDITOR = "code_editor"
    TOOLBAR = "toolbar"
    SIDEBAR = "sidebar"
    STATUS_BAR = "status_bar"


class MessageType(Enum):
    """WebSocket message types"""
    COMPONENT_REGISTER = "component_register"
    COMPONENT_UPDATE = "component_update"
    COMPONENT_EVENT = "component_event"
    MCP_REQUEST = "mcp_request"
    MCP_RESPONSE = "mcp_response"
    REALTIME_SYNC = "realtime_sync"
    AUTH_REQUEST = "auth_request"
    AUTH_RESPONSE = "auth_response"


@dataclass
class WebUIComponent:
    """Web UI component definition"""
    id: str
    type: ComponentType
    name: str
    version: str
    config: Dict[str, Any]
    state: Dict[str, Any]
    permissions: List[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    component_id: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    session_id: str
    user_id: Optional[str] = None


class SmartUIAdapter:
    """
    SmartUI Adapter for PowerAutomation 4.0
    
    Provides integration between web UI components and MCP architecture.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Component management
        self.components: Dict[str, WebUIComponent] = {}
        self.component_handlers: Dict[ComponentType, Callable] = {}
        
        # WebSocket management
        self.websocket_server = None
        self.connected_clients: Dict[str, WebSocketServerProtocol] = {}
        self.client_sessions: Dict[str, Dict[str, Any]] = {}
        
        # MCP integration
        self.mcp_coordinator = None
        self.mcp_handlers: Dict[str, Callable] = {}
        
        # Event system
        self.event_listeners: Dict[str, List[Callable]] = {}
        
        # Statistics
        self.stats = {
            "components_registered": 0,
            "messages_processed": 0,
            "active_sessions": 0,
            "errors_count": 0,
            "start_time": datetime.now()
        }
        
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default component and message handlers"""
        # Component handlers
        self.component_handlers = {
            ComponentType.MONACO_EDITOR: self._handle_monaco_editor,
            ComponentType.GITHUB_EXPLORER: self._handle_github_explorer,
            ComponentType.FILE_MANAGER: self._handle_file_manager,
            ComponentType.AUTH_MODAL: self._handle_auth_modal,
            ComponentType.CODE_EDITOR: self._handle_code_editor
        }
        
        # MCP handlers
        self.mcp_handlers = {
            "file_operation": self._handle_file_operation,
            "code_execution": self._handle_code_execution,
            "github_operation": self._handle_github_operation,
            "auth_operation": self._handle_auth_operation
        }
    
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.websocket_server = await websockets.serve(
                self._handle_websocket_connection,
                self.host,
                self.port
            )
            self.logger.info(f"SmartUI Adapter started on {self.host}:{self.port}")
            
            # Keep server running
            await self.websocket_server.wait_closed()
            
        except Exception as e:
            self.logger.error(f"Failed to start SmartUI Adapter: {e}")
            raise
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
            self.logger.info("SmartUI Adapter stopped")
    
    async def _handle_websocket_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        session_id = self._generate_session_id()
        self.connected_clients[session_id] = websocket
        self.client_sessions[session_id] = {
            "connected_at": datetime.now(),
            "user_id": None,
            "permissions": [],
            "active_components": []
        }
        
        self.stats["active_sessions"] += 1
        self.logger.info(f"New WebSocket connection: {session_id}")
        
        try:
            async for message in websocket:
                await self._process_websocket_message(session_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"WebSocket connection closed: {session_id}")
        except Exception as e:
            self.logger.error(f"WebSocket error for {session_id}: {e}")
            self.stats["errors_count"] += 1
        finally:
            # Cleanup
            if session_id in self.connected_clients:
                del self.connected_clients[session_id]
            if session_id in self.client_sessions:
                del self.client_sessions[session_id]
            self.stats["active_sessions"] -= 1
    
    async def _process_websocket_message(self, session_id: str, raw_message: str):
        """Process incoming WebSocket message"""
        try:
            message_data = json.loads(raw_message)
            message = WebSocketMessage(
                type=MessageType(message_data["type"]),
                component_id=message_data.get("component_id"),
                data=message_data["data"],
                timestamp=datetime.now(),
                session_id=session_id,
                user_id=message_data.get("user_id")
            )
            
            self.stats["messages_processed"] += 1
            
            # Route message based on type
            if message.type == MessageType.COMPONENT_REGISTER:
                await self._handle_component_register(message)
            elif message.type == MessageType.COMPONENT_UPDATE:
                await self._handle_component_update(message)
            elif message.type == MessageType.COMPONENT_EVENT:
                await self._handle_component_event(message)
            elif message.type == MessageType.MCP_REQUEST:
                await self._handle_mcp_request(message)
            elif message.type == MessageType.AUTH_REQUEST:
                await self._handle_auth_request(message)
            elif message.type == MessageType.REALTIME_SYNC:
                await self._handle_realtime_sync(message)
            else:
                self.logger.warning(f"Unknown message type: {message.type}")
                
        except Exception as e:
            self.logger.error(f"Error processing message from {session_id}: {e}")
            self.stats["errors_count"] += 1
            await self._send_error_response(session_id, str(e))
    
    async def _handle_component_register(self, message: WebSocketMessage):
        """Handle component registration"""
        try:
            component_data = message.data
            component = WebUIComponent(
                id=component_data["id"],
                type=ComponentType(component_data["type"]),
                name=component_data["name"],
                version=component_data["version"],
                config=component_data.get("config", {}),
                state=component_data.get("state", {}),
                permissions=component_data.get("permissions", []),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Register component
            self.components[component.id] = component
            self.stats["components_registered"] += 1
            
            # Add to session
            session = self.client_sessions[message.session_id]
            session["active_components"].append(component.id)
            
            # Call component-specific handler
            if component.type in self.component_handlers:
                await self.component_handlers[component.type](component, message)
            
            # Send success response
            await self._send_response(message.session_id, {
                "type": "component_registered",
                "component_id": component.id,
                "status": "success"
            })
            
            self.logger.info(f"Component registered: {component.id} ({component.type.value})")
            
        except Exception as e:
            self.logger.error(f"Error registering component: {e}")
            await self._send_error_response(message.session_id, f"Component registration failed: {e}")
    
    async def _handle_component_update(self, message: WebSocketMessage):
        """Handle component state update"""
        try:
            component_id = message.component_id
            if component_id not in self.components:
                raise ValueError(f"Component not found: {component_id}")
            
            component = self.components[component_id]
            update_data = message.data
            
            # Update component state
            if "state" in update_data:
                component.state.update(update_data["state"])
            if "config" in update_data:
                component.config.update(update_data["config"])
            
            component.updated_at = datetime.now()
            
            # Broadcast update to other sessions
            await self._broadcast_component_update(component_id, update_data, exclude_session=message.session_id)
            
            # Send success response
            await self._send_response(message.session_id, {
                "type": "component_updated",
                "component_id": component_id,
                "status": "success"
            })
            
        except Exception as e:
            self.logger.error(f"Error updating component: {e}")
            await self._send_error_response(message.session_id, f"Component update failed: {e}")
    
    async def _handle_component_event(self, message: WebSocketMessage):
        """Handle component event"""
        try:
            component_id = message.component_id
            event_data = message.data
            
            # Emit event to listeners
            await self._emit_event(f"component:{component_id}", event_data)
            
            # Handle specific component events
            if component_id in self.components:
                component = self.components[component_id]
                if component.type in self.component_handlers:
                    await self.component_handlers[component.type](component, message)
            
        except Exception as e:
            self.logger.error(f"Error handling component event: {e}")
            await self._send_error_response(message.session_id, f"Event handling failed: {e}")
    
    async def _handle_mcp_request(self, message: WebSocketMessage):
        """Handle MCP request from web UI"""
        try:
            mcp_data = message.data
            operation = mcp_data.get("operation")
            
            if operation in self.mcp_handlers:
                result = await self.mcp_handlers[operation](mcp_data, message)
                
                # Send MCP response
                await self._send_response(message.session_id, {
                    "type": "mcp_response",
                    "operation": operation,
                    "result": result,
                    "status": "success"
                })
            else:
                raise ValueError(f"Unknown MCP operation: {operation}")
                
        except Exception as e:
            self.logger.error(f"Error handling MCP request: {e}")
            await self._send_error_response(message.session_id, f"MCP request failed: {e}")
    
    async def _handle_auth_request(self, message: WebSocketMessage):
        """Handle authentication request"""
        try:
            auth_data = message.data
            auth_type = auth_data.get("type")
            
            # Handle different auth types
            if auth_type == "api_key":
                result = await self._authenticate_api_key(auth_data)
            elif auth_type == "oauth":
                result = await self._authenticate_oauth(auth_data)
            elif auth_type == "email":
                result = await self._authenticate_email(auth_data)
            else:
                raise ValueError(f"Unknown auth type: {auth_type}")
            
            # Update session with auth info
            session = self.client_sessions[message.session_id]
            session["user_id"] = result["user_id"]
            session["permissions"] = result["permissions"]
            
            # Send auth response
            await self._send_response(message.session_id, {
                "type": "auth_response",
                "status": "success",
                "user": result
            })
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            await self._send_error_response(message.session_id, f"Authentication failed: {e}")
    
    async def _handle_realtime_sync(self, message: WebSocketMessage):
        """Handle real-time synchronization"""
        try:
            sync_data = message.data
            sync_type = sync_data.get("type")
            
            # Broadcast sync message to all connected clients
            await self._broadcast_sync_message(sync_data, exclude_session=message.session_id)
            
        except Exception as e:
            self.logger.error(f"Error handling realtime sync: {e}")
    
    # Component-specific handlers
    async def _handle_monaco_editor(self, component: WebUIComponent, message: WebSocketMessage):
        """Handle Monaco Editor specific operations"""
        if message.type == MessageType.COMPONENT_EVENT:
            event_data = message.data
            event_type = event_data.get("event")
            
            if event_type == "content_change":
                # Handle code content change
                await self._handle_code_change(component, event_data)
            elif event_type == "cursor_change":
                # Handle cursor position change
                await self._handle_cursor_change(component, event_data)
            elif event_type == "selection_change":
                # Handle text selection change
                await self._handle_selection_change(component, event_data)
    
    async def _handle_github_explorer(self, component: WebUIComponent, message: WebSocketMessage):
        """Handle GitHub Explorer specific operations"""
        if message.type == MessageType.COMPONENT_EVENT:
            event_data = message.data
            event_type = event_data.get("event")
            
            if event_type == "file_select":
                # Handle file selection
                await self._handle_file_select(component, event_data)
            elif event_type == "repo_change":
                # Handle repository change
                await self._handle_repo_change(component, event_data)
    
    async def _handle_file_manager(self, component: WebUIComponent, message: WebSocketMessage):
        """Handle File Manager specific operations"""
        pass
    
    async def _handle_auth_modal(self, component: WebUIComponent, message: WebSocketMessage):
        """Handle Auth Modal specific operations"""
        pass
    
    async def _handle_code_editor(self, component: WebUIComponent, message: WebSocketMessage):
        """Handle Code Editor specific operations"""
        pass
    
    # MCP operation handlers
    async def _handle_file_operation(self, mcp_data: Dict[str, Any], message: WebSocketMessage) -> Dict[str, Any]:
        """Handle file operations through MCP"""
        operation = mcp_data.get("file_operation")
        
        if operation == "read":
            # Read file content
            file_path = mcp_data.get("path")
            # TODO: Integrate with MCP file service
            return {"content": "file content", "path": file_path}
        elif operation == "write":
            # Write file content
            file_path = mcp_data.get("path")
            content = mcp_data.get("content")
            # TODO: Integrate with MCP file service
            return {"success": True, "path": file_path}
        else:
            raise ValueError(f"Unknown file operation: {operation}")
    
    async def _handle_code_execution(self, mcp_data: Dict[str, Any], message: WebSocketMessage) -> Dict[str, Any]:
        """Handle code execution through MCP"""
        code = mcp_data.get("code")
        language = mcp_data.get("language")
        
        # TODO: Integrate with MCP code execution service
        return {
            "output": "execution result",
            "status": "success",
            "language": language
        }
    
    async def _handle_github_operation(self, mcp_data: Dict[str, Any], message: WebSocketMessage) -> Dict[str, Any]:
        """Handle GitHub operations through MCP"""
        operation = mcp_data.get("github_operation")
        
        if operation == "list_files":
            repo = mcp_data.get("repo")
            path = mcp_data.get("path", "")
            # TODO: Integrate with GitHub API
            return {"files": [], "repo": repo, "path": path}
        else:
            raise ValueError(f"Unknown GitHub operation: {operation}")
    
    async def _handle_auth_operation(self, mcp_data: Dict[str, Any], message: WebSocketMessage) -> Dict[str, Any]:
        """Handle authentication operations through MCP"""
        # TODO: Integrate with MCP auth service
        return {"authenticated": True, "user_id": "user123"}
    
    # Authentication methods
    async def _authenticate_api_key(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using API key"""
        api_key = auth_data.get("api_key")
        
        # TODO: Validate API key with auth service
        # Mock implementation
        if api_key and api_key.startswith("admin_"):
            return {
                "user_id": "admin_user",
                "role": "admin",
                "permissions": ["read", "write", "admin"]
            }
        elif api_key and api_key.startswith("dev_"):
            return {
                "user_id": "dev_user",
                "role": "developer",
                "permissions": ["read", "write"]
            }
        elif api_key and api_key.startswith("user_"):
            return {
                "user_id": "regular_user",
                "role": "user",
                "permissions": ["read"]
            }
        else:
            raise ValueError("Invalid API key")
    
    async def _authenticate_oauth(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using OAuth"""
        provider = auth_data.get("provider")
        token = auth_data.get("token")
        
        # TODO: Validate OAuth token
        return {
            "user_id": f"{provider}_user",
            "role": "user",
            "permissions": ["read"]
        }
    
    async def _authenticate_email(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using email/password"""
        email = auth_data.get("email")
        password = auth_data.get("password")
        
        # TODO: Validate email/password
        return {
            "user_id": email,
            "role": "user",
            "permissions": ["read"]
        }
    
    # Event system
    async def _emit_event(self, event_name: str, data: Dict[str, Any]):
        """Emit event to listeners"""
        if event_name in self.event_listeners:
            for listener in self.event_listeners[event_name]:
                try:
                    await listener(data)
                except Exception as e:
                    self.logger.error(f"Error in event listener for {event_name}: {e}")
    
    def add_event_listener(self, event_name: str, listener: Callable):
        """Add event listener"""
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
        self.event_listeners[event_name].append(listener)
    
    def remove_event_listener(self, event_name: str, listener: Callable):
        """Remove event listener"""
        if event_name in self.event_listeners:
            try:
                self.event_listeners[event_name].remove(listener)
            except ValueError:
                pass
    
    # Utility methods
    async def _send_response(self, session_id: str, data: Dict[str, Any]):
        """Send response to specific session"""
        if session_id in self.connected_clients:
            try:
                websocket = self.connected_clients[session_id]
                await websocket.send(json.dumps(data))
            except Exception as e:
                self.logger.error(f"Error sending response to {session_id}: {e}")
    
    async def _send_error_response(self, session_id: str, error_message: str):
        """Send error response to specific session"""
        await self._send_response(session_id, {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _broadcast_component_update(self, component_id: str, update_data: Dict[str, Any], exclude_session: str = None):
        """Broadcast component update to all sessions"""
        message = {
            "type": "component_update_broadcast",
            "component_id": component_id,
            "data": update_data,
            "timestamp": datetime.now().isoformat()
        }
        
        for session_id, websocket in self.connected_clients.items():
            if session_id != exclude_session:
                try:
                    await websocket.send(json.dumps(message))
                except Exception as e:
                    self.logger.error(f"Error broadcasting to {session_id}: {e}")
    
    async def _broadcast_sync_message(self, sync_data: Dict[str, Any], exclude_session: str = None):
        """Broadcast sync message to all sessions"""
        message = {
            "type": "realtime_sync_broadcast",
            "data": sync_data,
            "timestamp": datetime.now().isoformat()
        }
        
        for session_id, websocket in self.connected_clients.items():
            if session_id != exclude_session:
                try:
                    await websocket.send(json.dumps(message))
                except Exception as e:
                    self.logger.error(f"Error broadcasting sync to {session_id}: {e}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return str(uuid.uuid4())
    
    # Component event handlers
    async def _handle_code_change(self, component: WebUIComponent, event_data: Dict[str, Any]):
        """Handle code content change"""
        # Broadcast code change to other sessions for real-time collaboration
        await self._broadcast_component_update(
            component.id,
            {"event": "content_change", "data": event_data}
        )
    
    async def _handle_cursor_change(self, component: WebUIComponent, event_data: Dict[str, Any]):
        """Handle cursor position change"""
        # Broadcast cursor change for real-time collaboration
        await self._broadcast_component_update(
            component.id,
            {"event": "cursor_change", "data": event_data}
        )
    
    async def _handle_selection_change(self, component: WebUIComponent, event_data: Dict[str, Any]):
        """Handle text selection change"""
        # Broadcast selection change for real-time collaboration
        await self._broadcast_component_update(
            component.id,
            {"event": "selection_change", "data": event_data}
        )
    
    async def _handle_file_select(self, component: WebUIComponent, event_data: Dict[str, Any]):
        """Handle file selection in GitHub explorer"""
        file_path = event_data.get("file_path")
        repo = event_data.get("repo")
        
        # Emit file selection event
        await self._emit_event("file_selected", {
            "file_path": file_path,
            "repo": repo,
            "component_id": component.id
        })
    
    async def _handle_repo_change(self, component: WebUIComponent, event_data: Dict[str, Any]):
        """Handle repository change in GitHub explorer"""
        repo = event_data.get("repo")
        
        # Emit repo change event
        await self._emit_event("repo_changed", {
            "repo": repo,
            "component_id": component.id
        })
    
    # Statistics and monitoring
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        uptime = datetime.now() - self.stats["start_time"]
        
        return {
            **self.stats,
            "uptime_seconds": uptime.total_seconds(),
            "components_count": len(self.components),
            "active_sessions": len(self.connected_clients)
        }
    
    def get_components(self) -> List[Dict[str, Any]]:
        """Get all registered components"""
        return [asdict(component) for component in self.components.values()]
    
    def get_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Get specific component"""
        if component_id in self.components:
            return asdict(self.components[component_id])
        return None


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartUI Adapter for PowerAutomation 4.0")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start adapter
    adapter = SmartUIAdapter(host=args.host, port=args.port)
    
    try:
        asyncio.run(adapter.start_server())
    except KeyboardInterrupt:
        print("\nShutting down SmartUI Adapter...")

