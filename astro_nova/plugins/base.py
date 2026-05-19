"""插件基类 — 所有插件继承此类"""

from astro_nova.tools.registry import Tool, registry


def register_tool(name: str, description: str, parameters: dict):
    """装饰器: 将方法注册为可调用工具"""
    def decorator(func):
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=func,
        )
        func._tool_def = tool
        return func
    return decorator


class BasePlugin:
    """插件基类

    用法:
        class MyPlugin(BasePlugin):
            name = "my-plugin"
            version = "1.0.0"
            description = "我的插件"

            @register_tool("my_tool", "工具描述", {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string", "description": "参数说明"}
                },
                "required": ["arg1"]
            })
            async def my_tool(self, arg1: str) -> str:
                return f"Hello {arg1}"
    """

    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""

    def __init__(self):
        self._tools_registered = False

    async def on_load(self):
        """插件加载时调用"""
        pass

    async def on_unload(self):
        """插件卸载时调用"""
        pass

    def register_tools(self):
        """自动收集并注册所有带 @register_tool 的方法"""
        if self._tools_registered:
            return
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            tool_def = getattr(attr, "_tool_def", None)
            if tool_def:
                # 绑定 self 后重新创建 Tool
                bound_handler = lambda args, attr=attr: attr(**args) if isinstance(args, dict) else attr()
                tool = Tool(
                    name=tool_def.name,
                    description=tool_def.description,
                    parameters=tool_def.parameters,
                    handler=attr,  # 已经 bound (实例方法)
                )
                registry.register(tool)
        self._tools_registered = True

    def unregister_tools(self):
        """卸载所有工具"""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            tool_def = getattr(attr, "_tool_def", None)
            if tool_def:
                registry.unregister(tool_def.name)
        self._tools_registered = False

    def to_dict(self):
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
        }
