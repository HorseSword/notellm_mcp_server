""" 
可用于加载 MCP 工具，并对外提供 API 服务。

用法：
uv run mcp_server.py
"""

from fastmcp import FastMCP
from fastmcp import Client
import json 
from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel
import asyncio 
from contextlib import asynccontextmanager
import argparse
import time 
from openai import OpenAI
import uvicorn

#%% ================ =================== ==================== =====================
#
# 在 mcp_config.json 文件中，定义需要使用的 MCP 工具
with open('mcp_config.json','r', encoding='utf-8') as f:
    mcp_config = json.load(f)

client = Client(mcp_config)

server_data = {
    "lst_tools": None,
    'lst_desc': None,  # 
    'dict_groups': {},
}

lst_desc = []
dict_desc = {}
for tool_head in mcp_config.get("mcpServers"):
    is_active = mcp_config["mcpServers"][tool_head].get("isActive",True)
    if is_active:
        tool_desc = mcp_config["mcpServers"][tool_head].get("description","(no description)")
        lst_desc.append(f"'{tool_head}': {tool_desc}")
        # print(f"tool_head = {tool_head}, tool_desc = {tool_desc}")
        dict_desc[tool_head] = tool_desc
server_data['lst_desc'] = lst_desc
server_data['dict_groups'] = dict_desc

#%% ================ =================== ==================== =====================
#
async def startup_event():
    async with client:
        lst_tools = await client.list_tools()
    print('lst_tools inited.')
    return lst_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    global server_data
    async with client:
        server_data["lst_tools"] = await client.list_tools()  # 初始化操作
    print('server_data inited.')
    print(server_data)
    yield
    # Clean up the ML models and release the resources
    server_data.clear()

app = FastAPI(lifespan=lifespan)
#
@app.head("/")
def check_health_head():
    """
    专门处理 HEAD 请求，不返回任何内容体。
    """
    # 直接返回一个 Response 对象，状态码为 200
    return Response(status_code=200)

#%% 
# ================ =================== ==================== =====================
#
@app.get("/mcp/list_tools")
async def get_list_tools():
    if server_data["lst_tools"] is None:
        async with client:
            server_data["lst_tools"] = await client.list_tools()
    else:
        pass
    return {"tools": server_data["lst_tools"]}


