from geometry.geometry import Geometry
import numpy as np


from geometry.geometry import Geometry


class ColosseumGeometry(Geometry):
    def __init__(self, width=1, height=1, depth=1, verticesTuba=[], uv_data=[]):
        super().__init__()

        gray = [0.5, 0.5, 0.5]

        position_data = verticesTuba
        color_data = [gray] * len(position_data)  # Aplica cinzento em todos os vértices

        # Usa as coordenadas UV fornecidas
        self.add_attribute("vec3", "vertexPosition", position_data)
        self.add_attribute("vec3", "vertexColor", color_data)
        self.add_attribute("vec2", "vertexUV", uv_data)