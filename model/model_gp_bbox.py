import bpy
import numpy as np
from mathutils import Vector
from typing import Sequence, Union, ClassVar, Optional, Literal
from dataclasses import dataclass, field

from .utils import VecTool
from .model_gp_edit import EditGreasePencilStroke
from .model_gp import GreasePencilProperty


class MouseDetectModel:
    """MouseDetectModel Model, a base class for detect mouse position with 2d grease pencil annotation.
    work in region 2d space.
    """

    bbox_model: 'GreasePencilLayerBBox' = None
    debug_points: list[Vector] = []

    def _bind_bbox_model(self, bbox_model: 'GreasePencilLayerBBox') -> 'MouseDetectModel':
        """Need to bind the bbox model to work."""
        self.bbox_model = bbox_model
        self.bbox_model.detect_model = self
        return self

    def in_area(self, pos: Union[Sequence, Vector], feather: int = 0) -> bool:
        """check if the pos is in the area defined by the points
        :param pos: the position to check, in v2d/r2d space
        :param feather: the feather to expand the area, unit: pixel
        :return: True if the pos is in the area, False otherwise
        """
        x, y = pos
        points = self.bbox_model.bbox_points_r2d
        top_left, top_right, bottom_left, bottom_right = points

        if feather != 0:
            top_left = (top_left[0] - feather, top_left[1] + feather)
            top_right = (top_right[0] + feather, top_right[1] + feather)
            bottom_left = (bottom_left[0] - feather, bottom_left[1] - feather)

        if top_left[0] < x < top_right[0] and bottom_left[1] < y < top_left[1]:
            return True
        return False

    def near_edge_center(self, pos: Union[Sequence, Vector], radius: int = 20) -> \
            Union[tuple[Vector, int], tuple[None, None]]:
        """check if the pos is near the edge center of the area defined by the points
        :param pos: the position to check
        :param radius: the radius of the edge center point
        :return: True if the pos is near the edge center, False otherwise
        """
        vec_pos = Vector((pos[0], pos[1]))
        points = self.bbox_model.edge_center_points_r2d
        for i, point in enumerate(points):
            vec_point = Vector(point)
            if (vec_pos - vec_point).length < radius:
                return vec_point, i
        return None, None

    def near_corners(self, pos: Union[Sequence, Vector], radius: int = 20) -> \
            Union[tuple[Vector, int], tuple[None, None]]:
        """check if the pos is near the corners of the area defined by the bounding box points
        :param pos: the position to check
        :param radius: the radius of the corner point
        :return: True if the pos is near the corners, False otherwise
        """
        vec_pos = Vector((pos[0], pos[1]))
        points = self.bbox_model.bbox_points_r2d
        for i, point in enumerate(points):
            vec_point = Vector(point)
            if (vec_pos - vec_point).length < radius:
                return vec_point, i
        return None, None

    def near_corners_extrude(self, pos: Union[Sequence, Vector], extrude: int = 15, radius: int = 15) -> Union[
        tuple[Vector, int], tuple[None, None]]:

        """check if the pos is near the corner point extrude outward by 45 deg, space is default to r2d
        :param pos: the position to check
        :param extrude: the extrude distance
        :param radius: the radius of the extrude point
        :return: True if the pos is near the corners, False otherwise
        """
        vec = Vector(pos)
        points = self.bbox_model.corner_extrude_points_r2d(extrude)
        self.debug_points = [*points, vec]
        for i, point in enumerate(points):
            if (vec - point).length < radius:
                return point, i
        return None, None


