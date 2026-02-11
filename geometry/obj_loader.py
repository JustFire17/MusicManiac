import numpy as np
from geometry.geometry import Geometry

class OBJGeometry(Geometry):
    """
    Loads a Wavefront OBJ file and creates geometry from it.
    Currently supports vertices, texture coordinates, and normals.
    """
    def __init__(self, file_path):
        super().__init__()
        
        # Lists to store the data from the OBJ file
        vertices = []
        tex_coords = []
        normals = []
        
        # Lists to store the final data for rendering
        position_data = []
        uv_data = []
        normal_data = []
        
        # Read the OBJ file
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('#'): continue  # Skip comments
                
                values = line.split()
                if not values: continue
                
                if values[0] == 'v':  # Vertex
                    vertices.append([float(x) for x in values[1:4]])
                elif values[0] == 'vt':  # Texture coordinate
                    tex_coords.append([float(x) for x in values[1:3]])
                elif values[0] == 'vn':  # Normal
                    normals.append([float(x) for x in values[1:4]])
                elif values[0] == 'f':  # Face
                    # Process each vertex of the face
                    for v in values[1:]:
                        # Split vertex data (format: vertex_idx/texcoord_idx/normal_idx)
                        indices = v.split('/')
                        
                        # Get vertex position (convert to 0-based index)
                        v_idx = int(indices[0]) - 1
                        position_data.append(vertices[v_idx])
                        
                        # Get texture coordinate if present
                        if len(indices) > 1 and indices[1]:
                            vt_idx = int(indices[1]) - 1
                            uv_data.append(tex_coords[vt_idx])
                        
                        # Get normal if present
                        if len(indices) > 2 and indices[2]:
                            vn_idx = int(indices[2]) - 1
                            normal_data.append(normals[vn_idx])
        
        # Add the attributes to the geometry
        self.add_attribute("vec3", "vertexPosition", position_data)
        
        if uv_data:
            self.add_attribute("vec2", "vertexUV", uv_data)
            
        if normal_data:
            self.add_attribute("vec3", "vertexNormal", normal_data)
            # For compatibility with lighting calculations
            self.add_attribute("vec3", "faceNormal", normal_data) 