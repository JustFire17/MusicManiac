from typing import List, Tuple

def my_obj_reader2(filename: str) -> Tuple[List, List]:
    """
    Get the vertices and texture coordinates from the file.
    """
    position_list = list()
    texture_list = list()
    vertices = list()
    tex_coords = list()

    with open(filename, 'r') as in_file:
        for line in in_file:
            if line.startswith('v '):
                point = [float(value) for value in line.strip().split()[1:]]
                vertices.append(point)
            elif line.startswith('vt '):
                tex = [float(value) for value in line.strip().split()[1:]]
                tex_coords.append(tex)
            elif line.startswith('f '):
                for elem in line.strip().split()[1:]:
                    indices = elem.split('/')
                    vertex_idx = int(indices[0]) - 1
                    position_list.append(vertices[vertex_idx])

                    if len(indices) > 1 and indices[1]:
                        tex_idx = int(indices[1]) - 1
                        texture_list.append(tex_coords[tex_idx])

    print(f"[OBJ] {filename} - vértices: {len(position_list)}, texturas: {len(texture_list)}")
    return position_list, texture_list

if __name__ == '__main__':
    f_in = input("File? ")
    positions, textures = my_obj_reader2(f_in)
    print("Vertex positions:", positions)
    print("Texture coordinates:", textures)