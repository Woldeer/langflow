import json
import os
from pathlib import Path
import pickle
from typing import Type, Union
from langflow.graph.edge.base import Edge
from langflow.graph.vertex.base import Vertex
from langchain.agents import AgentExecutor
import pytest
from langchain.chains.base import Chain
from langchain.llms.fake import FakeListLLM
from langflow.graph import Graph
from langflow.graph.vertex.types import (
    FileToolVertex,
    LLMVertex,
    ToolkitVertex,
)
from langflow.processing.process import get_result_and_thought
from langflow.utils.payload import get_root_node

# Test cases for the graph module

# now we have three types of graph:
# BASIC_EXAMPLE_PATH, COMPLEX_EXAMPLE_PATH, OPENAPI_EXAMPLE_PATH


def get_node_by_type(graph, node_type: Type[Vertex]) -> Union[Vertex, None]:
    """Get a node by type"""
    return next((node for node in graph.nodes if isinstance(node, node_type)), None)


def test_graph_structure(basic_graph):
    assert isinstance(basic_graph, Graph)
    assert len(basic_graph.nodes) > 0
    assert len(basic_graph.edges) > 0
    for node in basic_graph.nodes:
        assert isinstance(node, Vertex)
    for edge in basic_graph.edges:
        assert isinstance(edge, Edge)
        assert edge.source in basic_graph.nodes
        assert edge.target in basic_graph.nodes


def test_circular_dependencies(basic_graph):
    assert isinstance(basic_graph, Graph)

    def check_circular(node, visited):
        visited.add(node)
        neighbors = basic_graph.get_nodes_with_target(node)
        for neighbor in neighbors:
            if neighbor in visited:
                return True
            if check_circular(neighbor, visited.copy()):
                return True
        return False

    for node in basic_graph.nodes:
        assert not check_circular(node, set())


def test_invalid_node_types():
    graph_data = {
        "nodes": [
            {
                "id": "1",
                "data": {
                    "node": {
                        "base_classes": ["BaseClass"],
                        "template": {
                            "_type": "InvalidNodeType",
                        },
                    },
                },
            },
        ],
        "edges": [],
    }
    with pytest.raises(Exception):
        Graph(graph_data["nodes"], graph_data["edges"])


def test_get_nodes_with_target(basic_graph):
    """Test getting connected nodes"""
    assert isinstance(basic_graph, Graph)
    # Get root node
    root = get_root_node(basic_graph)
    assert root is not None
    connected_nodes = basic_graph.get_nodes_with_target(root)
    assert connected_nodes is not None


def test_get_node_neighbors_basic(basic_graph):
    """Test getting node neighbors"""

    assert isinstance(basic_graph, Graph)
    # Get root node
    root = get_root_node(basic_graph)
    assert root is not None
    neighbors = basic_graph.get_node_neighbors(root)
    assert neighbors is not None
    assert isinstance(neighbors, dict)
    # Root Node is an Agent, it requires an LLMChain and tools
    # We need to check if there is a Chain in the one of the neighbors'
    # data attribute in the type key
    assert any(
        "ConversationBufferMemory" in neighbor.data["type"]
        for neighbor, val in neighbors.items()
        if val
    )

    assert any(
        "OpenAI" in neighbor.data["type"] for neighbor, val in neighbors.items() if val
    )


