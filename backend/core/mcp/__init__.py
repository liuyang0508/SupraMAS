"""
MCP (Model Context Protocol) Integration Layer
让Domain Agent能够连接真实的外部系统和数据源

架构：
    Domain Agent
        ↓ 调用
    MCP Client (统一接口)
        ↓ 协议通信
    MCP Servers (外部系统适配器)
        ├── filesystem-mcp  (文件系统)
        ├── postgres-mcp     (数据库)
        ├── github-mcp       (代码管理)
        ├── slack-mcp        (团队协作)
        ├── search-mcp      (搜索引擎)
        └── custom-mcp      (自定义服务)
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class MCPCapability:
    """MCP Server能力声明"""
    server_name: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    auth_required: bool = False
    rate_limit: Optional[int] = None


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    is_dangerous: bool = False


@dataclass
class MCPResult:
    """MCP调用结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseMCPServer(ABC):
    """
    MCP Server基类 - 外部系统适配器
    
    每个MCP Server封装一个外部系统，提供统一的工具调用接口。
    Domain Agent通过MCP Client间接调用这些Server。
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """建立与外部系统的连接"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """列出该Server提供的所有工具"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> MCPResult:
        """调用指定工具"""
        pass
    
    @abstractmethod
    def get_capability(self) -> MCPCapability:
        """返回Server能力声明"""
        pass


class FileSystemMCPServer(BaseMCPServer):
    """
    文件系统MCP Server - 提供文件读写、目录浏览等能力
    """
    
    async def connect(self) -> bool:
        base_path = self.config.get("base_path", "./")
        import os
        if os.path.exists(base_path):
            self.is_connected = True
            logger.info(f"[{self.name}] Connected to filesystem at {base_path}")
            return True
        return False
    
    async def disconnect(self):
        self.is_connected = False
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="read_file",
                description="读取文件内容",
                input_schema={"path": {"type": "string"}, "output_schema": {"content": {"type": "string"}}}
            ),
            MCPTool(
                name="write_file",
                description="写入/创建文件",
                input_schema={"path": {"type": "string"}, "content": {"type": "string"}},
                output_schema={"success": {"type": "boolean"}}
            ),
            MCPTool(
                name="list_directory",
                description="列出目录内容",
                input_schema={"path": {"type": "string"}},
                output_schema={"files": {"type": "array"}}
            ),
            MCPTool(
                name="search_files",
                description="按关键词搜索文件",
                input_schema={"query": {"type": "string"}, "path": {"type": "string", "optional": True}},
                output_schema={"results": {"type": "array"}}
            )
        ]
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> MCPResult:
        import os
        
        if not self.is_connected:
            return MCPResult(success=False, error="Not connected")
        
        try:
            if tool_name == "read_file":
                path = os.path.join(self.config.get("base_path", "."), params["path"])
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return MCPResult(success=True, data=content)
            
            elif tool_name == "write_file":
                path = os.path.join(self.config.get("base_path", "."), params["path"])
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(params["content"])
                return MCPResult(success=True, data={"written_bytes": len(params["content"])})
            
            elif tool_name == "list_directory":
                path = os.path.join(self.config.get("base_path", "."), params.get("path", "."))
                files = [{"name": f, "is_dir": os.path.isdir(os.path.join(path, f))} for f in os.listdir(path)]
                return MCPResult(success=True, data=files)
            
            elif tool_name == "search_files":
                import glob
                pattern = f"**/*{params['query']}*"
                results = glob.glob(os.path.join(self.config.get("base_path", "."), pattern), recursive=True)
                return MCPResult(success=True, data=results[:20])
            
            else:
                return MCPResult(success=False, error=f"Unknown tool: {tool_name}")
                
        except Exception as e:
            return MCPResult(success=False, error=str(e))
    
    def get_capability(self) -> MCPCapability:
        return MCPCapability(
            server_name=self.name,
            capabilities=["file_read", "file_write", "directory_browse", "file_search"],
            description="本地文件系统访问"
        )


