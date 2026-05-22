from utils import *
from example import example_use_of_gym_env
from gymnasium.envs.registration import register
from minigrid.envs.doorkey import DoorKeyEnv


class DoorKey10x10Env(DoorKeyEnv):
    """
    Inputs:
        kwargs: arguments passed to DoorKeyEnv

    Output:
        A 10x10 DoorKey environment

    Creates a custom 10x10 DoorKey environment.
    """
    def __init__(self, **kwargs):
        super().__init__(size=10, **kwargs)


register(
    id='MiniGrid-DoorKey-10x10-v0',
    entry_point='__main__:DoorKey10x10Env'
)


MF = 0  # Move Forward
TL = 1  # Turn Left
TR = 2  # Turn Right
PK = 3  # Pickup Key
UD = 4  # Unlock Door


def build_state_space(height, width):
    """
    Inputs:
        height: height of the map
        width: width of the map

    Output:
        state_space: list of all possible states

    Builds the state space for Part A with one key and one door.
    """
    state_space = []

    for h in range(height):
        for w in range(width):
            for direction in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                for has_key in [0, 1]:
                    for door_open in [0, 1]:
                        state_space.append((w, h, direction, has_key, door_open))

    return state_space


def build_state_space_B(height, width):
    """
    Inputs:
        height: height of the map
        width: width of the map

    Output:
        state_space: list of all possible states

    Builds the state space for Part B with two doors and multiple possible key/goal positions.
    """
    state_space = []

    for h in range(height):
        for w in range(width):
            for direction in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                for has_key in [0, 1]:
                    for door_open_1 in [0, 1]:
                        for door_open_2 in [0, 1]:
                            for key_pos in [(2, 2), (2, 3), (1, 6)]:
                                for goal_pos in [(6, 1), (7, 3), (6, 6)]:
                                    state_space.append(
                                        (
                                            w, h, direction, has_key,
                                            door_open_1, door_open_2,
                                            key_pos, goal_pos
                                        )
                                    )

    return state_space


def out_of_bounds(x, y, width, height):
    """
    Inputs:
        x: x-coordinate
        y: y-coordinate
        width: map width
        height: map height

    Output:
        True if the position is outside the map, otherwise False

    Checks whether a position is outside the grid.
    """
    return x >= width or x < 0 or y >= height or y < 0


def get_walls(env):
    """
    Inputs:
        env: MiniGrid environment

    Output:
        walls: set of wall positions

    Extracts wall locations from the environment.
    """
    walls = set()

    for y in range(env.unwrapped.height):
        for x in range(env.unwrapped.width):
            cell = env.grid.get(x, y)

            if cell is not None and cell.type == "wall":
                walls.add((x, y))

    return walls


def valid_action(state, action, info):
    """
    Inputs:
        state: current Part A state
        action: action being checked
        info: map information dictionary

    Output:
        True if the action is valid, otherwise False

    Checks whether an action is allowed in Part A.
    """
    x, y, direction, has_key, door_open = state
    dir_x, dir_y = direction

    front_pos = (x + dir_x, y + dir_y)

    if action == MF:
        if out_of_bounds(front_pos[0], front_pos[1], info["width"], info["height"]):
            return False

        if front_pos in info["wall_pos"]:
            return False

        if front_pos == tuple(info["door_pos"]) and door_open == 0:
            return False

        return True

    if action == PK:
        return front_pos == tuple(info["key_pos"]) and has_key == 0

    if action == UD:
        return front_pos == tuple(info["door_pos"]) and has_key == 1 and door_open == 0

    # Turning is always valid
    return True


