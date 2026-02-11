from core.obj_reader import my_obj_reader
from geometry.geometry import Geometry


"""class BallGeometry(Geometry):
    def __init__(self, width=1, height=1, depth=1):
        super().__init__()
        position_data = my_obj_reader('geometry/Bola.obj')
        # print(position_data)
        self.add_attribute("vec3", "vertexPosition", position_data)
        self.count_vertices()
        # print(self.vertex_count)
        """
class TubaGeometry(Geometry):
    def __init__(self):
        super().__init__()

        # Definindo os dados das cores
        c1, c2 = [1.0, 1.0, 1.0], [0, 0, 0]

        # Dados das coordenadas de textura
        t0, t1, t2, t3 = [0, 0], [1, 0], [0, 1], [1, 1]

        # Lendo os dados de posição do arquivo Bola.obj usando my_obj_reader
        position_data = my_obj_reader('geometry/tubabuedafixemaispequenasemface.obj')

        # Calculando o número de vértices
        num_vertices = len(position_data) // 3

        # Duplicando os dados de cor para cada vértice
        num_seam_vertices = 94000
        color_data = [c1] * num_seam_vertices

        # Definindo a cor dos vértices que representam a bola como branco
        num_ball_vertices = num_vertices - num_seam_vertices
        color_data.extend([c2] * num_ball_vertices)

        # Criando os dados de coordenadas de textura
        uv_data = [t0, t1, t3, t0, t3, t2] * (num_vertices // 6)

        # Adicionando os atributos à geometria
        self.add_attribute("vec3", "vertexPosition", position_data)
        #self.add_attribute("vec3", "vertexColor", color_data)
        self.add_attribute("vec2", "vertexUV", uv_data)

        # Contando o número total de vértices
        self.count_vertices()