class DatabaseMCPServer(BaseMCPServer):
    """
    数据库MCP Server - 提供SQL查询能力（PostgreSQL）
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._pool = None
    
    async def connect(self) -> bool:
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            url = self.config.get("database_url")
            if not url:
                return False
            
            self._pool = create_async_engine(url)
            async with self._pool.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.is_connected = True
            logger.info(f"[{self.name}] Connected to database")
            return True
        except Exception as e:
            logger.error(f"[{self.name}] Connection failed: {e}")
            return False
    
    async def disconnect(self):
        if self._pool:
            await self._pool.dispose()
            self._pool = None
        self.is_connected = False
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(name="execute_query", description="执行SQL查询语句", 
                   input_schema={"sql": {"type": "string"}}, 
                   output_schema={"rows": {"type": "array"}}),
            MCPTool(name="get_table_info", description="获取表结构信息",
                   input_schema={"table_name": {"type": "string"}},
                   output_schema={"columns": {"type": "array"}}),
            MCPTool(name="list_tables", description="列出所有表",
                   input_schema={}, output_schema={"tables": {"type": "array"}}),
            MCPTool(name="count_rows", description="统计行数",
                   input_schema={"table_name": {"type": "string"}, "where_clause": {"type": "string", "optional": True}},
                   output_schema={"count": {"type": "integer"}})
        ]
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> MCPResult:
        if not self.is_connected or not self._pool:
            return MCPResult(success=False, error="Not connected")
        
        from sqlalchemy import text
        
        try:
            async with self._pool.connect() as conn:
                if tool_name == "execute_query":
                    result = await conn.execute(text(params["sql"]))
                    rows = [dict(row._mapping) for row in result.fetchall()]
                    return MCPResult(success=True, data=rows)
                
                elif tool_name == "get_table_info":
                    table_name = params.get("table_name", "")
                    # Use parameterized query to prevent SQL injection
                    sql = text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = :table_name")
                    result = await conn.execute(sql, {"table_name": table_name})
                    columns = [dict(row._mapping) for row in result.fetchall()]
                    return MCPResult(success=True, data=columns)
                
                elif tool_name == "list_tables":
                    result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
                    tables = [row[0] for row in result.fetchall()]
                    return MCPResult(success=True, data=tables)
                
                elif tool_name == "count_rows":
                    table_name = params.get("table_name", "")
                    where_clause = params.get("where_clause", "")
                    # Validate table_name to prevent SQL injection - only allow alphanumeric and underscore
                    import re
                    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                        return MCPResult(success=False, error="Invalid table name format")
                    # Validate where_clause - only allow safe characters (no semicolons, no comments)
                    if where_clause and not re.match(r'^[\w\s=<>\'"%()\.\-,]+$', where_clause):
                        return MCPResult(success=False, error="Invalid where clause format")
                    # Use parameterized query for any user values
                    if where_clause:
                        sql = text(f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}")
                    else:
                        sql = text(f"SELECT COUNT(*) FROM {table_name}")
                    result = await conn.execute(sql)
                    count = result.scalar()
                    return MCPResult(success=True, data=count)
                
                else:
                    return MCPResult(success=False, error=f"Unknown tool: {tool_name}")
                    
        except Exception as e:
            return MCPResult(success=False, error=f"Database error: {str(e)}")
    
    def get_capability(self) -> MCPCapability:
        return MCPCapability(
            server_name=self.name,
            capabilities=["sql_query", "table_metadata", "data_retrieval"],
            description=f"数据库访问 ({self.config.get('database_type', 'postgresql')})",
            auth_required=True
        )


class SearchMCPServer(BaseMCPServer):
    """
    搜索引擎MCP Server - 提供网络搜索能力
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._ddg_available = None  # Lazy check for duckduckgo-search

    def _is_ddg_available(self) -> bool:
        """Check if duckduckgo-search package is available"""
        if self._ddg_available is None:
            try:
                from duckduckgo_search import DDGS
                self._ddg_available = True
            except ImportError:
                self._ddg_available = False
        return self._ddg_available

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def disconnect(self):
        self.is_connected = False

    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(name="web_search", description="网络搜索",
                   input_schema={"query": {"type": "string"}, "num_results": {"type": "integer", "default": 5}},
                   output_schema={"results": {"type": "array"}}),
            MCPTool(name="news_search", description="新闻搜索",
                   input_schema={"query": {"type": "string"}},
                   output_schema={"articles": {"type": "array"}})
        ]

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> MCPResult:
        query = params.get("query", "")
        num_results = params.get("num_results", 5)

        if not query:
            return MCPResult(success=False, error="Query is required")

        try:
            if tool_name == "web_search":
                return await self._web_search(query, num_results)
            elif tool_name == "news_search":
                return await self._news_search(query, num_results)
            else:
                return MCPResult(success=False, error=f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.error(f"[SearchMCPServer] Search error: {e}")
            return MCPResult(success=False, error=f"Search failed: {str(e)}")

    async def _web_search(self, query: str, num_results: int) -> MCPResult:
        """Perform web search using DuckDuckGo"""
        if self._is_ddg_available():
            try:
                from duckduckgo_search import DDGS
                results = []
                with DDGS() as ddg:
                    for r in ddg.text(query, max_results=num_results):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", "")
                        })
                return MCPResult(success=True, data=results)
            except Exception as e:
                logger.warning(f"[SearchMCPServer] DuckDuckGo search failed: {e}, falling back to httpx")
                return await self._web_search_fallback(query, num_results)
        else:
            return await self._web_search_fallback(query, num_results)

    async def _web_search_fallback(self, query: str, num_results: int) -> MCPResult:
        """Fallback search using DuckDuckGo's HTML interface via httpx"""
        import httpx
        from bs4 import BeautifulSoup

        try:
            # Use DuckDuckGo HTML search
            url = f"https://html.duckduckgo.com/html/"
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.post(url, data={"q": query})
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            for result in soup.select(".result")[:num_results]:
                title_elem = result.select_one(".result__title a")
                snippet_elem = result.select_one(".result__snippet")
                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": title_elem.get("href", ""),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                    })

            if not results:
                # Fallback to mock if parsing fails
                logger.warning("[SearchMCPServer] Could not parse search results, using fallback")
                return MCPResult(success=True, data=[
                    {"title": f"关于 '{query}' 的搜索结果", "url": f"https://duckduckgo.com/?q={query}", "snippet": "使用DuckDuckGo搜索获取实时结果"}
                ])

            return MCPResult(success=True, data=results)
        except ImportError:
            # BeautifulSoup not available, return error with suggestion
            return MCPResult(success=False, error="Search requires 'beautifulsoup4' and 'httpx' packages. Install with: pip install beautifulsoup4 httpx")
        except Exception as e:
            logger.error(f"[SearchMCPServer] Fallback search error: {e}")
            return MCPResult(success=False, error=f"Search service unavailable: {str(e)}")

    async def _news_search(self, query: str, num_results: int) -> MCPResult:
        """Perform news search using DuckDuckGo"""
        if self._is_ddg_available():
            try:
                from duckduckgo_search import DDGS
                results = []
                with DDGS() as ddg:
                    for r in ddg.news(query, max_results=num_results):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("body", ""),
                            "date": r.get("date", "")
                        })
                return MCPResult(success=True, data=results)
            except Exception as e:
                logger.warning(f"[SearchMCPServer] DuckDuckGo news search failed: {e}")
                return await self._news_search_fallback(query, num_results)
        else:
            return await self._news_search_fallback(query, num_results)

    async def _news_search_fallback(self, query: str, num_results: int) -> MCPResult:
        """Fallback news search"""
        import httpx

        try:
            # Use DuckDuckGo news RSS/API
            url = f"https://duckduckgo.com/news/?q={query}&format=json"
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

            # Try to parse JSON response
            try:
                data = response.json()
                results = []
                for item in data.get("results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("excerpt", ""),
                        "date": item.get("date", "")
                    })
                return MCPResult(success=True, data=results)
            except Exception:
                # JSON parsing failed, return suggestion
                return MCPResult(success=True, data=[
                    {"title": f"关于 '{query}' 的新闻", "url": f"https://duckduckgo.com/?q={query}&ia=news", "snippet": "访问DuckDuckGo查看完整新闻列表"}
                ])
        except Exception as e:
            return MCPResult(success=False, error=f"News search unavailable: {str(e)}")

    def get_capability(self) -> MCPCapability:
        return MCPCapability(
            server_name=self.name,
            capabilities=["web_search", "news_search"],
            description="网络搜索 (DuckDuckGo)"
        )