def valid_action_B(state, action):
    """
    Inputs:
        state: current Part B state
        action: action being checked

    Output:
        True if the action is valid, otherwise False

    Checks whether an action is allowed in Part B.
    """
    x, y, direction, has_key, d1, d2, key_pos, goal_pos = state
    dir_x, dir_y = direction

    front_pos = (x + dir_x, y + dir_y)

    if action == MF:
        if out_of_bounds(front_pos[0], front_pos[1], 10, 10):
            return False

        if is_wall_B(front_pos):
            return False

        # Closed doors block forward motion
        if front_pos == (5, 3) and d1 == 0:
            return False

        if front_pos == (5, 7) and d2 == 0:
            return False

        return True

    if action == PK:
        return front_pos == key_pos and has_key == 0

    if action == UD:
        if front_pos == (5, 3):
            return has_key == 1 and d1 == 0

        if front_pos == (5, 7):
            return has_key == 1 and d2 == 0

        return False

    # Turning is always valid
    return True


def pf(state, action, info):
    """
    Inputs:
        state: current Part A state
        action: action to apply
        info: map information dictionary

    Output:
        next_state: state after applying the action

    Computes the deterministic transition for Part A.
    """
    x, y, direction, has_key, door_open = state
    width, height = info["width"], info["height"]
    door_pos = tuple(info["door_pos"])
    key_pos = tuple(info["key_pos"])

    dir_x, dir_y = direction[0], direction[1]

    if action == MF:
        nx, ny = x + dir_x, y + dir_y

        if out_of_bounds(nx, ny, width, height):
            return state

        if (nx, ny) == door_pos and door_open == 0:
            return state

        x, y = nx, ny

    elif action == TL:
        TL_map = {
            (1, 0): (0, -1),
            (0, -1): (-1, 0),
            (-1, 0): (0, 1),
            (0, 1): (1, 0),
        }
        direction = TL_map[direction]

    elif action == TR:
        TR_map = {
            (1, 0): (0, 1),
            (0, 1): (-1, 0),
            (-1, 0): (0, -1),
            (0, -1): (1, 0),
        }
        direction = TR_map[direction]

    elif action == PK:
        front_pos = (x + dir_x, y + dir_y)

        if front_pos == key_pos and has_key == 0:
            has_key = 1

    elif action == UD:
        front_pos = (x + dir_x, y + dir_y)

        if front_pos == door_pos and has_key == 1 and door_open == 0:
            door_open = 1

    next_state = (x, y, direction, has_key, door_open)
    return next_state


def pf_B(state, action):
    """
    Inputs:
        state: current Part B state
        action: action to apply

    Output:
        next_state: state after applying the action

    Computes the deterministic transition for Part B.
    """
    x, y, direction, has_key, d1, d2, key_pos, goal_pos = state
    dir_x, dir_y = direction

    if action == MF:
        nx, ny = x + dir_x, y + dir_y

        if out_of_bounds(nx, ny, 10, 10):
            return state

        if is_wall_B((nx, ny)):
            return state

        if (nx, ny) == (5, 3) and d1 == 0:
            return state

        if (nx, ny) == (5, 7) and d2 == 0:
            return state

        x, y = nx, ny

    elif action == TL:
        direction = {
            (1, 0): (0, -1),
            (0, -1): (-1, 0),
            (-1, 0): (0, 1),
            (0, 1): (1, 0)
        }[direction]

    elif action == TR:
        direction = {
            (1, 0): (0, 1),
            (0, 1): (-1, 0),
            (-1, 0): (0, -1),
            (0, -1): (1, 0)
        }[direction]

    elif action == PK:
        if (x + dir_x, y + dir_y) == key_pos:
            has_key = 1

    elif action == UD:
        front = (x + dir_x, y + dir_y)

        if front == (5, 3):
            d1 = 1

        elif front == (5, 7):
            d2 = 1

    next_state = (x, y, direction, has_key, d1, d2, key_pos, goal_pos)
    return next_state


def l(action):
    """
    Inputs:
        action: selected action

    Output:
        cost: stage cost of the action

    Returns the cost for each action.
    """
    if action in [TL, TR]:
        return 1

    elif action == PK:
        return 2

    elif action == MF:
        return 3

    elif action == UD:
        return 5


