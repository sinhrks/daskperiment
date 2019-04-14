import platform
import multiprocessing

import cpuinfo

from daskperiment.environment.base import _EnvironmentJsonDataClass
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class PlatformEnvironment(_EnvironmentJsonDataClass):
    """
    Handle device info

    * CPU
    * OS
    """

    key = 'platform'

    __slots__ = ('platform', 'cpu_count')

    # class attribute for display key
    # should be capital with the same name
    _PLATFORM = 'Platform Information'
    _CPU_COUNT = 'Device CPU Count'

    def __init__(self):
        self.platform = platform.platform()
        self.cpu_count = multiprocessing.cpu_count()


class DetailedCPUEnvironment(_EnvironmentJsonDataClass):
    """
    Handle device info

    * CPU
    """
    key = 'cpu'

    # cache cpu info to shorten the execution time,
    # as it shouldn't be changed
    _CACHE = cpuinfo.get_cpu_info()

    __slots__ = ('python_version', 'cpuinfo_version', 'vendor_id', 'hardware',
                 'brand', 'hz_advertised', 'hz_actual', 'hz_advertised_raw',
                 'hz_actual_raw', 'arch', 'bits', 'count', 'raw_arch_string',
                 'l1_data_cache_size', 'l1_instruction_cache_size',
                 'l2_cache_size', 'l2_cache_line_size',
                 'l2_cache_associativity', 'l3_cache_size', 'stepping',
                 'model', 'family', 'processor_type', 'extended_model',
                 'extended_family', 'flags')

    _PYTHON_VERSION = 'Python Version'
    _CPUINFO_VERSION = 'Cpuinfo Version'
    _VENDOR_ID = 'Vendor ID'
    _HARDWARE = 'Hardware Raw'
    _BRAND = 'Brand'
    _HZ_ADVERTISED = 'Hz Advertised'
    _HZ_ACTUAL = 'Hz Actual'
    _HZ_ADVERTISED_RAW = 'Hz Advertised Raw'
    _HZ_ACTUAL_RAW = 'Hz Actual Raw'
    _ARCH = 'Arch'
    _BITS = 'Bits'
    _COUNT = 'Count'
    _RAW_ARCH_STRING = 'Raw Arch String'
    _L1_DATA_CACHE_SIZE = 'L1 Data Cache Size'
    _L1_INSTRUCTION_CACHE_SIZE = 'L1 Instruction Cache Size'
    _L2_CACHE_SIZE = 'L2 Cache Size'
    _L2_CACHE_LINE_SIZE = 'L2 Cache Line Size'
    _L2_CACHE_ASSOCIATIVITY = 'L2 Cache Associativity'
    _L3_CACHE_SIZE = 'L3 Cache Size'
    _STEPPING = 'Stepping'
    _MODEL = 'Model'
    _FAMILY = 'Family'
    _PROCESSOR_TYPE = 'Processor Type'
    _EXTENDED_MODEL = 'Extended Model'
    _EXTENDED_FAMILY = 'Extended Family'
    _FLAGS = 'Flags'

    def __init__(self):
        for key in self.__slots__:
            value = self._CACHE.get(key, '')
            if isinstance(value, tuple):
                # version-likes
                value = '.'.join([str(v) for v in value])
            elif isinstance(value, list):
                # stringify and conat flags
                value = ','.join([str(v) for v in value])
            setattr(self, key, value)

    def output_init(self):
        return []