@dataclass
class GreasePencilLayerBBox(GreasePencilProperty):
    """
    Calculate the bounding box of the grease pencil bounding box. useful for drawing the bounding box.
    """
    # The indices of the bounding box points, use for gpu batch drawing
    indices: ClassVar = ((0, 1, 2), (2, 1, 3))
    # The bounding box max and min values
    max_x: float = 0
    min_x: float = 0
    max_y: float = 0
    min_y: float = 0
    #
    last_layer_index: int = None
    detect_model: Optional['MouseDetectModel'] = field(init=False)

    def __post_init__(self):
        self.detect_model = MouseDetectModel()._bind_bbox_model(self)

    @property
    def size(self) -> tuple[float, float]:
        """Return the 3d size of the bounding box."""
        return self.max_x - self.min_x, self.max_y - self.min_y

    @property
    def size_v2d(self) -> Vector:
        """Return the 2d view size of the bounding box."""
        return VecTool.loc3d_2_v2d(self.size)

    @property
    def center(self) -> tuple[float, float]:
        """Return the 3d center of the bounding box."""
        return (self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2

    @property
    def center_v2d(self) -> Vector:
        """Return the 2d view center of the bounding box."""
        return VecTool.loc3d_2_v2d(self.center)

    @property
    def center_r2d(self) -> Vector:
        """Return the 2d region center of the bounding box."""
        return VecTool.v2d_2_r2d(self.center_v2d)

    @property
    def top_left(self) -> tuple[float, float]:
        """Return the 3d top left point of the bounding box."""
        return self.min_x, self.max_y

    @property
    def top_right(self) -> tuple[float, float]:
        """Return the 3d top right point of the bounding box."""
        return self.max_x, self.max_y

    @property
    def bottom_left(self) -> tuple[float, float]:
        """Return the 3d bottom left point of the bounding box."""
        return self.min_x, self.min_y

    @property
    def bottom_right(self) -> tuple[float, float]:
        """Return the 3d bottom right point of the bounding box."""
        return self.max_x, self.min_y

    @property
    def bbox_points_3d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the bounding box points."""
        # top_left, top_right, bottom_left, bottom_right
        return Vector(self.top_left), Vector(self.top_right), Vector(self.bottom_left), Vector(self.bottom_right)

    @property
    def bbox_points_v2d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the bounding box points in node editor view."""
        return tuple(map(VecTool.loc3d_2_v2d, self.bbox_points_3d))

    @property
    def bbox_points_r2d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the bounding box points in region 2d space."""

        return tuple(map(VecTool.v2d_2_r2d, self.bbox_points_v2d))

    @property
    def edge_center_points_3d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the edge center points of the bounding box."""
        top_center = (self.max_x + self.min_x) / 2, self.max_y
        bottom_center = (self.max_x + self.min_x) / 2, self.min_y
        left_center = self.min_x, (self.max_y + self.min_y) / 2
        right_center = self.max_x, (self.max_y + self.min_y) / 2
        return Vector(top_center), Vector(bottom_center), Vector(left_center), Vector(right_center)

    @property
    def edge_center_points_v2d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the edge center points of the bounding box in node editor view."""
        return tuple(map(VecTool.loc3d_2_v2d, self.edge_center_points_3d))

    @property
    def edge_center_points_r2d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the edge center points of the bounding box in region 2d space."""
        return tuple(map(VecTool.v2d_2_r2d, self.edge_center_points_v2d))

    def corner_extrude_points_r2d(self, extrude: int = 10) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the corner extrude points of the bounding box.
        :param extrude: the extrude distance
        this is not a property because it needs an extrude distance"""
        points = self.bbox_points_r2d
        extrude_vecs = [Vector((-extrude, extrude)), Vector((extrude, extrude)), Vector((-extrude, -extrude)),
                        Vector((extrude, -extrude))]  # top_left, top_right, bottom_left, bottom_right
        new_points = [Vector(point) + vec for point, vec in zip(points, extrude_vecs)]

        return new_points

    @staticmethod
    def _calc_stroke_bbox(stroke: bpy.types.GPencilStroke) -> tuple[float, float, float, float]:
        """
        Calculate the bounding box of a stroke.
        :param stroke:
        :return:
        """
        with EditGreasePencilStroke.stroke_points(stroke) as vertices:
            max_xyz_id = np.argmax(vertices, axis=0)
            min_xyz_id = np.argmin(vertices, axis=0)

            max_x = float(vertices[max_xyz_id[0], 0])
            max_y = float(vertices[max_xyz_id[1], 1])
            min_x = float(vertices[min_xyz_id[0], 0])
            min_y = float(vertices[min_xyz_id[1], 1])

        return max_x, min_x, max_y, min_y

    def calc_active_layer_bbox(self, frame: int = 0) -> None:
        """
        Calculate the bounding box of the active grease pencil annotation layer.
        :param frame: calc this frame
        """
        layer = self.active_layer
        if not layer:
            raise ValueError('Active layer not found.')

        return self.calc_bbox(layer.info, frame)

    def calc_bbox(self, layer_name_or_inedx: Union[str, int], frame: int = 0) -> None:
        """
        Calculate the bounding box of the grease pencil annotation.
        :param layer_name_or_inedx: The name or index of the layer.
        :param frame: calc this frame
        """

        layer = self._get_layer(layer_name_or_inedx)
        if not layer:
            raise ValueError(f'Layer {layer_name_or_inedx} not found.')

        frame = layer.frames[frame]
        if not frame:
            raise ValueError(f'Frame {frame} not found.')

        x_list = []
        y_list = []
        for stroke in frame.strokes:
            max_x, min_x, max_y, min_y = self._calc_stroke_bbox(stroke)
            x_list.extend([max_x, min_x])
            y_list.extend([max_y, min_y])

        self.max_x = max(x_list)
        self.min_x = min(x_list)
        self.max_y = max(y_list)
        self.min_y = min(y_list)
        self.last_layer_index = [i for i, l in enumerate(self.gp_data.layers) if l == layer][0]


@dataclass
class GreasePencilLayers(GreasePencilProperty):
    @staticmethod
    def in_layer_area(gp_data: bpy.types.GreasePencil, pos: Union[Sequence, Vector], feather: int = 0, ) -> Union[
        int, None]:

        """check if the pos is in the area defined by the points
        :param gp_data: the grease pencil data
        :param pos: the position to check
        :param feather: the feather to expand the area, unit: pixel
        :return: index of the layer if the pos is in the area, None otherwise
        """
        bboxs: list[GreasePencilLayerBBox] = [GreasePencilLayerBBox(gp_data, layer) for layer in
                                              gp_data.layers]
        for i, bbox in enumerate(bboxs):
            bbox.calc_bbox(i)
            if bbox.detect_model.in_area(pos, feather):
                # print(f'In layer {bbox.gp_data.layers[i].info}')
                return bbox.last_layer_index

        return None
