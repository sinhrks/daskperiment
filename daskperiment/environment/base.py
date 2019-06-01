from abc import abstractmethod
import os

from daskperiment.util.diff import unified_diff


class _EnvironmentDataClass(object):
    # TODO: use @dataclass?

    __slots__ = ()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        for key in self.__slots__:
            if getattr(self, key) != getattr(other, key):
                return False
        return True

    @property
    def key(self):
        """
        Unique key to specify environment
        """
        raise NotImplementedError

    @property
    def ext(self):
        """
        File extension to be used, only used for LocalBackend
        """
        raise NotImplementedError

    def output_init(self):
        """
        Return a list of str which is displayed when Experiment is initialized
        """
        raise NotImplementedError

    def output_detail(self):
        """
        Return a readable string which should contains full output
        """
        raise NotImplementedError

    def difference_from(self, prev):
        current = self.output_detail()
        previous = prev.output_detail()
        assert isinstance(current, str)
        assert isinstance(previous, str)

        if current != previous:
            results = []
            for d in unified_diff(previous, current, n=0):
                results.append(d)
            return results
        else:
            return None

    @abstractmethod
    def dumps(self):
        """
        Dump myself to string
        """
        pass

    @abstractmethod
    def loads(self):
        """
        Load myself myself from string
        """
        pass


class _EnvironmentTextDataClass(_EnvironmentDataClass):
    """
    DataClass contains a single text value
    """
    __slots__ = ('value', )
    ext = 'txt'

    def __init__(self, value):
        self.value = value

    def output_init(self):
        return [self.value]

    def output_detail(self):
        return self.value

    def dumps(self):
        return self.value

    def loads(self, text):
        obj = object.__new__(self.__class__)
        obj.value = text
        return obj


class _EnvironmentJsonDataClass(_EnvironmentDataClass):
    """
    DataClass contains multiple text values
    """
    ext = 'json'

    def _format_list(self):
        res = []
        for key in self.__slots__:
            disp = getattr(self, '_{}'.format(key.upper()))
            res.append('{}: {}'.format(disp, getattr(self, key)))
        return res

    def output_init(self):
        return self._format_list()

    def output_detail(self):
        return os.linesep.join(self._format_list())

    def __json__(self):
        """
        Dump myself
        """
        results = {}
        for attr in self.__slots__:
            key = getattr(self, '_{}'.format(attr.upper()))
            value = getattr(self, attr)
            assert isinstance(value, (int, float, str)), (key, value)
            results[key] = getattr(self, attr)
        return results

    def dumps(self):
        """
        Dump instance to JSON string
        """
        # use standard json not to parse datetime-like str
        import json
        return json.dumps(self.__json__())

    def loads(self, text):
        """
        Load instance from JSON string
        """
        # use standard json not to parse datetime-like str
        import json

        obj = object.__new__(self.__class__)

        attrs = json.loads(text)
        for k, v in attrs.items():
            # search slots which has the same repr
            for s in self.__slots__:
                key = getattr(self, '_{}'.format(s.upper()))
                if key == k:
                    setattr(obj, s, v)
        return obj