# def test_get_node_neighbors_complex(complex_graph):
#     """Test getting node neighbors"""
#     assert isinstance(complex_graph, Graph)
#     # Get root node
#     root = get_root_node(complex_graph)
#     assert root is not None
#     neighbors = complex_graph.get_nodes_with_target(root)
#     assert neighbors is not None
#     # Neighbors should be a list of nodes
#     assert isinstance(neighbors, list)
#     # Root Node is an Agent, it requires an LLMChain and tools
#     # We need to check if there is a Chain in the one of the neighbors'
#     assert any("Chain" in neighbor.data["type"] for neighbor in neighbors)
#     # assert Tool is in the neighbors
#     assert any("Tool" in neighbor.data["type"] for neighbor in neighbors)
#     # Now on to the Chain's neighbors
#     chain = next(neighbor for neighbor in neighbors if "Chain" in neighbor.data["type"])
#     chain_neighbors = complex_graph.get_nodes_with_target(chain)
#     assert chain_neighbors is not None
#     # Check if there is a LLM in the chain's neighbors
#     assert any("OpenAI" in neighbor.data["type"] for neighbor in chain_neighbors)
#     # Chain should have a Prompt as a neighbor
#     assert any("Prompt" in neighbor.data["type"] for neighbor in chain_neighbors)
#     # Now on to the Tool's neighbors
#     tool = next(neighbor for neighbor in neighbors if "Tool" in neighbor.data["type"])
#     tool_neighbors = complex_graph.get_nodes_with_target(tool)
#     assert tool_neighbors is not None
#     # Check if there is an Agent in the tool's neighbors
#     assert any("Agent" in neighbor.data["type"] for neighbor in tool_neighbors)
#     # This Agent has a Tool that has a PythonFunction as func
#     agent = next(
#         neighbor for neighbor in tool_neighbors if "Agent" in neighbor.data["type"]
#     )
#     agent_neighbors = complex_graph.get_nodes_with_target(agent)
#     assert agent_neighbors is not None
#     # Check if there is a Tool in the agent's neighbors
#     assert any("Tool" in neighbor.data["type"] for neighbor in agent_neighbors)
#     # This Tool has a PythonFunction as func
#     tool = next(
#         neighbor for neighbor in agent_neighbors if "Tool" in neighbor.data["type"]
#     )
#     tool_neighbors = complex_graph.get_nodes_with_target(tool)
#     assert tool_neighbors is not None
#     # Check if there is a PythonFunction in the tool's neighbors
#     assert any(
#         "PythonFunctionTool" in neighbor.data["type"] for neighbor in tool_neighbors
#     )


def test_get_node(basic_graph):
    """Test getting a single node"""
    node_id = basic_graph.nodes[0].id
    node = basic_graph.get_node(node_id)
    assert isinstance(node, Vertex)
    assert node.id == node_id


def test_build_nodes(basic_graph):
    """Test building nodes"""

    assert len(basic_graph.nodes) == len(basic_graph._nodes)
    for node in basic_graph.nodes:
        assert isinstance(node, Vertex)


def test_build_edges(basic_graph):
    """Test building edges"""
    assert len(basic_graph.edges) == len(basic_graph._edges)
    for edge in basic_graph.edges:
        assert isinstance(edge, Edge)
        assert isinstance(edge.source, Vertex)
        assert isinstance(edge.target, Vertex)


def test_get_root_node(client, basic_graph, complex_graph):
    """Test getting root node"""
    assert isinstance(basic_graph, Graph)
    root = get_root_node(basic_graph)
    assert root is not None
    assert isinstance(root, Vertex)
    assert root.data["type"] == "TimeTravelGuideChain"
    # For complex example, the root node is a ZeroShotAgent too
    assert isinstance(complex_graph, Graph)
    root = get_root_node(complex_graph)
    assert root is not None
    assert isinstance(root, Vertex)
    assert root.data["type"] == "ZeroShotAgent"


def test_validate_edges(basic_graph):
    """Test validating edges"""

    assert isinstance(basic_graph, Graph)
    # all edges should be valid
    assert all(edge.valid for edge in basic_graph.edges)


def test_matched_type(basic_graph):
    """Test matched type attribute in Edge"""
    assert isinstance(basic_graph, Graph)
    # all edges should be valid
    assert all(edge.valid for edge in basic_graph.edges)
    # all edges should have a matched_type attribute
    assert all(hasattr(edge, "matched_type") for edge in basic_graph.edges)
    # The matched_type attribute should be in the source_types attr
    assert all(edge.matched_type in edge.source_types for edge in basic_graph.edges)


