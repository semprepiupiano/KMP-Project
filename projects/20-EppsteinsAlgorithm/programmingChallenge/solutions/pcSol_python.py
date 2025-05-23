import sys
from heapq import heappush, heappop
from collections import deque

# For an "infinity" weight cost
INF = float('inf')

def dijkstra(g, src, pred):
    """
    Standard Dijkstra's algorithm on graph g from source src.
    Also fills pred[] with the predecessor of each node on the shortest-path tree.
    Returns distance array d[].
    """
    n = len(g)
    d = [INF] * n       # initialize distances to infinity
    d[src] = 0          # distance from src to itself is zero
    pq = [(0, src)]     # min-heap of (distance, node)

    while pq:
        du, u = heappop(pq)
        if du != d[u]:   # stale entry in heap
            continue
        for w, v in g[u]:
            nd = du + w
            if nd < d[v]:
                d[v] = nd
                pred[v] = u
                heappush(pq, (nd, v))
    return d

class HeapNode:
    """
    Leftist heap node to manage deviations from the shortest-path tree.
    Stores a "key" (cost difference), the origin node, and the child node.
    """
    def __init__(self, key, origin, value, left=None, right=None):
        self.key = key        # additional cost to take this deviation
        self.origin = origin  # node where deviation starts
        self.value = value    # destination of this deviation
        self.left = left      # left child in leftist heap
        self.right = right    # right child in leftist heap
        # rank of a leftist heap is 1 + min(rank(left), rank(right))
        self.rank = 1 + min(self._rank(left), self._rank(right))

    @staticmethod
    def _rank(h):
        return 0 if h is None else h.rank

    @staticmethod
    def merge(a, b):
        """
        Merge two leftist heaps rooted at a and b, returning the new root.
        Ensures the smaller key is at the root, then fixes the leftist property.
        """
        if a is None:
            return b
        if b is None:
            return a
        # ensure a has the smaller key
        if b.key < a.key:
            a, b = b, a
        # merge b into the right subtree of a
        a.right = HeapNode.merge(a.right, b)
        # enforce leftist property (rank(left) >= rank(right))
        if HeapNode._rank(a.left) < HeapNode._rank(a.right):
            a.left, a.right = a.right, a.left
        # update rank
        a.rank = 1 + HeapNode._rank(a.right)
        return a

    @staticmethod
    def insert(h, key, origin, value):
        """
        Insert a new deviation (key, origin->value) into heap h.
        """
        node = HeapNode(key, origin, value)
        return HeapNode.merge(h, node)

    def __lt__(self, other):
        # break ties in the priority queue by comparing keys
        return self.key < other.key


def shortest_paths_no_same_arrival(g, src, dst, k):
    """
    Computes the k-th shortest path distance from src to dst, disallowing
    two paths that arrive at dst at the same total distance.
    Uses simplificaiton of Eppstein's algorithm with leftist heaps for efficiency.
    Returns the k-th shortest distance, along with the sidetrack edges taken.
    """
    n = len(g)

    # Build reverse graph for running Dijkstra from dst
    revg = [[] for _ in range(n)]
    for u in range(n):
        for w, v in g[u]:
            revg[v].append((w, u))

    # Compute distances from dst to all nodes and record predecessors
    pred = [-1] * n
    d = dijkstra(revg, dst, pred)
    # if src can't reach dst, return -1
    if d[src] == INF:
        return -1

    # Build the shortest-path tree (edges where pred[u] -> u)
    tree = [[] for _ in range(n)]
    for u in range(n):
        if pred[u] != -1:
            tree[pred[u]].append(u)

    # Build deviation heaps for each node
    h = [None] * n
    queue = deque([dst])
    while queue:
        u = queue.popleft()
        seenp = False
        # for each outgoing edge u->v, compute its extra cost
        for w, v in g[u]:
            if d[v] == INF:
                continue
            diff = w + d[v] - d[u]
            # skip the tree edge with zero extra cost once
            if not seenp and v == pred[u] and diff == 0:
                seenp = True
                continue
            h[u] = HeapNode.insert(h[u], diff, u, v)
        # propagate heap reference to tree children
        for v in tree[u]:
            h[v] = h[u]
            queue.append(v)

    # Gather k shortest paths, starting with the shortest path
    # for each path, store the distance and the sidetrack edges taken
    results = [(d[src], [])]

    if h[src] is None:
        # if no sidetrack is available, return the shortest path
        return results[0]

    pq = [(d[src] + h[src].key, h[src], [])]
    # Extract next-best deviations until we have k distances
    while pq and len(results) < k:
        cd, node, path = heappop(pq)

        # add this sidetrack to the path
        new_path = path + [(node.origin, node.value)]

        if cd > results[-1][0]:
            results.append((cd, new_path))

        # push further deviations from this node
        if h[node.value] is not None:
            heappush(pq, (cd + h[node.value].key, h[node.value], new_path))
        if node.left:
            heappush(pq, (cd + node.left.key - node.key, node.left, path))
        if node.right:
            heappush(pq, (cd + node.right.key - node.key, node.right, path))

    # return the k-th shortest path
    return results[-1]

def get_kth_shortest_path(g, src, dst, k):
    """
    Returns the k-th shortest path from src to dst in graph g.
    The path is represented as a list of nodes.
    """
    # Compute the shortest path predecessor tree
    n = len(g)
    revg = [[] for _ in range(n)]
    for u in range(n):
        for w, v in g[u]:
            revg[v].append((w, u))
    pred = [-1] * n
    d = dijkstra(revg, dst, pred)
    if d[src] == INF:
        return []

    # Get the sidetracks used in the k-th shortest path
    sidetracks_used = shortest_paths_no_same_arrival(g, src, dst, k)[1]

    # Reconstruct the path from src to dst using the sidetracks and predecessors
    path = []
    u = src
    while u != dst:
        path.append(u)
        if sidetracks_used and sidetracks_used[0][0] == u:
            u = sidetracks_used[0][1]
            sidetracks_used.pop(0)
        else:
            u = pred[u]
    path.append(dst)

    # Return the path
    return path


def main():
    data = sys.stdin.buffer
    n, m, s, t, k = map(int, data.readline().split())
    g = [[] for _ in range(n)]
    for _ in range(m):
        u, v, w = map(int, data.readline().split())
        g[u].append((w, v))

    path = get_kth_shortest_path(g, s, t, k)
    if path:
        print(" ".join(map(str, path)))
    else:
        print(-1)

if __name__ == '__main__':
    main()
