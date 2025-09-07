# MCP项目框架示例

此项目展示了一个示例的MCP框架，意在帮助开发者快速上手MCP框架。

[FastMCP官方文档](https://gofastmcp.com/servers/context)

## 相关命令

### **启动MCP服务器**

```bash
uv run hw-mcp-shellagent
```

### **构建项目（生成wheel文件）**

```bash
uv build
```

### **使用MCP调试工具并进入开发模式**

注意，所指向的文件必须创建一个名为`mcp`或`server`的实例。

```bash
uv run mcp dev ./src/mcp_shellagent/__main__.py
```

## 相关配置

### **cline配置**（在VSCode中使用）：

```json
{
  "mcpServers": {
    "hw-mcp-shellagent": {
      "disabled": false,
      "timeout": 600,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\henry\\PycharmProjects\\ShellAgent",
        "run",
        "hw-mcp-shellagent"
      ]
    }
  }
}
```

## UV命令

### 添加包W

```bash
uv add <package-name>
```