from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from base64 import b64decode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .core.jetson import Jetson
from .core.grove_vision_ai_v2 import GroveVisionAiV2
from .core.recamera import ReCamera
from .const import (
    DOMAIN,
    JETSON,
    DATA_SOURCE,
    GROVE_VISION_AI_V2,
    RECAMERA_GIMBAL,
)
from PIL import Image, ImageDraw
import io
import logging
import json

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    if data_source == JETSON:
        jetson: Jetson = data[JETSON]
        camera = JetsonCamera(jetson.deviceMac, jetson.deviceName)
        jetson.on_monitor_stream(camera.received_image)
        async_add_entities([camera], False)
    elif data_source == GROVE_VISION_AI_V2:
        groveVisionAiV2: GroveVisionAiV2 = data[GROVE_VISION_AI_V2]
        camera = GroveVisionAiV2Camera(groveVisionAiV2.deviceId, groveVisionAiV2.deviceName)
        groveVisionAiV2.on_monitor_stream(camera.received_image)
        async_add_entities([camera], False)
    elif data_source == RECAMERA_GIMBAL:
        recamera: ReCamera = data[RECAMERA_GIMBAL]
        camera = ReCameraEntity(recamera.deviceId, recamera.deviceName)
        recamera.on_received_image(camera.received_image)
        async_add_entities([camera], False)


class CameraBase(Camera):
    """Representation of an camera entity."""

    def __init__(
        self,
        id: str, 
        name:str,
    ) -> None:
        """Initialize the camera entity."""
        super().__init__()
        self._attr_frame_interval = 0.1
        self._attr_name = name
        self._device_name = name
        self._attr_unique_id = id
        self._stream_source = None
        self._attr_is_streaming = True

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes:
        """Return a still image response."""
        return self._stream_source

    def received_image(self, frame):
        """Base method to receive image data."""
        try:
            self._stream_source = b64decode(frame)
        except Exception as e:
            _LOGGER.error("Error processing image: %s", e)
            
    
    def should_poll(self):
        """Return True if entity should be polled for state updates."""
        return True

class JetsonCamera(CameraBase):

    def __init__(
        self,
        mac: str, 
        name:str,
    ) -> None:
        """Initialize the image entity."""
        super().__init__(mac, name)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._attr_unique_id)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            model="Jetson",
            sw_version="1.0",
        )

class GroveVisionAiV2Camera(CameraBase):

    def __init__(
        self,
        id: str, 
        name:str,
    ) -> None:
        """Initialize the image entity."""
        super().__init__(id, name)
        number = name.split("_")[-1]
        self._model = name.removesuffix("_" + number)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._attr_unique_id)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            model=self._model,
            sw_version="1.0",
        )