def q(state, info):
    """
    Inputs:
        state: current Part A state
        info: map information dictionary

    Output:
        terminal cost: 0 at the goal, infinity otherwise

    Computes the terminal cost for Part A.
    """
    x, y, direction, has_key, door_open = state
    goal_pos = tuple(info["goal_pos"])

    return 0 if (x, y) == goal_pos else float("inf")


def q_B(state):
    """
    Inputs:
        state: current Part B state

    Output:
        terminal cost: 0 at the goal, infinity otherwise

    Computes the terminal cost for Part B.
    """
    x, y, direction, has_key, door1_open, door2_open, key_pos, goal_pos = state

    return 0 if (x, y) == goal_pos else float("inf")


def dpa_B(state_space, control_space, pf_B, l, T):
    """
    Inputs:
        state_space: list of all possible Part B states
        control_space: list of possible actions
        pf_B: Part B transition function
        l: stage cost function
        T: planning horizon

    Outputs:
        policy: optimal action for each state and time
        V: value function for each state and time

    Runs backward dynamic programming for Part B.
    """
    V = [{} for _ in range(T + 1)]
    policy = [{} for _ in range(T)]

    # Initialize terminal value
    for state in state_space:
        V[T][state] = q_B(state)

    # Work backwards from time T-1 to 0
    for t in range(T - 1, -1, -1):
        converged = True

        for state in state_space:
            if q_B(state) == 0:
                V[t][state] = 0
                policy[t][state] = None
            else:
                Q = {}

                # Evaluate each valid action
                for action in control_space:
                    if not valid_action_B(state, action):
                        continue

                    next_state = pf_B(state, action)
                    Q[action] = l(action) + V[t + 1][next_state]

                # Pick the action with minimum cost
                min_action = min(Q, key=Q.get)
                V[t][state] = Q[min_action]
                policy[t][state] = min_action

            # Check convergence for every state
            if V[t][state] != V[t + 1][state]:
                converged = False

        if converged:
            print("Converged at t =", t)
            return policy, V

    return policy, V


def dpa(state_space, control_space, p0, pf, l, T, info):
    """
    Inputs:
        state_space: list of all possible Part A states
        control_space: list of possible actions
        p0: initial state
        pf: Part A transition function
        l: stage cost function
        T: planning horizon
        info: map information dictionary

    Outputs:
        policy: optimal action for each state and time
        V: value function for each state and time

    Runs backward dynamic programming for Part A.
    """
    V = [{} for _ in range(T + 1)]
    policy = [{} for _ in range(T)]

    # Initialize terminal value
    for state in state_space:
        V[T][state] = q(state, info)

    # Work backwards from time T-1 to 0
    for t in range(T - 1, -1, -1):
        converged = True

        for state in state_space:
            if q(state, info) == 0:
                V[t][state] = 0
                policy[t][state] = None
            else:
                Q = {}

                # Evaluate each valid action
                for action in control_space:
                    if not valid_action(state, action, info):
                        continue

                    next_state = pf(state, action, info)
                    Q[action] = l(action) + V[t + 1][next_state]

                # Pick the action with minimum cost
                min_action = min(Q, key=Q.get)
                V[t][state] = Q[min_action]
                policy[t][state] = min_action

            # Check convergence for every state
            if V[t][state] != V[t + 1][state]:
                converged = False

        if converged:
            print("Converged at t =", t)
            return policy, V

    return policy, V


def is_wall_B(pos):
    """
    Inputs:
        pos: grid position as (x, y)

    Output:
        True if the position is a wall, otherwise False

    Checks whether a position is a wall in the Part B map.
    """
    x, y = pos

    # Perimeter walls
    if x == 0 or x == 9 or y == 0 or y == 9:
        return True

    # Vertical wall at column 5, except at the two door positions
    if x == 5 and pos not in [(5, 3), (5, 7)]:
        return True

    return False


