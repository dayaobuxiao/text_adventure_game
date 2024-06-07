import json
import requests
import pickle
from flask import request, session, jsonify, render_template

from app import app
from app.game import Player, Enemy, Level, MapArea, Battle, Quest, QuestManager, StoryNode, StoryTree, Item

# ChatGLM API 的 URL 和密钥
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
API_KEY = "your_api_key"

# 游戏上下文信息
GAME_CONTEXT = """
You are an AI assistant powering a text adventure game. The game has a player character, a map with different areas, quests, enemies, and a story with branching paths.

The player can enter various commands such as "move north", "pickup item", "attack enemy", "complete quest 1", or make choices to advance the story.

You should never break character or reveal that you are an AI. Always respond from the perspective of the game world, describing what happens in response to the player's actions.

The current game state is:
{game_state}
"""

def update_game_state(game_state, response_text):
    # 解析响应文本,更新游戏状态
    words = response_text.split()
    command = words[0].lower()

    if command == "move":
        if len(words) > 1:
            direction = words[1].lower()
            game_state["level"].move_player(direction)
        else:
            print("Please specify a direction to move.")

    elif command == "pickup":
        if len(words) > 1:
            item_name = " ".join(words[1:])
            items = [item for item in game_state["level"].current_area.items if item.name.lower() == item_name.lower()]
            if items:
                item = items[0]
                game_state["player"].pickup_item(item)
                game_state["level"].current_area.items.remove(item)
                print(f"You picked up the {item.name}.")
            else:
                print(f"There is no '{item_name}' to pick up.")
        else:
            print("Please specify an item to pick up.")

    elif command == "attack":
        if game_state["level"].current_area.enemies:
            enemy = game_state["level"].current_area.enemies[0]
            battle = Battle(game_state["player"], enemy)
            battle.run_battle()
            if enemy.hp <= 0:
                game_state["level"].current_area.enemies.remove(enemy)
        else:
            print("There are no enemies to attack in this area.")

    elif command == "complete":
        if len(words) > 1:
            quest_id = int(words[1])
            game_state["quest_manager"].complete_quest(quest_id)
        else:
            print("Please specify a quest ID to complete.")

    elif command == "story":
        if len(words) > 1:
            choice = words[1]
            game_state["story_tree"].move_to_node(choice)
        else:
            game_state["story_tree"].present_options()

    else:
        print(f"Invalid command: {response_text}")

    return game_state

def default_encode(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

@app.route('/', methods=['GET', 'POST'])
def index():
    # Load game state from session
    game_state = session.get('game_state')

    # 创建游戏实例
    # If the game state is not set, create a new game instance
    if game_state is None:
        player = Player()
        quest_manager = QuestManager()

        forest_area = MapArea("Forest", "You find yourself in a dense forest.")
        cave_area = MapArea("Cave", "You enter a dark and damp cave.")
        forest_area.add_connection("north", cave_area)
        cave_area.add_connection("south", forest_area)

        goblin = Enemy("Goblin", 20, 5, 2, 10)
        forest_area.add_enemy(goblin)

        healing_potion = Item("Healing Potion", "A potion that restores HP", "consumable")
        forest_area.add_item(healing_potion)

        quest1 = Quest(1, "Slay the goblin king", "Exp: 100")
        quest2 = Quest(2, "Collect 10 bear pelts", "Item: Fur Cloak")
        quest3 = Quest(3, "Explore the cave", "Exp: 50")
        quest_manager.add_quest(quest1)
        quest_manager.add_quest(quest2)
        cave_area.add_quest(quest3)

        level1 = Level("The Haunted Woods", "An ancient forest shrouded in mystery.", forest_area)

        start_node = StoryNode("You wake up in a forest, unsure of how you got here...", {
            "1": StoryNode("1. You decide to explore the forest.", {}),
            "2": StoryNode("2. You head north towards a cave.", {})
        })

        story_tree = StoryTree(start_node)
        story_tree.add_node(start_node.options["1"], "1")
        story_tree.add_node(start_node.options["2"], "2")

        game_state = {
            'player': player,
            'level': level1,
            'story_tree': story_tree,
            'quest_manager': quest_manager,
        }

        # Save the new game state to the session
        session['game_state'] = json.dumps(game_state, default=default_encode)

    if request.method == 'POST':
        user_input = request.form['user_input']

        # 准备 ChatGLM API 请求的数据
        game_state_str = json.dumps(game_state, default=default_encode)
        data = {
            "model": "glm-4",
            "messages": [
                {"role": "system", "content": GAME_CONTEXT.format(game_state=game_state_str)},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 500,
            "temperature": 0.7,
            "stop": ["stop_generating"]
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        # 发送请求到 ChatGLM API
        response = requests.post(API_URL, headers=headers, json=data)
        print(response.json())
        result = response.json()["choices"][0]["message"]["content"].strip()
        # 处理游戏响应并更新游戏状态
        print(f"Bot: {result}")
        game_state = update_game_state(game_state, result)
        # Save the updated game state to the session
        session['game_state'] = json.dumps(game_state, default=default_encode)
        # Send data to front-end
        game_state_json = {
            'player': json.dumps(game_state['player'].to_json(), default=default_encode),
            'level': json.dumps(game_state['level'].to_json(), default=default_encode),
            'story_tree': json.dumps(game_state['story_tree'].to_json(), default=default_encode),
            'quest_manager': json.dumps(game_state['quest_manager'].to_json(), default=default_encode),
        }
        data = {
            'game_state': game_state_json,
            'result': result
        }
        return jsonify(data)
    elif request.method == 'GET':
        # 确保game_state不是None，然后渲染模板
        return render_template('index.html', game_state=game_state)
    else:
        # 其他请求就报错
        return "An error occurred. Please try again later.", 500

@app.before_request
def load_game_state():
    # 在每个请求之前加载游戏状态
    if 'game_state' not in session:
        session['game_state'] = None

    if session['game_state'] is not None:
        try:
            request.game_state = pickle.loads(session['game_state'])
        except (pickle.UnpicklingError, AttributeError, TypeError):
            # 如果无法unpickle游戏状态,则重置为None
            session['game_state'] = None

@app.teardown_request
def save_game_state(exception=None):
    # 在每个请求之后保存游戏状态
    if 'game_state' in session:
        try:
            # Use pickle.dumps to serialize the game state to bytes
            session['game_state'] = pickle.dumps(session['game_state'])
        except pickle.PicklingError:
            # 如果无法pickle游戏状态,则不保存
            session['game_state'] = None