@app.get("/mcp/get_tools")
async def get_openai_api_tools(tool_group:str=''):
    """ 
    返回 openai-api tool_call 格式的工具列表。
    
    参数 tool_group 是只返回特定字符开头的工具列表。

    返回值：{
        "tools": [{"type":"function", "function":xxx}, ...]
    }
    """
    if server_data["lst_tools"] is None:
        async with client:
            server_data["lst_tools"] = await client.list_tools()
    else:
        pass
    lst_mcp_tools = server_data["lst_tools"]
    #
    if len(server_data['lst_desc']) <= 1:  # 这里有些简单暴力，存在遗留bug，之后检查
        RETURN_ALL = True
    else:
        RETURN_ALL = False
    #
    openai_tools = []
    lst_group = [str(x).strip() for x in tool_group.split(',') if len(str(x).strip())>0]
    print(f"lst_group = {lst_group}")
    #
    # 如果有 group 传入，就返回对应分组的工具列表
    if len(lst_group) > 0:  
        if lst_group[0] == 'all':        # 返回所有工具 
            # 遍历原始数据中的每一个工具
            for mcp_tool_definition in lst_mcp_tools:
                # 构建符合 OpenAI 格式的工具结构
                    openai_tool_definition = {
                        "type": "function",
                        "function": {
                            "name": mcp_tool_definition.name,
                            "description": mcp_tool_definition.description,
                            "parameters": mcp_tool_definition.inputSchema, # 'inputSchema' 的内容可以直接作为 'parameters' 的值
                        }
                    }
                    openai_tools.append(openai_tool_definition)
        else:
            for group_name in lst_group:  # 对于每个工具组
                #
                # 特殊处理： 要求用 agent 模式运行的
                if group_name.endswith('_agent'):  # 比如 math_agent
                    # 获取 agent 功能
                    agent_info = server_data['dict_groups'].get(group_name,'')
                    #
                    openai_tool_definition = {
                        "type": "function",
                        "function": {
                            "name": group_name,
                            "description": " \n".join([
                                agent_info,
                                '如果前文已经提供查询结果, 可以不必重复提问。',
                                '参数 task: 你的查询语句。'
                            ]),
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "task":{
                                        "type": "string",
                                        "description": "Input the main tasks that need to be handled by agent. Remember to provide necessary supplementary information to solve the problem more accurately."
                                    }
                                },
                                "required": ["task"]
                            }
                        }
                    }
                    openai_tools.append(openai_tool_definition)
                #
                # 正常的工具组
                else:
                    for mcp_tool_definition in lst_mcp_tools:  # 遍历所有工具
                        if str(mcp_tool_definition.name).startswith(group_name):  # 只返回目标分组的工具
                            openai_tool_definition = {
                                "type": "function",
                                "function": {
                                    "name": mcp_tool_definition.name,
                                    "description": mcp_tool_definition.description,
                                    "parameters": mcp_tool_definition.inputSchema,  # 'inputSchema' 的内容可以直接作为 'parameters' 的值
                                }
                            }
                            openai_tools.append(openai_tool_definition)
                            # break # 添加之后用不用看其余分组了
            # 这里最好再去重，还没写
    #
    # 没有传入分组请求时
    else:  
        # 返回所有工具
        if RETURN_ALL:  
            # 遍历原始数据中的每一个工具
            for mcp_tool_definition in lst_mcp_tools:
                # 构建符合 OpenAI 格式的工具结构
                    openai_tool_definition = {
                        "type": "function",
                        "function": {
                            "name": mcp_tool_definition.name,
                            "description": mcp_tool_definition.description,
                            "parameters": mcp_tool_definition.inputSchema, # 'inputSchema' 的内容可以直接作为 'parameters' 的值
                        }
                    }
                    openai_tools.append(openai_tool_definition)
        #
        # 返回引导词
        else:  
            openai_tool_definition = {
                "type": "function",
                "function": {
                    "name": 'get_tool_groups',
                    "description": 'Get tools from groups to use them. Important: function name is "get_tool_groups", and arguments should be "group_names" only.',
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "group_names":{
                                "type": "string",
                                "description": "\n ".join([
                                    "group_names: 工具集的名称，调用后可以获得工具集内部的具体工具与用法，以便进一步使用。如果需要多个工具集，用英文逗号隔开。可选值：",
                                    ] + server_data['lst_desc']
                                )
                            }
                        },
                        "required": ["group_names"]
                    }
                }
            }
            openai_tools.append(openai_tool_definition)

    # return {"tools": json.dumps(openai_tools, ensure_ascii=False)}
    return {"tools": openai_tools}

@app.get("/mcp/get_agents")
async def get_agents():
    """ 
    返回 openai-api tool_call 格式的 agents 列表。

    返回值：{
        "tools": list
    }
    """
    lst_agents = []
    openai_tool_definition = {
        "type": "function",
        "function": {
            "name": 'call_agents',
            "description": '通过询问特定领域的 AI Agent, 以获得相对专业的结果。如果前文已经提供，可以不必重复提问。调用时, agent_id 与 task 均为必填参数，两个参数全都要提交才能正常调用。',
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id":{
                        "type": "string",
                        "description": "\n\n ".join([
                            "Agent ID. Choose one from following:",
                            ] + server_data['lst_desc']
                        )
                    },
                    "task":{
                        "type": "string",
                        "description": "Input the main tasks that need to be handled by agent. Remember to provide necessary supplementary information to solve the problem more accurately."
                    }
                },
                "required": ["agent_id", "task"]
            }
        }
    }
    lst_agents.append(openai_tool_definition)
    return {"tools": lst_agents}


