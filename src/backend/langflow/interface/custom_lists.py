## LLM
from typing import Any

from langchain import llms, requests
from langchain.agents import agent_toolkits
from langchain.llms.openai import OpenAIChat

from langflow.interface.importing.utils import import_class

llm_type_to_cls_dict = llms.type_to_cls_dict
llm_type_to_cls_dict["openai-chat"] = OpenAIChat


## Memory

# from langchain.memory.buffer_window import ConversationBufferWindowMemory
# from langchain.memory.chat_memory import ChatMessageHistory
# from langchain.memory.combined import CombinedMemory
# from langchain.memory.entity import ConversationEntityMemory
# from langchain.memory.kg import ConversationKGMemory
# from langchain.memory.readonly import ReadOnlySharedMemory
# from langchain.memory.simple import SimpleMemory
# from langchain.memory.summary import ConversationSummaryMemory
# from langchain.memory.summary_buffer import ConversationSummaryBufferMemory

memory_type_to_cls_dict: dict[str, Any] = {
    # "CombinedMemory": CombinedMemory,
    # "ConversationBufferWindowMemory": ConversationBufferWindowMemory,
    # "ConversationBufferMemory": ConversationBufferMemory,
    # "SimpleMemory": SimpleMemory,
    # "ConversationSummaryBufferMemory": ConversationSummaryBufferMemory,
    # "ConversationKGMemory": ConversationKGMemory,
    # "ConversationEntityMemory": ConversationEntityMemory,
    # "ConversationSummaryMemory": ConversationSummaryMemory,
    # "ChatMessageHistory": ChatMessageHistory,
    # "ConversationStringBufferMemory": ConversationStringBufferMemory,
    # "ReadOnlySharedMemory": ReadOnlySharedMemory,
}


## Chain
# from langchain.chains.loading import type_to_loader_dict
# from langchain.chains.conversation.base import ConversationChain

# chain_type_to_cls_dict = type_to_loader_dict
# chain_type_to_cls_dict["conversation_chain"] = ConversationChain

toolkit_type_to_loader_dict: dict[str, Any] = {
    toolkit_name: import_class(f"langchain.agents.agent_toolkits.{toolkit_name}")
    # if toolkit_name is lower case it is a loader
    for toolkit_name in agent_toolkits.__all__
    if toolkit_name.islower()
}

toolkit_type_to_cls_dict: dict[str, Any] = {
    toolkit_name: import_class(f"langchain.agents.agent_toolkits.{toolkit_name}")
    # if toolkit_name is not lower case it is a class
    for toolkit_name in agent_toolkits.__all__
    if not toolkit_name.islower()
}


wrapper_type_to_cls_dict: dict[str, Any] = {
    wrapper.__name__: wrapper for wrapper in [requests.RequestsWrapper]
}
