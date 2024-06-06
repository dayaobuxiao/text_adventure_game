import random

# 玩家类
class Player:
    def __init__(self):
        self.hp = 100
        self.level = 1
        self.strength = 10
        self.intelligence = 10
        self.endurance = 10
        self.exp = 0
        self.items = []

    def pickup_item(self, item):
        self.items.append(item)

    def gain_exp(self, exp):
        self.exp += exp
        while self.exp >= 100 * self.level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.hp = self.level * 10 + 100
        self.strength += 2
        self.intelligence += 2
        self.endurance += 2
        self.exp -= 100 * (self.level - 1)
        print(f"You leveled up to level {self.level}!")

    def to_json(self):
        return {
            'hp': self.hp,
            'level': self.level,
            'strength': self.strength,
            'intelligence': self.intelligence,
            'endurance': self.endurance,
            'exp': self.exp,
            'items': [item.__dict__ for item in self.items],
        }

# 敌人类
class Enemy:
    def __init__(self, name, hp, strength, intelligence, exp):
        self.name = name
        self.hp = hp
        self.strength = strength
        self.intelligence = intelligence
        self.exp = exp

    def to_json(self):
        return {
            'name': self.name,
            'hp': self.hp,
            'strength': self.strength,
            'intelligence': self.intelligence,
            'exp': self.exp,
        }

# 战斗系统
class Battle:
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy

    def run_battle(self):
        print(f"A {self.enemy.name} appears!")
        while self.player.hp > 0 and self.enemy.hp > 0:
            print(f"Your HP: {self.player.hp}")
            print(f"{self.enemy.name}'s HP: {self.enemy.hp}")
            print("What do you want to do?")
            print("1. Attack")
            print("2. Run")

            choice = input("> ")
            if choice == "1":
                # 攻击
                attack_value = random.randint(1, self.player.strength)
                self.enemy.hp -= attack_value
                print(f"You attack the {self.enemy.name} for {attack_value} damage!")
                if self.enemy.hp <= 0:
                    print(f"You defeated the {self.enemy.name}!")
                    self.player.gain_exp(self.enemy.exp)
                    break
            elif choice == "2":
                # 逃跑
                print("You ran away from the battle.")
                break
            else:
                print("Invalid choice, try again.")

            # 敌人攻击
            enemy_attack_value = random.randint(1, self.enemy.strength)
            self.player.hp -= enemy_attack_value
            print(f"The {self.enemy.name} attacks you for {enemy_attack_value} damage!")
            if self.player.hp <= 0:
                print("You were defeated...")
                break

    def to_json(self):
        return {
            'player': self.player.__dict__,
            'enemy': self.enemy.__dict__,
        }

# 物品类
class Item:
    def __init__(self, name, description, item_type):
        self.name = name
        self.description = description
        self.type = item_type

    def to_json(self):
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type,
        }

# 任务类
class Quest:
    def __init__(self, id, description, reward):
        self.id = id
        self.description = description
        self.reward = reward
        self.completed = False

    def to_json(self):
        return {
            'id': self.id,
            'description': self.description,
            'reward': self.reward,
            'completed': self.completed,
        }

# 任务管理器
class QuestManager:
    def __init__(self):
        self.quests = []
        self.active_quests = []

    def add_quest(self, quest):
        self.quests.append(quest)
        self.active_quests.append(quest)

    def complete_quest(self, quest_id):
        for quest in self.active_quests:
            if quest.id == quest_id:
                quest.completed = True
                self.active_quests.remove(quest)
                print(f"Quest '{quest.description}' completed! Reward: {quest.reward}")
                if "Exp:" in quest.reward:
                    exp = int(quest.reward.split(":")[1])
                    player.gain_exp(exp)
                elif "Item:" in quest.reward:
                    item_name = quest.reward.split(":")[1].strip()
                    item = Item(item_name, f"A reward for completing the quest '{quest.description}'", "reward")
                    player.pickup_item(item)
                break
        else:
            print(f"No quest found with ID {quest_id}")

    def get_active_quests(self):
        return self.active_quests

    def to_json(self):
        return {
            'quests': [quest.__dict__ for quest in self.quests],
            'active_quests': [quest.__dict__ for quest in self.active_quests],
        }

# 地图区域类
class MapArea:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.connections = {}
        self.enemies = []
        self.items = []
        self.quests = []

    def add_connection(self, direction, area_name):
        self.connections[direction] = area_name

    def add_enemy(self, enemy):
        self.enemies.append(enemy)

    def add_item(self, item):
        self.items.append(item)

    def add_quest(self, quest):
        self.quests.append(quest)

    def to_json(self):
        return {
            'name': self.name,
            'description': self.description,
            # 'connections': self.connections,  # Store only the names of the connected areas
            'enemies': [enemy.__dict__ for enemy in self.enemies],
            'items': [item.__dict__ for item in self.items],
            'quests': [quest.__dict__ for quest in self.quests],
        }

# 关卡类
class Level:
    def __init__(self, name, description, start_area):
        self.name = name
        self.description = description
        self.areas = {}
        self.add_area(start_area)
        self.current_area = start_area.name  # Store the name of the current area

    def add_area(self, area):
        self.areas[area.name] = area

    def move_player(self, direction):
        next_area_name = self.current_area.connections.get(direction)
        if next_area_name:
            self.current_area = next_area_name
            print(f"You moved to {self.current_area}.")
            # Add battle, item pickup, and quest logic here
        else:
            print("You cannot go that way.")

    def to_json(self):
        # 将 areas 转换为可以被 JSON 序列化的格式
        areas_json = {name: area.to_json() for name, area in self.areas.items()}
        return {
            'name': self.name,
            'description': self.description,
            'areas': areas_json,
            'current_area': self.current_area,
        }

# 剧情节点类
class StoryNode:
    def __init__(self, description, options):
        self.description = description
        self.options = options

    def to_json(self):
        return {
            'description': self.description,
            'options': self.options,
        }

# 剧情树类
class StoryTree:
    def __init__(self, root):
        self.nodes = {}
        self.root = root
        self.current_node = root

    def add_node(self, node, parent_option):
        self.nodes[node] = parent_option

    def move_to_node(self, option):
        next_node = self.current_node.options.get(option)
        if next_node:
            self.current_node = next_node
            print(self.current_node.description)
            self.present_options()
        else:
            print("Invalid choice.")

    def present_options(self):
        if self.current_node.options:
            print("What would you like to do?")
            for option, node in self.current_node.options.items():
                print(f"{option}. {node.description}")
        else:
            print("There are no more choices to make.")

    def to_json(self):
        # 确保只处理 StoryNode 对象
        nodes_dict = {node.description: node.to_json() for node in self.nodes.values() if isinstance(node, StoryNode)}
        return {
            'nodes': nodes_dict,
            'root': self.root.description,
            'current_node': self.current_node.description,
        }