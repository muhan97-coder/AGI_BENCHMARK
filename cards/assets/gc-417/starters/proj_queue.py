"""proj_queue: stable priority queue (gc-417 starter; seeded defects)."""


def new_queue():
    return {"items": [], "pushes": 0}


def push(q, item, priority):
    q["items"].append((priority, item))
    q["pushes"] += 1


def pop(q):
    if not q["items"]:
        raise IndexError("empty queue")
    best = max(range(len(q["items"])),
               key=lambda i: (q["items"][i][0], i))
    return q["items"].pop(best)[1]


def peek(q):
    return pop(q)


def qsize(q):
    return q["pushes"]