class ReCameraEntity(CameraBase):
    """Representation of a ReCamera entity."""

    def __init__(
        self,
        id: str, 
        name: str,
    ) -> None:
        """Initialize the camera entity."""
        super().__init__(id, name)
        self._attr_is_streaming = True
        self._attr_frame_interval = 0.1  # 10 FPS
        self._image = None
        self._detection_data = None
        self._min_update_interval = 0.1  # 100ms 最小更新间隔
        # 添加支持的功能
        self._attr_supported_features = CameraEntityFeature.ON_OFF

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._device_name,
            manufacturer="Seeed Studio",
            model="ReCamera",
            sw_version="1.0",
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._stream_source is not None
        
    @property
    def state(self) -> str:
        """Return the camera state."""
        if self._stream_source is None:
            return "unavailable"
        return ""

    def received_image(self, frame):
        """Handle received image and detection data."""
        try:
            if isinstance(frame, bytes):
                try:
                    # 解析数据
                    text_data = frame.decode('utf-8')
                    parsed_data = json.loads(text_data)
                    
                    if parsed_data.get('code') == 0 and 'data' in parsed_data:
                        data = parsed_data['data']
                        
                        if 'image' in data and data['image']:
                            try:
                                # 处理图像和检测数据
                                img_bytes = b64decode(data['image'])
                                
                                # 加载图像并处理检测数据
                                if data.get('boxes'):
                                    # 打开图像并绘制检测框
                                    image = Image.open(io.BytesIO(img_bytes))
                                    self._draw_detections(image, data)
                                    # 将图像转换回字节
                                    buffer = io.BytesIO()
                                    image.save(buffer, format='JPEG')
                                    processed_bytes = buffer.getvalue()
                                    self._stream_source = processed_bytes
                                else:
                                    # 没有检测数据，直接使用原始图像
                                    self._stream_source = img_bytes
                                
                                self._image = img_bytes
                                self._detection_data = data
                            except Exception as e:
                                _LOGGER.error("Error processing image: %s", e)
                        
                except Exception as e:
                    _LOGGER.error("Error parsing data: %s", e)
            else:
                return

            if self.hass:
                self.hass.loop.call_soon_threadsafe(self.schedule_update_ha_state)

        except Exception as e:
            _LOGGER.error("Error processing received data: %s", e)

    def _draw_detections(self, image, data):
        """Draw all visualization elements on the image."""
        try:            
            # 获取图像尺寸
            width, height = image.size            
            # 创建 ImageDraw 对象
            draw = ImageDraw.Draw(image)
            
            # 根据JavaScript代码定义颜色列表
            COLORS_HEX = [
                "#FF0000", "#FF4500", "#FF6347", "#FF8C00", "#FFA500",
                "#FFD700", "#32CD32", "#006400", "#4169E1", "#0000FF",
                "#1E90FF", "#00FFFF", "#00CED1", "#20B2AA", "#FF1493",
                "#FF69B4", "#800080", "#8A2BE2", "#9400D3", "#9932CC"
            ]
            
            # 将十六进制颜色转换为RGB元组
            COLORS = []
            for hex_color in COLORS_HEX:
                r = int(hex_color[1:3], 16)
                g = int(hex_color[3:5], 16)
                b = int(hex_color[5:7], 16)
                COLORS.append((r, g, b))
            
            # 绘制线条 (lines)
            if 'lines' in data:
                for i, line in enumerate(data['lines']):
                    if len(line) >= 4:
                        x1 = int(line[0] * 0.01 * width)
                        y1 = int(line[1] * 0.01 * height)
                        x2 = int(line[2] * 0.01 * width)
                        y2 = int(line[3] * 0.01 * height)
                        color = COLORS[i % len(COLORS)]
                        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)
            
            # 绘制分类结果 (classes)
            if 'classes' in data:
                rect_height = height / 16
                for i, cls in enumerate(data['classes']):
                    if len(cls) >= 2:
                        score, tar = cls
                        label_text = data['labels'][i] if 'labels' in data and i < len(data['labels']) else f"NA-{tar}"
                        rect_width = width / len(data['classes'])
                        color = COLORS[int(tar) % len(COLORS)]
                        # 绘制矩形
                        draw.rectangle(
                            [int(rect_width * i), 0, int(rect_width * (i + 1)), int(rect_height)],
                            fill=color,
                            outline=color
                        )
                        # 绘制文本
                        draw.text(
                            (int(rect_width * i + 5), int(rect_height / 2 - 7)),
                            f"{label_text}: {score}",
                            fill="white"
                        )
            
            # 绘制检测框 (boxes)
            if 'boxes' in data:
                for i, box in enumerate(data['boxes']):
                    if len(box) >= 6:
                        x, y, w, h, score, tar = box
                        
                        # 计算框的坐标
                        x1 = max(0, int(x - w/2))
                        y1 = max(0, int(y - h/2))
                        x2 = min(width, int(x + w/2))
                        y2 = min(height, int(y + h/2))
                        
                        # 获取颜色
                        color = COLORS[int(tar) % len(COLORS)]
                        
                        # 绘制矩形框
                        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                        
                        # 准备标签文本
                        label_text = data['labels'][i] if 'labels' in data and i < len(data['labels']) else f"NA-{tar}"
                        
                        # 构建标签
                        label = f"{label_text}({score})"
                        if 'tracks' in data and i < len(data['tracks']):
                            track_id = data['tracks'][i]
                            label = f"#{track_id}: {label}"
                        
                        # 绘制标签背景
                        text_width = draw.textlength(label, font=None)
                        text_height = 14  # 假定高度为14像素
                        draw.rectangle(
                            [x1, y1 - text_height, x1 + text_width, y1],
                            fill=color
                        )
                        
                        # 绘制标签文本
                        draw.text((x1 + 5, y1 - text_height + 2), label, fill="white")
            
            # 绘制分割结果 (segments)
            if 'segments' in data:
                for i, segment in enumerate(data['segments']):
                    if len(segment) >= 2:
                        box = segment[0]
                        polygon = segment[1]
                        
                        # 默认颜色
                        color = COLORS[i % len(COLORS)]
                        
                        # 如果有框信息，则使用框的类别作为颜色索引
                        if box and len(box) >= 6:
                            x, y, w, h, score, tar = box
                            color = COLORS[int(tar) % len(COLORS)]
                            
                            # 计算框的坐标
                            x1 = max(0, int(x - w/2))
                            y1 = max(0, int(y - h/2))
                            x2 = min(width, int(x + w/2))
                            y2 = min(height, int(y + h/2))
                            
                            # 绘制矩形框
                            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                            
                            # 准备标签文本
                            label_text = data['labels'][i] if 'labels' in data and i < len(data['labels']) else f"NA-{tar}"
                            
                            # 构建标签
                            label = f"{label_text}({score})"
                            if 'tracks' in data and i < len(data['tracks']):
                                track_id = data['tracks'][i]
                                label = f"#{track_id}: {label}"
                            
                            # 绘制标签背景
                            text_width = draw.textlength(label, font=None)
                            text_height = 14  # 假定高度为14像素
                            draw.rectangle(
                                [x1, y1 - text_height, x1 + text_width, y1],
                                fill=color
                            )
                            
                            # 绘制标签文本
                            draw.text((x1 + 5, y1 - text_height + 2), label, fill="white")
                        
                        # 绘制多边形
                        if polygon:
                            points = []
                            for j in range(0, len(polygon), 2):
                                if j + 1 < len(polygon):
                                    points.append((polygon[j], polygon[j + 1]))
                            
                            if points:
                                # 绘制多边形轮廓
                                draw.polygon(points, outline=color)
            
            # 绘制关键点 (keypoints)
            if 'keypoints' in data:
                for i, keypoint_data in enumerate(data['keypoints']):
                    if len(keypoint_data) >= 2:
                        box = keypoint_data[0]
                        keypoints = keypoint_data[1]
                        
                        if box and len(box) >= 6 and keypoints:
                            x, y, w, h, score, tar = box
                            
                            # 计算框的坐标
                            x1 = max(0, int(x - w/2))
                            y1 = max(0, int(y - h/2))
                            x2 = min(width, int(x + w/2))
                            y2 = min(height, int(y + h/2))
                            
                            # 获取颜色
                            color = COLORS[int(tar) % len(COLORS)]
                            
                            # 绘制矩形框
                            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                            
                            # 准备标签文本
                            label_text = data['labels'][i] if 'labels' in data and i < len(data['labels']) else f"NA-{tar}"
                            
                            # 构建标签
                            label = f"{label_text}({score})"
                            if 'tracks' in data and i < len(data['tracks']):
                                track_id = data['tracks'][i]
                                label = f"#{track_id}: {label}"
                            
                            # 绘制标签背景
                            text_width = draw.textlength(label, font=None)
                            text_height = 14  # 假定高度为14像素
                            draw.rectangle(
                                [x1, y1 - text_height, x1 + text_width, y1],
                                fill=color
                            )
                            
                            # 绘制标签文本
                            draw.text((x1 + 5, y1 - text_height + 2), label, fill="white")
                            
                            # 收集有效的关键点（在框内的点）
                            valid_points = set()
                            for j, point in enumerate(keypoints):
                                if len(point) >= 2:
                                    px, py = point[0], point[1]
                                    target = point[3] if len(point) > 3 else j
                                    
                                    if px > x1 and px < x2 and py > y1 and py < y2:
                                        valid_points.add(j)
                                        
                                        # 绘制关键点
                                        point_color = COLORS[target % len(COLORS)]
                                        radius = 3
                                        draw.ellipse(
                                            [(px - radius, py - radius), (px + radius, py + radius)],
                                            fill=point_color,
                                            outline=point_color
                                        )
                            
                            # 如果是人体姿态点(17个关键点)，绘制骨骼连接线
                            if len(keypoints) == 17:
                                # 头部连接
                                self._draw_keypoint_line(draw, keypoints, valid_points, 0, 1, COLORS, 0)  # 鼻子到左眼
                                self._draw_keypoint_line(draw, keypoints, valid_points, 0, 2, COLORS, 0)  # 鼻子到右眼
                                self._draw_keypoint_line(draw, keypoints, valid_points, 1, 3, COLORS, 0)  # 左眼到左耳
                                self._draw_keypoint_line(draw, keypoints, valid_points, 2, 4, COLORS, 0)  # 右眼到右耳
                                self._draw_keypoint_line(draw, keypoints, valid_points, 3, 5, COLORS, 0)  # 左耳到左肩
                                self._draw_keypoint_line(draw, keypoints, valid_points, 4, 6, COLORS, 0)  # 右耳到右肩
                                
                                # 上半身连接
                                self._draw_keypoint_line(draw, keypoints, valid_points, 5, 6, COLORS, 1)  # 左肩到右肩
                                self._draw_keypoint_line(draw, keypoints, valid_points, 5, 7, COLORS, 1)  # 左肩到左肘
                                self._draw_keypoint_line(draw, keypoints, valid_points, 7, 9, COLORS, 1)  # 左肘到左腕
                                self._draw_keypoint_line(draw, keypoints, valid_points, 6, 8, COLORS, 6)  # 右肩到右肘
                                self._draw_keypoint_line(draw, keypoints, valid_points, 8, 10, COLORS, 1)  # 右肘到右腕
                                
                                # 躯干连接
                                self._draw_keypoint_line(draw, keypoints, valid_points, 5, 11, COLORS, 2)  # 左肩到左臀
                                self._draw_keypoint_line(draw, keypoints, valid_points, 6, 12, COLORS, 2)  # 右肩到右臀
                                self._draw_keypoint_line(draw, keypoints, valid_points, 11, 12, COLORS, 2)  # 左臀到右臀
                                
                                # 下半身连接
                                self._draw_keypoint_line(draw, keypoints, valid_points, 11, 13, COLORS, 3)  # 左臀到左膝
                                self._draw_keypoint_line(draw, keypoints, valid_points, 13, 15, COLORS, 3)  # 左膝到左踝
                                self._draw_keypoint_line(draw, keypoints, valid_points, 12, 14, COLORS, 3)  # 右臀到右膝
                                self._draw_keypoint_line(draw, keypoints, valid_points, 14, 16, COLORS, 3)  # 右膝到右踝
                        
        except Exception as e:
            _LOGGER.error("Error drawing detections: %s", e, exc_info=True)
    
    def _draw_keypoint_line(self, draw, keypoints, valid_points, idx1, idx2, colors, color_idx=None):
        """绘制关键点之间的连接线"""
        if idx1 in valid_points and idx2 in valid_points:
            point1 = keypoints[idx1]
            point2 = keypoints[idx2]
            
            if len(point1) >= 2 and len(point2) >= 2:
                x1, y1 = point1[0], point1[1]
                x2, y2 = point2[0], point2[1]
                
                if color_idx is None:
                    color_idx = idx1
                
                color = colors[color_idx % len(colors)]
                draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