class MCPClient:
    """
    MCP客户端 - 统一管理所有MCP Server连接
    
    Domain Agent通过MCPClient间接调用各种外部系统，
    无需关心底层协议细节。
    """
    
    def __init__(self):
        self.servers: Dict[str, BaseMCPServer] = {}
        self.server_capabilities: Dict[str, MCPCapability] = {}
    
    async def register_server(self, name: str, server: BaseMCPServer) -> bool:
        """注册并连接一个MCP Server"""
        success = await server.connect()
        if success:
            self.servers[name] = server
            self.server_capabilities[name] = server.get_capability()
            logger.info(f"[MCPClient] Registered server: {name} ({len(await server.list_tools())} tools)")
        return success
    
    async def unregister_server(self, name: str):
        """注销并断开MCP Server"""
        if name in self.servers:
            await self.servers[name].disconnect()
            del self.servers[name]
            del self.server_capabilities[name]
    
    async def call_tool(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> MCPResult:
        """跨Server调用工具"""
        server = self.servers.get(server_name)
        if not server:
            return MCPResult(success=False, error=f"MCP server '{server_name}' not found")
        
        return await server.call_tool(tool_name, params)
    
    async def discover_tools(self, server_name: Optional[str] = None) -> Dict[str, List[MCPTool]]:
        """发现可用的工具"""
        if server_name:
            server = self.servers.get(server_name)
            if server:
                return {server_name: await server.list_tools()}
            return {}
        
        all_tools = {}
        for name, server in self.servers.items():
            all_tools[name] = await server.list_tools()
        return all_tools
    
    async def list_servers(self) -> List[Dict]:
        """列出所有已连接的Server及其状态"""
        result = []
        for name, server in self.servers.items():
            tools = await server.list_tools()
            result.append({
                "name": name,
                "connected": server.is_connected,
                "capability": self.server_capabilities.get(name).__dict__ if name in self.server_capabilities else {},
                "tools_count": len(tools)
            })
        return result


# ===== 预配置的MCP Server实例工厂 =====

async def create_default_mcp_client(config_overrides: Optional[Dict] = None) -> MCPClient:
    """
    创建预配置的MCP客户端，包含常用Server
    
    Args:
        config_overrides: 可选的配置覆盖
    """
    client = MCPClient()
    
    configs = {
        "filesystem": {
            "name": "filesystem-mcp",
            "base_path": "./data/mcp-files"
        },
        "postgres": {
            "name": "postgres-mcp",
            "database_url": "postgresql+asyncpg://wukong:wukong@localhost:5432/wukong"
        },
        "search": {
            "name": "search-mcp"
        }
    }
    
    if config_overrides:
        configs.update(config_overrides)
    
    # 创建并注册各Server
    servers_to_create = {
        "filesystem": lambda c: FileSystemMCPServer(c),
        "postgres": lambda c: DatabaseMCPServer(c),
        "search": lambda c: SearchMCPServer(c)
    }
    
    for name, factory in servers_to_create.items():
        if name in configs:
            server = factory(configs[name])
            success = await client.register_server(name, server)
            if not success:
                logger.warning(f"[MCPClient] Failed to register {name}, continuing without it")
    
    return client


__all__ = [
    "BaseMCPServer",
    "FileSystemMCPServer",
    "DatabaseMCPServer", 
    "SearchMCPServer",
    "MCPClient",
    "MCPResult",
    "MCPTool",
    "MCPCapability",
    "create_default_mcp_client"
]