class AgentCallQuest(BaseModel):
    agent_id: str
    task: str

@app.post("/mcp/call_agent")
async def call_one_agent(call_quest:AgentCallQuest):
    """ 
    call one AI agent.
    """
    # 获取工具列表
    res_tools = await get_openai_api_tools(tool_group=call_quest.agent_id)
    #
    # 调用LLM
    try:
        from openai_config import AGENT_OPENAI_KEY, AGENT_OPENAI_URL, AGENT_OPENAI_MODEL
        openai_client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key = AGENT_OPENAI_KEY,
            base_url = AGENT_OPENAI_URL
        )
        messages = [
            {"role": "system", "content": "\n ".join([
                "You are a professional AI assistant, you should help user with tools.",
                "When you use tools and meet errors, try to solve them first.",
                "But if you can not solve the problem with tools and given messages, tell user directly.",
                "Reply in simple way, do not use emoji, and do not ask for more after your reply."
            ])},
            {"role": "user", "content": f"{call_quest.task}"}
        ]
        lst_tools = res_tools.get("tools")
        print(f"[call_one_agent] lst_tools = {lst_tools}", flush=True)
        completion = openai_client.chat.completions.create(
            model= AGENT_OPENAI_MODEL,
            messages=messages,
            tools=lst_tools,
            temperature=0,
            stream = False,
        )
        #
        # 调用工具
        finish_reason = completion.choices[0].finish_reason
        call_cnt = 1
        call_cnt_max = 5
        while finish_reason in ['tool_calls']:
            lst_call = [{"name":x.function.name, "arguments":x.function.arguments} for x in completion.choices[0].message.tool_calls]
            lst_call_result = []
            for one_call in lst_call:
                one_result = await call_one_tool(ToolCallQuest(name=one_call['name'], arguments=one_call['arguments']))
                lst_call_result.append({"role":"system", "content": f"tool_call result = {one_result}"})
            #
            call_cnt += 1
            messages = messages + lst_call_result
            #
            if call_cnt < call_cnt_max:   
                completion = openai_client.chat.completions.create(
                    model= AGENT_OPENAI_MODEL,
                    messages = messages,
                    tools=lst_tools,
                    temperature=0,
                    stream = False,
                )
            else:
                completion = openai_client.chat.completions.create(
                    model= AGENT_OPENAI_MODEL,
                    messages = messages,
                    temperature=0,
                    stream = False,
                )
            finish_reason = completion.choices[0].finish_reason
        #
        if finish_reason in ['stop']:
            ai_result = completion.choices[0].message.content
    #
    except Exception as e:
        ai_result = f"Error = {e}"
    #
    finally:
        # 返回结果
        return ai_result

#%%
#
class ToolCallQuest(BaseModel):
    name: str
    arguments: str = None

