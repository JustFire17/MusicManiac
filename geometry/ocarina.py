from geometry.geometry import Geometry
import numpy as np


from geometry.geometry import Geometry


class OcarinaGeometry(Geometry):
    def __init__(self, width=1, height=1, depth=1, verticesTuba=[], uv_data=[]):
        super().__init__()

        # Define a cor azul para todas as faces
        blue = [0, 0, 1]

        # Cada lado consiste em dois triângulos
        position_data = verticesTuba
        color_data = [blue] * len(position_data)  # Aplica azul em todos os vértices

        # Usa as coordenadas UV fornecidas
        self.add_attribute("vec3", "vertexPosition", position_data)
        self.add_attribute("vec3", "vertexColor", color_data)
        self.add_attribute("vec2", "vertexUV", uv_data)
        self.count_vertices()