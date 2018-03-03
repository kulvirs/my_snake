import bottle
import os
import random
import heapq
#from priodict import priorityDictionary

class Logic:
    def __init__(self):
        self.last_dir = ''

    def opposite(self,dir):
        if dir == 'left':
            return 'right'
        if dir == 'right':
            return 'left'
        if dir == 'up':
            return 'down'
        if dir == 'down':
            return 'up'
        else:
            return None

class Graph:
    def __init__(self):
        self.vertices = {}
        self.x_range = self.y_range = 0

    def create(self,x,y):
        self.x_range = x
        self.y_range = y
        for i in range(x):
            for j in range(y):
                self.vertices[(i,j)] = Vertex(i,j,EMPTY)

    def neighbours(self,coords):
        vertex = self.vertices[coords]
        dirs = [[1,0],[0,1],[-1,0],[0,-1]]
        result = []
        for dir in dirs:
            neighbour_coords = (vertex.x + dir[0], vertex.y+dir[1])
            if 0 <= neighbour_coords[0] < self.x_range and 0 <= neighbour_coords[1] < self.y_range:
                neighbour = self.vertices[neighbour_coords]
                if neighbour.vertex_type != OCCUPIED:
                    result.append(neighbour)
        return result

    def clear(self,food_list,occupied_list):
        for vertex in food_list:
            vertex.vertex_type = EMPTY
        for vertex in occupied_list:
            vertex.vertex_type = EMPTY

class Vertex:
    def __init__(self,x,y,vertex_type):
        self.x = x
        self.y = y
        self.vertex_type = vertex_type

logic = Logic()
graph = Graph()

@bottle.route('/')
def static():
    return "the server is running"


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data.get('game_id')
    board_width = data.get('width')
    board_height = data.get('height')

    graph.create(board_width,board_height)

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    return {
        'color': '#00FF00',
        'taunt': '{} ({}x{})'.format(game_id, board_width, board_height),
        'head_url': head_url
    }

def get_food_vertices(food_data):
    food_vertices = []
    for food_item in food_data:
        x = food_item['x']
        y = food_item['y']
        food_vertex = graph.vertices[(x,y)]
        food_vertex.vertex_type = FOOD
        food_vertices.append(food_vertex)
    return food_vertices

def update_vertices(resp):
    snake_vertices = []
    snakes = resp['snakes']['data']
    for snake in snakes:
        for point in snake['body']['data']:
            x = point['x']
            y = point['y']
            point_vertex = graph.vertices[(x,y)]
            point_vertex.vertex_type = OCCUPIED
            snake_vertices.append(point_vertex)
    return snake_vertices

def get_head(resp):
    point = resp['you']['body']['data'][0]
    x = point['x']
    y = point['y']
    return graph.vertices[(x,y)]

def get_closest_food(food_vertices,head):
    if len(food_vertices) == 1:
        return food_vertices[0]
    min_length = graph.x_range + graph.y_range + 1
    min_index = -1
    for i,vertex in enumerate(food_vertices):
        distance = abs(vertex.x - head.x) + abs(vertex.y - head.y)
        if distance < min_length:
            min_length = distance
            min_index = i
    return food_vertices[min_index]

def find_shortest_path(source,dest):
    neighbours = graph.neighbours((source.x,source.y))
    if len(neighbours) == 0:
        print("Got trapped")
        return(source) #what to do here?
    min_dist = graph.x_range + graph.y_range + 1
    min_index = 0
    for i,neighbour in enumerate(neighbours):
        distance = abs(neighbour.x-dest.x) + abs(neighbour.y-dest.y)
        if distance < min_dist:
            min_dist = distance
            min_index = i
    return neighbours[min_index]

def Dijkstra_shortest_path(source,dest):
    dist = {source: 0}
    prev = {source: None}
    visited = []
    Q = [] #PQ
    heapq.heappush(Q,(dist[source],source))

    for vertex in graph.vertices.values():
        if vertex.vertex_type != OCCUPIED and vertex != source:
            dist[vertex] = float('inf')
            prev[vertex] = None
            #heapq.heappush(Q,(dist[vertex],vertex))

    while Q:
        dist_u,u = heapq.heappop(Q)
        if u not in visited:
            visited.append(u)
            if u == dest:
                print("got to destination")
                while prev[u] != source:
                    u = prev[u]
                return u
            for neighbour in graph.neighbours((u.x,u.y)):
                alt = dist[u] + 1 #all weights are 1
                if alt < dist[neighbour]:
                    dist[neighbour] = alt
                    prev[neighbour] = u
                    if neighbour not in visited:
                        heapq.heappush(Q,(dist[neighbour],neighbour))
    print("did not reach destination with Dijkstra")
    return find_shortest_path(source,dest) #see if maybe Euclidean distance can find path



def get_direction(head,next):
    x_diff = next.x-head.x
    y_diff = next.y-head.y
    if x_diff == 0:
        if y_diff == 1:
            return 'down'
        elif y_diff == -1:
            return 'up'
    elif y_diff == 0:
        if x_diff == 1:
            return 'right'
        if x_diff == -1:
            return 'left'
    else:
        return ''

@bottle.post('/move')
def move():
    resp = bottle.request.json
    food_data = resp['food']['data']
    food_vertices = get_food_vertices(food_data) #returns list of vertices that contain food
    occupied_vertices = update_vertices(resp) #update vertices that contain snakes
    head_vertex = get_head(resp)
    closest_food_vertex = get_closest_food(food_vertices,head_vertex)
    #next_vertex = find_shortest_path(head_vertex,closest_food_vertex)
    next_vertex_d = Dijkstra_shortest_path(head_vertex,closest_food_vertex)
    print("dijstra next vertex ",next_vertex_d.x,next_vertex_d.y)
    #print("next vertex: ",next_vertex.x,next_vertex.y)
    direction = get_direction(head_vertex,next_vertex_d)
    print("next direction: ",direction)
    graph.clear(food_vertices,occupied_vertices)

    # directions = ['up', 'down', 'left', 'right']
    # if logic.last_dir:
    #     opposite = logic.opposite(logic.last_dir)
    #     directions.remove(opposite)
    #     direction = random.choice(directions)
    #     directions.append(opposite)
    # else:
    #     direction = random.choice(directions)
    # print("last dir:%s"%logic.last_dir)
    # logic.last_dir = direction
    # print ("new direction: %s"%direction)
    return {
        'move': direction,
        'taunt': 'battlesnake-python!'
    }


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    global EMPTY
    EMPTY = 0
    global FOOD
    FOOD = 1
    global OCCUPIED
    OCCUPIED = 2
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8081'),
        debug = True)