@app.post("/mcp/call_tool")
async def call_one_tool(call_quest:ToolCallQuest):
    """
    用于执行工具，并返回执行结果。

    工具的调用请求，需要包括 name 和 arguments 两个键，而且都是字符串。

    每次请求只能调用一个工具，如果有多个工具，需要逐个调用。

    返回值：{ 
        'name': 'string', 
        'arguments': 'string',
        'result': 'json_to_string'
        }
    """
    SLEEP_SEC = 0.5  # 强行等待，防止返回过快，导致某些大模型API限流，如果不需要可以去掉
    #
    print('call_quest.name = ',call_quest.name, flush=True)
    print('call_quest.arguments = ',call_quest.arguments, flush=True)
    parsed_args = json.loads(call_quest.arguments)
    #
    try:
        if type(parsed_args) not in [dict]: # 输入参数不是键值对的情况下
            res_tools = 'arguments error!'
        #
        elif call_quest.name in ['get_tool_groups']:  # 仅用于获取工具组
            group_names = parsed_args.get("group_names","")
            res_tools = await get_openai_api_tools(group_names)
        #
        elif call_quest.name in ['call_agents']:  # 调用智能体
            agent_id = parsed_args.get("agent_id")
            task = parsed_args.get("task")
            res_tools = await call_one_agent(AgentCallQuest(agent_id=agent_id, task=task))
        #
        elif call_quest.name.endswith('_agent'):
            agent_id = call_quest.name + '_' # 保证结尾不是 agent 即可
            print(f"agent_id = {agent_id}", flush=True)
            task = parsed_args.get("task")
            res_tools = await call_one_agent(AgentCallQuest(agent_id=agent_id, task=task))
        #
        else:  # 标准工具调用
            try:
                async with client:
                    res_tools = await client.call_tool(name=call_quest.name, arguments=parsed_args)
                    # 得到的是 CallToolResult 对象，还需要调整为文本
                    try:
                        res_tools = res_tools.content[0].text
                    except Exception as e:
                        print(f"Error = {e}")
                        res_tools = str(res_tools)
            except Exception as e:
                res_tools = f"ERROR = {e}"
    except Exception as e:
        res_tools = f"Error = {e}"
    #
    # return res_tools 
    try:
        dict_result = {
            'name': call_quest.name,
            'arguments': parsed_args,
            'result': res_tools
        }
        json_dumpes_result = json.dumps(dict_result, ensure_ascii= False)
    except:
        dict_result = {
            'name': call_quest.name,
            'arguments': parsed_args,
            'result': str(res_tools)
        }
        json_dumpes_result = json.dumps(dict_result, ensure_ascii= False)
    finally:
        print(f"json_dumpes_result = {json_dumpes_result}")
        if not call_quest.name in ['get_tool_groups']:
            time.sleep(SLEEP_SEC)  # 防止返回过快，导致某些大模型API限流
        else:
            time.sleep(SLEEP_SEC)  # 防止返回过快，导致某些大模型API限流
        return json_dumpes_result


#%% ================ =================== ==================== =====================
#
if __name__ == "__main__":
    #
    parser = argparse.ArgumentParser(description="MCP转换器")
    parser.add_argument("--mode", default="api", help="Run mode, http, sse, stdio, api(default)")
    parser.add_argument("--host", default='127.0.0.1', help="Server IP")
    parser.add_argument("--port", default=7302, help="Server port number")
    args = parser.parse_args()

    RUN_MODE = args.mode  # 'fastapi'  # fastapi bridge
    SERVER_HOST = args.host  # '127.0.0.1'
    SERVER_PORT = args.port  # 7302
    #
    # uv run mcp_api.py --mode api
    #
    if RUN_MODE in ['http', 'bridge',]:
        """ 
        代理 MCP 服务，并对外提供 http 模式的接口
        """
        # http://host:port/mcp
        remote_proxy = FastMCP.as_proxy(
            client,
            name="MCP_Http_Bridge"
        )
        remote_proxy.run(transport="http", host=SERVER_HOST, port=SERVER_PORT)
    #
    elif RUN_MODE in ['sse']:
        """ 
        代理 MCP 服务，并对外提供 http 模式的接口
        """
        # http://host:port/sse
        remote_proxy = FastMCP.as_proxy(
            client,
            name="MCP_SSE_Bridge"
        )
        remote_proxy.run(transport="sse", host=SERVER_HOST, port=SERVER_PORT)
    #
    elif RUN_MODE in ['stdio']:
        """ 
        直接提供 stdio 模式的服务
        """
        remote_proxy = FastMCP.as_proxy(
            client,
            name="MCP_Stdio_Bridge"
        )
        remote_proxy.run(transport="stdio")
    #
    elif RUN_MODE in ['api', 'fastapi', ]:
        """ 
        以 Fastapi 的方式对外提供 MCP 的网络 API 服务。
        """
        # import uvicorn
        uvicorn.run("mcp_server:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
    #
    else:
        print("Param 'mode' is incorrect.")
        pass

