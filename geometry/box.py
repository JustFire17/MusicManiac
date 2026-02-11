from geometry.geometry import Geometry


class BoxGeometry(Geometry):
    def __init__(self, width=1, height=1, depth=1,
                 width_segments=1, height_segments=1, depth_segments=1):
        super().__init__()
        p0 = [-width/2, -height/2, -depth/2]  # front bottom left
        p1 = [width/2, -height/2, -depth/2]  # front bottom right
        p2 = [-width/2, height/2, -depth/2]  # front top left
        p3 = [width/2, height/2, -depth/2]  # front top right
        p4 = [-width/2, -height/2, depth/2]  # back bottom left
        p5 = [width/2, -height/2, depth/2]  # back bottom right
        p6 = [-width/2, height/2, depth/2]  # back top left
        p7 = [width/2, height/2, depth/2]  # back top right
        # colors for faces in order: right, left, top, bottom, front, back
        c1, c2 = [1, 0.5, 0.5], [0.5, 0, 0]  # red
        c3, c4 = [0.5, 1, 0.5], [0, 0.5, 0]  # green
        c5, c6 = [0.5, 0.5, 1], [0, 0, 0.5]  # blue
        position_data = [p5, p1, p3, p5, p3, p7,  # right
                          p0, p4, p6, p0, p6, p2,  # left
                          p6, p7, p3, p6, p3, p2,  # top
                          p0, p1, p5, p0, p5, p4,  # bottom
                          p1, p0, p2, p1, p2, p3,  # front
                          p4, p5, p7, p4, p7, p6]  # back
        color_data = [c1, c1, c1, c1, c1, c1,
                       c2, c2, c2, c2, c2, c2,
                       c3, c3, c3, c3, c3, c3,
                       c4, c4, c4, c4, c4, c4,
                       c5, c5, c5, c5, c5, c5,
                       c6, c6, c6, c6, c6, c6]
        uv_data = [[0, 0], [1, 0], [1, 1],
                     [0, 0], [1, 1], [0, 1],
                     [0, 0], [1, 0], [1, 1],
                     [0, 0], [1, 1], [0, 1],
                     [0, 0], [1, 0], [1, 1],
                     [0, 0], [1, 1], [0, 1],
                     [0, 0], [1, 0], [1, 1],
                     [0, 0], [1, 1], [0, 1],
                     [0, 0], [1, 0], [1, 1],
                     [0, 0], [1, 1], [0, 1],
                     [0, 0], [1, 0], [1, 1],
                     [0, 0], [1, 1], [0, 1]]
        self.add_attribute("vec3", "vertexPosition", position_data)
        self.add_attribute("vec3", "vertexColor", color_data)
        self.add_attribute("vec2", "vertexUV", uv_data)


class TexturedBoxGeometry(BoxGeometry):
    def __init__(self, width=1, height=1, depth=1,
                 width_segments=1, height_segments=1, depth_segments=1,
                 repeat_u=1, repeat_v=1):
        """
        Create a box geometry with custom texture repetition
        Args:
            width: width of the box
            height: height of the box
            depth: depth of the box
            width_segments: number of segments in width direction
            height_segments: number of segments in height direction
            depth_segments: number of segments in depth direction
            repeat_u: number of times to repeat texture in U direction
            repeat_v: number of times to repeat texture in V direction
        """
        # Primeiro, criar a geometria base
        super().__init__(width, height, depth, width_segments, height_segments, depth_segments)
        
        # UV coordinates with repetition
        uv_data = [[0, 0], [repeat_u, 0], [repeat_u, repeat_v],
                     [0, 0], [repeat_u, repeat_v], [0, repeat_v]] * 6
        
        # Atualizar as coordenadas UV
        self._attribute_dict["vertexUV"].data = uv_data
