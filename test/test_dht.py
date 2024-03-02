from src.core.data_service.dht import create_dht, add_node, update_finger_table, create_node

def test_create_dht():
    dht = create_dht()
    assert dht == {"nodes": {}}
    
def test_add_node():
    dht = create_dht()
    add_node(dht, 0)
    assert dht == {"nodes": {0: create_node(0)}}
    
def test_update_finger_table():
    dht = create_dht()
    add_node(dht, 0)
    add_node(dht, 1)
    update_finger_table(dht["nodes"][0])
    assert dht["nodes"][0]["finger_table"] == [dht["nodes"][0]] + [dht["nodes"][1]] * 159
    assert dht["nodes"][1]["finger_table"] == [dht["nodes"][1]] * 160
    assert dht["nodes"][0]["successor"] == dht["nodes"][1]
    assert dht["nodes"][1]["successor"] == dht["nodes"][0]
    add_node(dht, 2)
    update_finger_table(dht["nodes"][0])
    assert dht["nodes"][0]["finger_table"] == [dht["nodes"][0]] + [dht["nodes"][1]] * 159
    assert dht["nodes"][1]["finger_table"] == [dht["nodes"][1]] + [dht["nodes"][2]] * 159
    assert dht["nodes"][2]["finger_table"] == [dht["nodes"][2]] * 160
    
def test_create_node():
    node = create_node(0)
    assert node == {
        "node_id": 0,
        "data": {},
        "successor": node,
        "finger_table": [node] * 160,
        "hash_key": node["node_id"],
        "find_successor": node["find_successor"],
        "store": node["store"],
        "retrieve": node["retrieve"],
        "join": node["join"],
    }
    
def test_find_successor():
    dht = create_dht()
    add_node(dht, 0)
    add_node(dht, 1)
    add_node(dht, 2)
    assert dht["nodes"][0]["find_successor"](0) == dht["nodes"][0]
    assert dht["nodes"][0]["find_successor"](1) == dht["nodes"][1]
    assert dht["nodes"][0]["find_successor"](2) == dht["nodes"][2]
    assert dht["nodes"][0]["find_successor"](3) == dht["nodes"][0]
    assert dht["nodes"][1]["find_successor"](0) == dht["nodes"][0]
    assert dht["nodes"][1]["find_successor"](1) == dht["nodes"][1]
    assert dht["nodes"][1]["find_successor"](2) == dht["nodes"][2]
    assert dht["nodes"][1]["find_successor"](3) == dht["nodes"][0]
    assert dht["nodes"][2]["find_successor"](0) == dht["nodes"][0]
    assert dht["nodes"][2]["find_successor"](1) == dht["nodes"][1]
    assert dht["nodes"][2]["find_successor"](2) == dht["nodes"][2]
    assert dht["nodes"][2]["find_successor"](3) == dht["nodes"][0]