def get_action_sequence(policy, p0, pf, T, info):
    """
    Inputs:
        policy: computed Part A policy
        p0: initial state
        pf: Part A transition function
        T: planning horizon
        info: map information dictionary

    Output:
        seq: list of actions from start to goal

    Extracts an action sequence by following the Part A policy.
    """
    seq = []
    state = p0

    for t in range(T):
        action = policy[t][state]

        if action is None:
            break

        seq.append(action)
        state = pf(state, action, info)

        if q(state, info) == 0:
            break

    return seq


def get_action_sequence_B(policy, p0, pf_B, T):
    """
    Inputs:
        policy: computed Part B policy
        p0: initial state
        pf_B: Part B transition function
        T: planning horizon

    Output:
        seq: list of actions from start to goal

    Extracts an action sequence by following the Part B policy.
    """
    seq = []
    state = p0

    # Find first usable policy time
    start_t = None

    for t in range(T):
        if state in policy[t]:
            start_t = t
            break

    if start_t is None:
        print("p0 not found in any policy")
        return seq

    for t in range(start_t, T):
        action = policy[t][state]

        if action is None:
            break

        seq.append(action)
        state = pf_B(state, action)

        if q_B(state) == 0:
            break

    return seq


def partA():
    """
    Inputs:
        None

    Output:
        None

    Solves the known DoorKey maps and saves GIFs for Part A.
    """
    env_path = "./envs/"
    known_envs = "known_envs/doorkey-"

    known_maps = [
        "5x5-normal.env",
        "6x6-normal.env",
        "6x6-direct.env",
        "6x6-shortcut.env",
        "8x8-normal.env",
        "8x8-direct.env",
        "8x8-shortcut.env"
    ]

    control_space = [MF, TL, TR, PK, UD]

    for map in known_maps:
        env, info = load_env(env_path + known_envs + map)

        info["wall_pos"] = get_walls(env)

        state_space = build_state_space(info["height"], info["width"])

        # Get initial door status
        door = env.grid.get(info["door_pos"][0], info["door_pos"][1])
        door_open = 1 if door.is_open else 0

        # Get whether the agent initially has the key
        has_key = 1 if env.carrying is not None else 0

        p0 = (
            env.agent_pos[0],
            env.agent_pos[1],
            tuple(env.dir_vec),
            has_key,
            door_open
        )

        T = len(state_space)

        policy, V = dpa(state_space, control_space, p0, pf, l, T, info)

        seq = get_action_sequence(policy, p0, pf, T, info)

        draw_gif_from_seq(seq, env, path=f"./gif/known_{map}.gif")


def partB():
    """
    Inputs:
        None

    Output:
        None

    Solves the random DoorKey maps using one shared Part B policy and saves GIFs.
    """
    env_path = "./envs/"
    random_envs = "random_envs/"
    control_space = [MF, TL, TR, PK, UD]

    state_space = build_state_space_B(10, 10)
    T = len(state_space)

    # Compute one policy that covers all possible key and goal positions
    policy, V = dpa_B(state_space, control_space, pf_B, l, T)

    for i in range(1, 37):
        env_file = f"DoorKey-10x10-{i}.env"
        env, info = load_env(env_path + random_envs + env_file)

        door1 = env.grid.get(5, 3)
        door2 = env.grid.get(5, 7)

        door1_open = 1 if door1.is_open else 0
        door2_open = 1 if door2.is_open else 0

        key_pos = tuple(map(int, info["key_pos"]))
        goal_pos = tuple(map(int, info["goal_pos"]))

        p0 = (
            4, 8, (0, -1),
            0,
            door1_open,
            door2_open,
            key_pos,
            goal_pos
        )

        seq = get_action_sequence_B(policy, p0, pf_B, T)

        print("map:", env_file)
        print("p0:", p0)
        print("seq:", seq)
        print("cost:", sum(l(a) for a in seq))
        print()

        draw_gif_from_seq(seq, env, path=f"./gif/random_{i}.gif")


def main():
    """
    Inputs:
        None

    Output:
        None

    Runs both Part A and Part B.
    """
    partA()
    partB()


if __name__ == "__main__":
    main()
