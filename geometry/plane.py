from geometry.parametric import ParametricGeometry


class PlaneGeometry(ParametricGeometry):
    def __init__(self, width=1, height=1, width_segments=8, height_segments=8):
        super().__init__(-width / 2, width / 2, width_segments,
                         -height / 2, height / 2, height_segments,
                         lambda u, v: [u, v, 0])


class TexturedPlaneGeometry(ParametricGeometry):
    def __init__(self, width=1, height=1, width_segments=8, height_segments=8, repeat_u=1, repeat_v=1):
        """
        Create a plane geometry with custom texture repetition
        Args:
            width: width of the plane
            height: height of the plane
            width_segments: number of segments in width direction
            height_segments: number of segments in height direction
            repeat_u: number of times to repeat texture in U direction
            repeat_v: number of times to repeat texture in V direction
        """
        def surface_function(u, v):
            return [u, v, 0]

        def uv_function(u_param, v_param, u_start, u_end, v_start, v_end):
            # Map parameters to UV coordinates with repetition
            u_normalized = (u_param - u_start) / (u_end - u_start)
            v_normalized = (v_param - v_start) / (v_end - v_start)
            return [u_normalized * repeat_u, v_normalized * repeat_v]

        super().__init__(-width / 2, width / 2, width_segments,
                         -height / 2, height / 2, height_segments,
                         surface_function,
                         uv_function)