def test_build_params(basic_graph):
    """Test building params"""

    assert isinstance(basic_graph, Graph)
    # all edges should be valid
    assert all(edge.valid for edge in basic_graph.edges)
    # all edges should have a matched_type attribute
    assert all(hasattr(edge, "matched_type") for edge in basic_graph.edges)
    # The matched_type attribute should be in the source_types attr
    assert all(edge.matched_type in edge.source_types for edge in basic_graph.edges)
    # Get the root node
    root = get_root_node(basic_graph)
    # Root node is a TimeTravelGuideChain
    # which requires an llm and memory
    assert root is not None
    assert isinstance(root.params, dict)
    assert "llm" in root.params
    assert "memory" in root.params


def test_build(basic_graph):
    """Test Node's build method"""
    assert_agent_was_built(basic_graph)


def assert_agent_was_built(graph):
    """Assert that the agent was built"""
    assert isinstance(graph, Graph)
    # Now we test the build method
    # Build the Agent
    result = graph.build()
    # The agent should be a AgentExecutor
    assert isinstance(result, Chain)


def test_llm_node_build(basic_graph):
    llm_node = get_node_by_type(basic_graph, LLMVertex)
    assert llm_node is not None
    built_object = llm_node.build()
    assert built_object is not None


def test_toolkit_node_build(client, openapi_graph):
    # Write a file to the disk
    file_path = "api-with-examples.yaml"
    with open(file_path, "w") as f:
        f.write("openapi: 3.0.0")

    toolkit_node = get_node_by_type(openapi_graph, ToolkitVertex)
    assert toolkit_node is not None
    built_object = toolkit_node.build()
    assert built_object is not None
    # Remove the file
    os.remove(file_path)
    assert not Path(file_path).exists()


def test_file_tool_node_build(client, openapi_graph):
    file_path = "api-with-examples.yaml"
    with open(file_path, "w") as f:
        f.write("openapi: 3.0.0")

    assert Path(file_path).exists()
    file_tool_node = get_node_by_type(openapi_graph, FileToolVertex)
    assert file_tool_node is not None
    built_object = file_tool_node.build()
    assert built_object is not None
    # Remove the file
    os.remove(file_path)
    assert not Path(file_path).exists()


# def test_wrapper_node_build(openapi_graph):
#     wrapper_node = get_node_by_type(openapi_graph, WrapperVertex)
#     assert wrapper_node is not None
#     built_object = wrapper_node.build()
#     assert built_object is not None


def test_get_result_and_thought(basic_graph):
    """Test the get_result_and_thought method"""
    responses = [
        "Final Answer: I am a response",
    ]
    message = {"input": "Hello"}
    # Find the node that is an LLMNode and change the
    # _built_object to a FakeListLLM
    llm_node = get_node_by_type(basic_graph, LLMVertex)
    assert llm_node is not None
    llm_node._built_object = FakeListLLM(responses=responses)
    llm_node._built = True
    langchain_object = basic_graph.build()
    # assert all nodes are built
    assert all(node._built for node in basic_graph.nodes)
    # now build again and check if FakeListLLM was used

    # Get the result and thought
    result = get_result_and_thought(langchain_object, message)
    assert isinstance(result, dict)


def test_pickle_graph(json_vector_store):
    loaded_json = json.loads(json_vector_store)
    graph = Graph.from_payload(loaded_json)
    assert isinstance(graph, Graph)
    first_result = graph.build()
    assert isinstance(first_result, AgentExecutor)
    pickled = pickle.dumps(graph)
    assert pickled is not None
    unpickled = pickle.loads(pickled)
    assert unpickled is not None
    result = unpickled.build()
    assert isinstance(result, AgentExecutor)


def test_pickle_each_vertex(json_vector_store):
    loaded_json = json.loads(json_vector_store)
    graph = Graph.from_payload(loaded_json)
    assert isinstance(graph, Graph)
    for vertex in graph.nodes:
        vertex.build()
        pickled = pickle.dumps(vertex)
        assert pickled is not None
        unpickled = pickle.loads(pickled)
        assert unpickled is not None
