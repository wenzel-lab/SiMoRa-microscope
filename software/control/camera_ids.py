"""
IDS spectrometer camera backend.

Uses the IDS peak Python bindings to access the IDS USB3 camera. If the IDS SDK
is not available, the simulation backend can still be used.
"""

import threading
import time

import numpy as np

from control.camera import Camera_Simulation as BaseCameraSimulation
from control._def import TriggerMode

try:
    from ids_peak import ids_peak
    from ids_peak_ipl import ids_peak_ipl
except ImportError:  # pragma: no cover - fallback to simulation
    ids_peak = None
    ids_peak_ipl = None


class Camera:
    """IDS camera implementation using IDS peak."""

    _library_initialized = False

    def __init__(self, sn=None, rotate_image_angle=None, flip_image=None):
        if ids_peak is None or ids_peak_ipl is None:
            raise ImportError(
                "IDS peak Python bindings not available. Install ids_peak, "
                "ids_peak_ipl, and IDS peak SDK."
            )

        self.sn = sn
        self.rotate_image_angle = rotate_image_angle
        self.flip_image = flip_image

        self.device = None
        self.remote_device = None
        self.node_map = None
        self.datastream = None
        self._buffers = []
        self._grab_thread = None
        self._grab_stop = threading.Event()

        self.is_color = False
        self.is_streaming = False
        self.callback_is_enabled = False
        self.is_live = False
        self.image_locked = False

        self.new_image_callback_external = None
        self.current_frame = None

        self.frame_ID = -1
        self.frame_ID_software = -1
        self.frame_ID_offset_hardware_trigger = 0
        self.timestamp = 0

        self.exposure_time = 20
        self.analog_gain = 0
        self.pixel_format = None
        self.pixel_size_byte = 2
        self.trigger_mode = None
        self.exposure_delay_us = 0
        self.strobe_delay_us = 0
        self.row_period_us = 0
        self.row_numbers = 0

        # Defaults, will be updated on open()
        self.Width = 1920
        self.Height = 1080
        self.WidthMax = 1920
        self.HeightMax = 1080
        self.OffsetX = 0
        self.OffsetY = 0

        self.GAIN_MIN = 0
        self.GAIN_MAX = 24
        self.GAIN_STEP = 1
        self.EXPOSURE_TIME_MS_MIN = 0.01
        self.EXPOSURE_TIME_MS_MAX = 4000

    def _ensure_library(self):
        if not Camera._library_initialized:
            ids_peak.Library.Initialize()
            Camera._library_initialized = True

    def _get_node(self, name):
        if self.node_map is None:
            return None
        if not self.node_map.HasNode(name):
            return None
        return self.node_map.FindNode(name)

    def _set_enum(self, name, value):
        node = self._get_node(name)
        if node is None or not node.IsWriteable():
            return False
        try:
            node.SetCurrentEntry(value)
            return True
        except Exception:
            return False

    def _set_float(self, name, value):
        node = self._get_node(name)
        if node is None or not node.IsWriteable():
            return False
        try:
            node.SetValue(float(value))
            return True
        except Exception:
            return False

    def _set_int(self, name, value):
        node = self._get_node(name)
        if node is None or not node.IsWriteable():
            return False
        try:
            node.SetValue(int(value))
            return True
        except Exception:
            return False

    def _get_int(self, name, default):
        node = self._get_node(name)
        if node is None or not node.IsReadable():
            return default
        try:
            return int(node.Value())
        except Exception:
            return default

    def _get_float(self, name, default):
        node = self._get_node(name)
        if node is None or not node.IsReadable():
            return default
        try:
            return float(node.Value())
        except Exception:
            return default

    def open(self, index=0):
        self._ensure_library()
        dm = ids_peak.DeviceManager.Instance()
        dm.Update()
        devices = dm.Devices()
        if len(devices) == 0:
            raise RuntimeError("Could not find any IDS camera devices!")

        descriptor = None
        if self.sn is not None:
            for dev in devices:
                if dev.SerialNumber() == self.sn:
                    descriptor = dev
                    break
        if descriptor is None:
            descriptor = devices[index]

        self.device = descriptor.OpenDevice(ids_peak.DeviceAccessType_Control)
        self.remote_device = self.device.RemoteDevice()
        self.node_map = self.remote_device.NodeMaps()[0]

        self.datastream = self.device.DataStreams()[0].OpenDataStream()
        self._announce_buffers()

        self.Width = self._get_int("Width", self.Width)
        self.Height = self._get_int("Height", self.Height)
        self.WidthMax = self._get_int("WidthMax", self.WidthMax)
        self.HeightMax = self._get_int("HeightMax", self.HeightMax)
        self.OffsetX = self._get_int("OffsetX", self.OffsetX)
        self.OffsetY = self._get_int("OffsetY", self.OffsetY)
        self._init_feature_ranges()

        # Force a sensible default for spectrometer use.
        if self.pixel_format is None:
            self.set_pixel_format("MONO16")

        self.set_exposure_time(self.exposure_time)
        self.set_analog_gain(self.analog_gain)

    def close(self):
        self.stop_streaming()
        if self.datastream is not None:
            for buf in list(self._buffers):
                try:
                    self.datastream.RevokeBuffer(buf)
                except Exception:
                    pass
            self._buffers = []
        if self.device is not None:
            self.device = None
        if Camera._library_initialized:
            ids_peak.Library.Close()
            Camera._library_initialized = False

    def set_callback(self, function):
        self.new_image_callback_external = function

    def enable_callback(self):
        self.callback_is_enabled = True
        if self.is_streaming and self._grab_thread is None:
            self._start_grab_thread()

    def disable_callback(self):
        self.callback_is_enabled = False
        self._stop_grab_thread()

    def start_streaming(self):
        if self.is_streaming:
            return
        self._start_acquisition()
        self.is_streaming = True
        if self.callback_is_enabled:
            self._start_grab_thread()

    def stop_streaming(self):
        if not self.is_streaming:
            return
        self._stop_grab_thread()
        self._stop_acquisition()
        self.is_streaming = False

    def set_pixel_format(self, pixel_format):
        if self.is_streaming:
            self.stop_streaming()
        self.pixel_format = pixel_format
        if pixel_format in ("MONO8",):
            self.pixel_size_byte = 1
            if not self._set_enum("PixelFormat", "Mono8"):
                print("PixelFormat Mono8 not supported; falling back to MONO16")
                self.pixel_format = "MONO16"
        elif pixel_format in ("MONO12",):
            self.pixel_size_byte = 2
            if not self._set_enum("PixelFormat", "Mono12"):
                print("PixelFormat Mono12 not supported; falling back to MONO16")
                self.pixel_format = "MONO16"
        elif pixel_format in ("MONO16",):
            self.pixel_size_byte = 2
            self._set_enum("PixelFormat", "Mono16")
        elif pixel_format in ("BAYER_RG8",):
            self.pixel_size_byte = 1
            if not self._set_enum("PixelFormat", "BayerRG8"):
                print("PixelFormat BayerRG8 not supported; falling back to MONO16")
                self.pixel_format = "MONO16"
        elif pixel_format in ("BAYER_RG12",):
            self.pixel_size_byte = 2
            if not self._set_enum("PixelFormat", "BayerRG12"):
                print("PixelFormat BayerRG12 not supported; falling back to MONO16")
                self.pixel_format = "MONO16"

    def set_exposure_time(self, exposure_time):
        self.exposure_time = exposure_time
        self._set_float("ExposureTime", exposure_time * 1000)

    def update_camera_exposure_time(self):
        self._set_float("ExposureTime", self.exposure_time * 1000)

    def set_analog_gain(self, analog_gain):
        self.analog_gain = analog_gain
        self._set_float("Gain", analog_gain)

    def set_wb_ratios(self, wb_r=None, wb_g=None, wb_b=None):
        pass

    def set_balance_white_auto(self, value):
        pass

    def get_balance_white_auto(self):
        return 0

    def get_is_color(self):
        return self.is_color

    def set_reverse_x(self, value):
        pass

    def set_reverse_y(self, value):
        pass

    def set_continuous_acquisition(self):
        self._set_enum("TriggerMode", "Off")
        self._set_enum("AcquisitionMode", "Continuous")
        self.trigger_mode = TriggerMode.CONTINUOUS
        self.update_camera_exposure_time()

    def set_software_triggered_acquisition(self):
        self._set_enum("TriggerMode", "On")
        self._set_enum("TriggerSource", "Software")
        self.trigger_mode = TriggerMode.SOFTWARE
        self.update_camera_exposure_time()

    def set_hardware_triggered_acquisition(self):
        self._set_enum("TriggerMode", "On")
        self._set_enum("TriggerSource", "Line0")
        self.trigger_mode = TriggerMode.HARDWARE
        self.update_camera_exposure_time()

    def send_trigger(self):
        if not self.is_streaming:
            return
        node = self._get_node("TriggerSoftware")
        if node is None or not node.IsWriteable():
            return
        node.Execute()

    def read_frame(self):
        buffer = self._wait_for_buffer()
        if buffer is None:
            return None
        image = self._buffer_to_numpy(buffer)
        self.datastream.QueueBuffer(buffer)
        return image

    def set_ROI(self, offset_x=None, offset_y=None, width=None, height=None):
        was_streaming = self.is_streaming
        if was_streaming:
            self.stop_streaming()
        if width is not None:
            self.Width = width
            self._set_int("Width", width)
        if height is not None:
            self.Height = height
            self._set_int("Height", height)
        if offset_x is not None:
            self.OffsetX = offset_x
            self._set_int("OffsetX", offset_x)
        if offset_y is not None:
            self.OffsetY = offset_y
            self._set_int("OffsetY", offset_y)
        if was_streaming:
            self.start_streaming()

    def reset_camera_acquisition_counter(self):
        pass

    def set_line3_to_strobe(self):
        pass

    def set_line3_to_exposure_active(self):
        pass

    def _announce_buffers(self):
        payload_size = self.datastream.PayloadSize()
        min_buffers = self.datastream.NumBuffersAnnouncedMinRequired()
        self._buffers = []
        for _ in range(min_buffers + 1):
            buf = self.datastream.AllocAndAnnounceBuffer(payload_size)
            self.datastream.QueueBuffer(buf)
            self._buffers.append(buf)

    def _start_acquisition(self):
        self.datastream.StartAcquisition()
        node = self._get_node("AcquisitionStart")
        if node is not None and node.IsWriteable():
            node.Execute()

    def _stop_acquisition(self):
        node = self._get_node("AcquisitionStop")
        if node is not None and node.IsWriteable():
            node.Execute()
        try:
            self.datastream.StopAcquisition()
        except Exception:
            pass
        try:
            self.datastream.Flush(ids_peak.DataStreamFlushMode_AllToInputPool)
        except Exception:
            pass

    def _wait_for_buffer(self, timeout_ms=1000):
        try:
            return self.datastream.WaitForFinishedBuffer(timeout_ms)
        except Exception:
            return None

    def _buffer_to_numpy(self, buffer):
        if buffer is None or not buffer.HasImage():
            return None
        width = buffer.Width() if callable(getattr(buffer, "Width", None)) else buffer.Width
        height = buffer.Height() if callable(getattr(buffer, "Height", None)) else buffer.Height
        if hasattr(buffer, "DeliveredImageHeight"):
            try:
                delivered_height = buffer.DeliveredImageHeight()
                if delivered_height > 0:
                    height = delivered_height
            except Exception:
                pass
        if hasattr(buffer, "DeliveredDataSize"):
            try:
                buffer_size = buffer.DeliveredDataSize()
            except Exception:
                buffer_size = buffer.Size()
        else:
            buffer_size = buffer.Size()

        pixel_format = self._ipl_pixel_format_from_device()
        image = ids_peak_ipl.Image.CreateFromSizeAndBuffer(
            pixel_format,
            buffer.BasePtr(),
            buffer_size,
            width,
            height,
        )
        if self._is_packed_format(pixel_format) or self._is_high_bit_bayer(pixel_format):
            try:
                image = image.ConvertTo(ids_peak_ipl.PixelFormatName_Mono16)
                pixel_format = ids_peak_ipl.PixelFormatName_Mono16
            except Exception:
                pass
        if self._is_8bit_format(pixel_format):
            return image.get_numpy_2D().copy()
        return image.get_numpy_2D_16().copy()

    def _ipl_pixel_format(self):
        if self.pixel_format == "MONO8":
            return ids_peak_ipl.PixelFormatName_Mono8
        if self.pixel_format == "MONO12":
            return ids_peak_ipl.PixelFormatName_Mono12
        if self.pixel_format == "BAYER_RG8":
            return ids_peak_ipl.PixelFormatName_BayerRG8
        if self.pixel_format == "BAYER_RG12":
            return ids_peak_ipl.PixelFormatName_BayerRG12
        return ids_peak_ipl.PixelFormatName_Mono16

    def _get_pixel_format_symbolic(self):
        node = self._get_node("PixelFormat")
        if node is None or not node.IsReadable():
            return None
        try:
            entry = node.CurrentEntry()
            return entry.SymbolicValue()
        except Exception:
            return None

    def _ipl_pixel_format_from_device(self):
        symbolic = self._get_pixel_format_symbolic()
        mapping = {
            "Mono8": ids_peak_ipl.PixelFormatName_Mono8,
            "Mono10": ids_peak_ipl.PixelFormatName_Mono10,
            "Mono10p": ids_peak_ipl.PixelFormatName_Mono10p,
            "Mono10g40IDS": ids_peak_ipl.PixelFormatName_Mono10g40IDS,
            "Mono12": ids_peak_ipl.PixelFormatName_Mono12,
            "Mono12p": ids_peak_ipl.PixelFormatName_Mono12p,
            "Mono12g24IDS": ids_peak_ipl.PixelFormatName_Mono12g24IDS,
            "Mono16": ids_peak_ipl.PixelFormatName_Mono16,
            "BayerRG8": ids_peak_ipl.PixelFormatName_BayerRG8,
            "BayerRG10": ids_peak_ipl.PixelFormatName_BayerRG10,
            "BayerRG10p": ids_peak_ipl.PixelFormatName_BayerRG10p,
            "BayerRG12": ids_peak_ipl.PixelFormatName_BayerRG12,
            "BayerRG12p": ids_peak_ipl.PixelFormatName_BayerRG12p,
            "BayerRG12g24IDS": ids_peak_ipl.PixelFormatName_BayerRG12g24IDS,
        }
        if symbolic in mapping:
            return mapping[symbolic]
        return self._ipl_pixel_format()

    def _is_8bit_format(self, pixel_format):
        return pixel_format in (
            ids_peak_ipl.PixelFormatName_Mono8,
            ids_peak_ipl.PixelFormatName_BayerRG8,
        )

    def _is_packed_format(self, pixel_format):
        return pixel_format in (
            ids_peak_ipl.PixelFormatName_Mono10p,
            ids_peak_ipl.PixelFormatName_Mono12p,
            ids_peak_ipl.PixelFormatName_Mono10g40IDS,
            ids_peak_ipl.PixelFormatName_Mono12g24IDS,
            ids_peak_ipl.PixelFormatName_BayerRG10p,
            ids_peak_ipl.PixelFormatName_BayerRG12p,
            ids_peak_ipl.PixelFormatName_BayerRG10g40IDS,
            ids_peak_ipl.PixelFormatName_BayerRG12g24IDS,
        )

    def _is_high_bit_bayer(self, pixel_format):
        return pixel_format in (
            ids_peak_ipl.PixelFormatName_BayerRG10,
            ids_peak_ipl.PixelFormatName_BayerRG12,
        )

    def _init_feature_ranges(self):
        node = self._get_node("ExposureTime")
        if node is not None and node.IsReadable():
            try:
                self.EXPOSURE_TIME_MS_MIN = node.Minimum() / 1000
                self.EXPOSURE_TIME_MS_MAX = node.Maximum() / 1000
            except Exception:
                pass
        node = self._get_node("Gain")
        if node is not None and node.IsReadable():
            try:
                self.GAIN_MIN = node.Minimum()
                self.GAIN_MAX = node.Maximum()
                self.GAIN_STEP = node.Increment()
            except Exception:
                pass

    def _start_grab_thread(self):
        if self._grab_thread is not None:
            return
        self._grab_stop.clear()
        self._grab_thread = threading.Thread(target=self._grab_loop, daemon=True)
        self._grab_thread.start()

    def _stop_grab_thread(self):
        if self._grab_thread is None:
            return
        self._grab_stop.set()
        self._grab_thread.join(timeout=2)
        self._grab_thread = None

    def _grab_loop(self):
        while not self._grab_stop.is_set() and self.is_streaming:
            buffer = self._wait_for_buffer(timeout_ms=500)
            if buffer is None:
                continue
            if self.image_locked:
                self.datastream.QueueBuffer(buffer)
                continue
            image = self._buffer_to_numpy(buffer)
            self.datastream.QueueBuffer(buffer)
            if image is None:
                continue
            self.current_frame = image
            self.frame_ID_software += 1
            self.frame_ID = buffer.FrameID()
            self.timestamp = time.time()
            if self.new_image_callback_external is not None:
                self.new_image_callback_external(self)


class Camera_Simulation(BaseCameraSimulation):
    """Simulated IDS spectrometer camera."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Match the expected spectrometer frame size (1920x1080 mono)
        self.Width = 1920
        self.Height = 1080
        self.WidthMax = 1920
        self.HeightMax = 1080
        self.OffsetX = 0
        self.OffsetY = 0
        self.pixel_format = "MONO16"
        self.is_color = False
