from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils import cal_utils
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroEntry
from zzz_od.hollow_zero.hollow_map.hollow_zero_map import HollowZeroMap, HollowZeroMapNode
from one_dragon.yolo.detect_utils import DetectFrameResult


def construct_map_from_yolo_result(detect_result: DetectFrameResult, name_2_entry: dict[str, HollowZeroEntry]) -> HollowZeroMap:
    """
    根据识别结果构造地图
    """
    nodes: List[HollowZeroMapNode] = []
    unknown = name_2_entry['未知']

    for result in detect_result.results:
        entry_name = result.detect_class.class_name[5:]
        if entry_name in name_2_entry:
            entry = name_2_entry[entry_name]
        else:
            entry = unknown

        width = result.x2 - result.x1
        height = result.y2 - result.y1
        if entry.is_base:
            pos = Rect(result.x1, result.y2 - width, result.x2, result.y2)
        else:
            pos = Rect(result.x1, result.y1, result.x2, result.y2 + height // 3)

        # 判断与已有的节点是否重复
        to_merge: Optional[HollowZeroMapNode] = None
        for existed in nodes:
            min_dis = min(pos.height, pos.width, existed.pos.height, existed.pos.width) // 2
            if cal_utils.distance_between(pos.center, existed.pos.center) < min_dis:
                to_merge = existed
                break

        if to_merge is not None:
            if to_merge.entry.is_base and not entry.is_base:  # 旧的是底座 那么将新的类型赋值上去
                to_merge.entry = entry
                to_merge.pos.y1 = pos.y1  # 使用具体类型的坐标
            elif not to_merge.entry.is_base and entry.is_base:  # 旧的是格子类型 那么把底座的范围赋值上去
                to_merge.pos.x1 = pos.x1
                to_merge.pos.x2 = pos.x2
                to_merge.pos.y2 = pos.y2
            else:
                pass
        else:
            node = HollowZeroMapNode(pos, entry,
                                     check_time=detect_result.run_time,
                                     confidence=result.score)
            nodes.append(node)

    for node in nodes:
        if node.entry.is_base:  # 只识别到底座的 赋值为未知
            node.entry = unknown

    return construct_map_from_nodes(nodes, detect_result.run_time)


def construct_map_from_nodes(nodes: List[HollowZeroMapNode], check_time: float) -> HollowZeroMap:
    current_idx: Optional[int] = None
    for i in range(len(nodes)):
        if nodes[i].entry.entry_name == '当前':
            current_idx = i

    edges: dict[int, List[int]] = {}

    for i in range(len(nodes)):
        for j in range(len(nodes)):
            node_1 = nodes[i]
            node_2 = nodes[j]

            if not node_1.entry.can_go or not node_2.entry.can_go:
                continue

            if _at_left(node_1, node_2):  # 1在2左边
                if node_2.entry.entry_name in ['轨道-左']:
                    pass
                elif node_1.entry.entry_name in ['轨道-上', '轨道-下', '轨道-左']:
                    pass
                else:
                    _add_directed_edge(edges, i, j)
            elif _at_right(node_1, node_2):  # 1在2右边
                if node_2.entry.entry_name in ['轨道-右']:
                    pass
                elif node_1.entry.entry_name in ['轨道-上', '轨道-下', '轨道-右']:
                    pass
                else:
                    _add_directed_edge(edges, i, j)
            elif _above(node_1, node_2):  # 1在2上边
                if node_2.entry.entry_name in ['轨道-上']:
                    pass
                elif node_1.entry.entry_name in ['轨道-左', '轨道-右', '轨道-上']:
                    pass
                else:
                    _add_directed_edge(edges, i, j)
            elif _under(node_1, node_2):  # 1在2下边
                if node_2.entry.entry_name in ['轨道-下']:
                    pass
                elif node_1.entry.entry_name in ['轨道-左', '轨道-右', '轨道-下']:
                    pass
                else:
                    _add_directed_edge(edges, i, j)

    return HollowZeroMap(nodes, current_idx, edges, check_time=check_time)


def _at_left(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2左边
    :param node_1:
    :param node_2:
    :return:
    """
    min_width = min(node_1.pos.width,  node_2.pos.width) // 4
    return abs(node_1.pos.x2 - node_2.pos.x1) <= min_width and _is_same_row(node_1, node_2)


def _at_right(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2右边
    :param node_1:
    :param node_2:
    :return:
    """
    min_width = min(node_1.pos.width,  node_2.pos.width) // 4
    return abs(node_1.pos.x1 - node_2.pos.x2) <= min_width and _is_same_row(node_1, node_2)


def _above(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2上边
    :param node_1:
    :param node_2:
    :return:
    """
    min_height = min(node_1.pos.height,  node_2.pos.height) // 4
    return abs(node_1.pos.y2 - node_2.pos.y1) <= min_height and _is_same_col(node_1, node_2)


def _under(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    """
    1在2上边
    :param node_1:
    :param node_2:
    :return:
    """
    min_height = min(node_1.pos.height,  node_2.pos.height) // 4
    return abs(node_1.pos.y1 - node_2.pos.y2) <= min_height and _is_same_col(node_1, node_2)


def _is_same_row(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    min_height = min(node_1.pos.height,  node_2.pos.height) // 3
    y1_close = abs(node_1.pos.y1 - node_2.pos.y1) <= min_height
    y2_close = abs(node_1.pos.y2 - node_2.pos.y2) <= min_height
    return y1_close or y2_close


def _is_same_col(node_1: HollowZeroMapNode, node_2: HollowZeroMapNode) -> bool:
    min_width = min(node_1.pos.width,  node_2.pos.width) // 3
    x1_close = abs(node_1.pos.x1 - node_2.pos.x1) <= min_width
    x2_close = abs(node_1.pos.x2 - node_2.pos.x2) <= min_width
    return x1_close or x2_close


def _add_edge(edges: dict[int, List[int]], x: int, y: int) -> None:
    _add_directed_edge(edges, x, y)
    _add_directed_edge(edges, y, x)


def _add_directed_edge(edges: dict[int, List[int]], x: int, y: int) -> None:
    if x not in edges:
        edges[x] = [y]
    else:
        edges[x].append(y)


def merge_map(map_list: List[HollowZeroMap]):
    """
    将多个地图合并成一个
    """
    nodes: List[HollowZeroMapNode] = []
    max_check_time: Optional[float] = None

    # 每个地图的节点取出来后去重合并
    for m in map_list:
        for node in m.nodes:
            to_merge: Optional[HollowZeroMapNode] = None
            for existed in nodes:
                if cal_utils.distance_between(node.pos.center, existed.pos.center) < 100:
                    to_merge = existed
                    break

            if to_merge is not None:
                if to_merge.entry.is_base:  # 旧的是底座 那么将新的类型赋值上去
                    to_merge.entry = node.entry
                elif node.entry.is_base:  # 旧的是格子类型 新的是底座 将底座范围赋值上去
                    to_merge.pos = node.pos
                elif to_merge.entry.entry_name == '未知' and node.entry.entry_name != '未知':  # 旧的是格子类型 新的也是格子类型 旧的是未知 将新的类型赋值上去
                    to_merge.entry = node.entry
                elif to_merge.check_time < node.check_time:  # 旧的是格子类型 新的也是格子类型 新的识别时间更晚 将新的类型赋值上去
                    to_merge.entry = node.entry
            else:
                nodes.append(node)

        if max_check_time is None or m.check_time > max_check_time:
            max_check_time = m.check_time

    return construct_map_from_nodes(nodes, max_check_time)


class RouteSearchRoute:

    def __init__(self, node: HollowZeroMapNode, node_idx: int,
                 first_node: Optional[HollowZeroMapNode],
                 first_need_step_node: HollowZeroMapNode,
                 step_cnt: int, distance: float):
        self.node: HollowZeroMapNode = node  # 需要前往的节点
        self.node_idx: int = node_idx  # 需要前往的节点的下标
        self.first_node: HollowZeroMapNode = first_node  # 路径上的第一个节点 就是当前节点的相邻节点
        self.first_need_step_node: HollowZeroMapNode = first_need_step_node  # 路径上的第一个需要步数的节点 就是鼠标需要点击的节点
        self.step_cnt: int = step_cnt  # 前往目标节点需要的步数 即路上需要点击多少次鼠标
        self.distance: float = distance  # 在画面上 目标节点与当前节点的像素距离；用于步数相同时选一个更近的


def search_map(current_map: HollowZeroMap, avoid_entry_list: set[str]) -> dict[int, RouteSearchRoute]:
    """
    对当前地图进行搜索 获取前往每个节点的路径
    :param current_map: 识别到的地图信息
    :param: avoid_entry_list: 避免途经点
    :return:
    """
    if current_map is None or current_map.current_idx is None:
        return {}

    start_node_idx = current_map.current_idx
    start_node = current_map.nodes[start_node_idx]
    start_route = RouteSearchRoute(start_node, start_node_idx,
                                   None, start_node,
                                   0, 0)

    # 先避开部分节点进行搜索 例如战斗的节点
    result_1 = _bfs_search_map(current_map, [start_route], avoid_entry_list)
    start_routes = [i for i in result_1.values()]

    # 可能存在部分节点 一定要经过[避免途经点]才能到达
    # 因此 在上述搜索结果上 继续搜索剩余节点的路径
    result_2 = _bfs_search_map(current_map, start_routes, None)

    return result_2


def _bfs_search_map(
        current_map: HollowZeroMap,
        start_routes: List[RouteSearchRoute],
        avoid_entry_list: Optional[set[str]] = None
) -> dict[int, RouteSearchRoute]:
    """
    使用宽度搜索 找到达地图上每一个节点的最短路径
    :param current_map: 识别到的地图信息
    :param start_routes: 起始的路径：在第1次搜索时，只有当前节点；第2次搜索时，会包含第1次搜索的路径结果
    :param avoid_entry_list: 避免途经点
    :return:
    """
    result: dict[int, RouteSearchRoute] = {}

    bfs_queue: List[int] = []  # 当前层的节点下标
    searched: set[int] = set()  # 已经搜索过的节点下标
    for start_route in start_routes:
        current_idx = start_route.node_idx
        bfs_queue.append(current_idx)
        searched.add(current_idx)
        result[current_idx] = start_route

    # 宽度搜索 每层先搜索不需要移动步数的；再搜索需要移动步数的
    while len(bfs_queue) > 0:
        next_bfs_queue: List[int] = []  # 下一层
        bfs_idx = 0  # 遍历当前层的节点
        while bfs_idx < len(bfs_queue):  # 注意当前层bfs_queue会不断加入不需要步数的节点 因此用这个while
            current_idx = bfs_queue[bfs_idx]
            current_route = result[current_idx]
            current_node = current_route.node
            current_node_idx = current_route.node_idx
            searched.add(current_idx)
            bfs_idx += 1  # 标记这个节点已经处理 下一次循环需要处理下一个节点的

            if current_node_idx not in current_map.edges:  # 这个节点没有边 即没有可以移动的节点
                continue

            for next_idx in current_map.edges[current_node_idx]:  # 遍历这个节点的边 找到可以移动的节点
                if next_idx in searched:  # 这个可以移动的节点 已经被搜索过
                    continue

                next_node = current_map.nodes[next_idx]
                next_entry = next_node.entry

                if not next_entry.can_go:  # 无法移动
                    continue
                if avoid_entry_list is not None and next_entry.entry_name in avoid_entry_list:  # 避免途经点
                    continue

                # 根据节点类型 计算前往下一个节点的步数
                next_step_cnt = current_route.step_cnt + (next_entry.need_step if next_entry is not None else 1)
                # 判断这条路径上 第一个需要步数的节点是哪个 即需要点击的节点
                if next_step_cnt <= 1 and next_entry.need_step > 0:
                    first_need_step_node = next_node
                else:
                    first_need_step_node = current_route.first_need_step_node

                # 构建前往下一个节点的路径
                next_route = RouteSearchRoute(
                    node=next_node,
                    node_idx=next_idx,
                    first_node=next_node if current_route.first_node is None else current_route.first_node,
                    first_need_step_node=first_need_step_node,
                    step_cnt=next_step_cnt,
                    distance=cal_utils.distance_between(current_node.pos.center, next_node.pos.center)
                )

                if next_step_cnt == current_route.step_cnt:  # 相同步数 就加入当前层 继续搜索
                    if next_idx in bfs_queue:  # 已经在当前队列
                        pass
                    elif next_idx in next_bfs_queue:  # 在下一层的队列 移动
                        next_bfs_queue.remove(next_idx)
                        bfs_queue.append(next_idx)
                        result[next_idx] = next_route
                    else:  # 都不在 放入当前的队列
                        bfs_queue.append(next_idx)
                        result[next_idx] = next_route
                else:  # 步数增加的 就加入下一层 等待后续搜索
                    if next_idx not in next_bfs_queue:
                        next_bfs_queue.append(next_idx)
                        result[next_idx] = next_route

        bfs_queue = next_bfs_queue

    return result


def get_route_in_1_step(idx_2_route: dict[int, RouteSearchRoute],
                        visited_nodes: List[HollowZeroMapNode],
                        target_entry_list: Optional[List[str]] = None) -> Optional[RouteSearchRoute]:
    """
    获取1步能到的节点的路径
    :param idx_2_route: 路径搜索结果 key=节点下标 value=前往该节点的路径
    :param visited_nodes: 已经去过的节点 就不会再去了
    :param target_entry_list: 传入时 只考虑前往这些限定格子类型
    :return:
    """
    target: Optional[RouteSearchRoute] = None
    for idx, route in idx_2_route.items():
        if route.step_cnt != 1:  # 筛选只需要1步前往的路径
            continue

        entry = route.node.entry  # 目标节点的类型
        if target_entry_list is not None and entry.entry_name not in target_entry_list:  # 不符合目标类型
            continue

        if had_been_visited(route.node, visited_nodes):  # 曾经尝试去过了
            continue

        if target is None or target.distance > route.distance:  # 有多个候选时 优先选择画面上离当前节点最近的
            target = route

    return target

def get_route_by_entry(idx_2_route: dict[int, RouteSearchRoute],
                       entry_name: str,
                       visited_nodes: List[HollowZeroMapNode]) -> Optional[RouteSearchRoute]:
    """
    找一条最短的 能到达目标类型格子的 路径
    :param idx_2_route: 路径搜索结果 key=节点下标 value=前往该节点的路径
    :param entry_name: 需要前往的格子类型
    :param visited_nodes: 已经尝试去过的格子
    :return:
    """
    target: Optional[RouteSearchRoute] = None
    for idx, route in idx_2_route.items():
        node = route.node
        entry = route.node.entry
        if entry is None or entry.entry_name != entry_name:
            continue

        if had_been_visited(node, visited_nodes):
            continue

        # 有多个候选时 优先选择步数最少的
        # 步数一致时 优选选择画面上离当前节点最近的
        if (target is None
                or target.step_cnt > route.step_cnt
                or (target.step_cnt == route.step_cnt and target.distance > route.distance)):
            target = route

    return target


def get_route_by_direction(idx_2_route: dict[int, RouteSearchRoute], direction: str) -> Optional[RouteSearchRoute]:
    """
    找一条最远的 符合目标方向的 路径
    主要用于兜底情况 按副本类型找一个方向前进
    :param idx_2_route: 路径搜索结果 key=节点下标 value=前往该节点的路径
    :return:
    """
    target: Optional[RouteSearchRoute] = None
    for idx, route in idx_2_route.items():
        if route.node.entry.entry_name in ['当前', '空白已通行', '空白未通行']:
            continue

        # 根据各个方向 找到最远的格子
        if target is None:
            target = route
        elif direction == 'w' and target.node.pos.y1 > route.node.pos.y1:
            target = route
        elif direction == 's' and target.node.pos.y2 < route.node.pos.y2:
            target = route
        elif direction == 'a' and target.node.pos.x1 > route.node.pos.x1:
            target = route
        elif direction == 'd' and target.node.pos.x2 < route.node.pos.x2:
            target = route

    return target


def had_been_visited(current: HollowZeroMapNode, visited_nodes: List[HollowZeroMapNode]) -> bool:
    """
    判断节点是否已经尝试前往过了
    部分节点允许多次尝试前往 (例如 业绩考察点) 避免各种奇怪的情况错过
    """
    for visited in visited_nodes:
        if visited.gt_max_visited_times and is_same_node(current, visited):
            return True
    return False


def is_same_node(x: HollowZeroMapNode, y: HollowZeroMapNode) -> bool:
    """
    判断两个节点是否同一个节点
    """
    if x is None or y is None:
        return False
    min_dis = min(x.pos.height, x.pos.width, y.pos.height, y.pos.width) // 2
    return x.entry.entry_name == y.entry.entry_name and cal_utils.distance_between(x.pos.center, y.pos.center) < min_dis


def draw_map(screen: MatLike, current_map: HollowZeroMap,
             next_node: Optional[HollowZeroMapNode] = None,
             idx_2_route: Optional[dict[int, RouteSearchRoute]] = None) -> MatLike:
    """
    在图上画出地图
    :param screen:
    :param current_map:
    :return:
    """
    import cv2
    to_draw = screen.copy()

    for node in current_map.nodes:
        cv2.rectangle(to_draw, (node.pos.x1, node.pos.y1), (node.pos.x2, node.pos.y2), (255, 0, 0), 2)

    for i, j_list in current_map.edges.items():
        for j in j_list:
            if j > i:
                node_1 = current_map.nodes[i]
                node_2 = current_map.nodes[j]
                cv2.line(to_draw, node_1.pos.center.tuple(), node_2.pos.center.tuple(),
                         (0, 255, 0), 2)

    if idx_2_route is not None:
        for idx, route in idx_2_route.items():
            # 在对应坐标是显示idx
            node = current_map.nodes[idx]
            msg = f'{route.node.entry.entry_id} : {route.step_cnt}'
            cv2.putText(to_draw, msg, (node.pos.left_top + Point(0, 20)).tuple(), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 255), 2)
        for idx in range(len(current_map.nodes)):
            if idx in idx_2_route:
                continue
            node = current_map.nodes[idx]
            msg = f'{node.entry.entry_id} : -1'
            cv2.putText(to_draw, msg, (node.pos.left_top + Point(0, 20)).tuple(), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 255), 2)

    if next_node is not None:
        cv2.circle(to_draw, next_node.pos.center.tuple(), 20, (0, 0, 255), 2)

    return to_draw
