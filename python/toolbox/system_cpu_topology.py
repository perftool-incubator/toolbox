import copy
import logging
from pathlib import Path

log_format = '%(asctime)s %(levelname)s: %(message)s'

class system_cpu:
    """
    A class that represents a single CPU and provides methods to extract and store information about the CPU.

    Attributes:
    cpu_id (int): The ID of the CPU.
    online (int): A flag that indicates whether the CPU is online or not.
    physical_package_id (int): The physical package ID of the CPU.
    core_id (int): The core ID of the CPU.
    die_id (int): The die ID of the CPU.
    cores_cpus_list (list[int]): A list of CPU IDs of the cores associated with the CPU.
    core_siblings_list (list[int]): A list of CPU IDs of the siblings associated with the core that the CPU belongs to.
    die_cpus_list (list[int]): A list of CPU IDs of the dies associated with the CPU.
    package_cpus_list (list[int]): A list of CPU IDs of the packages associated with the CPU.
    thread_siblings_list (list[int]): A list of CPU IDs of the threads associated with the CPU.
    numa_node (int): The NUMA node that the CPU belongs to.
    numa_node_cpus_list (list[int]): A list of CPU IDs of the CPUs that belong to the same NUMA node as the CPU.

    Methods:
    __init__(self, cpu_dir, log = None, debug = False): Constructs a system_cpu object and extracts information about the CPU from the sysfs directory.
    get_id(self): Returns the ID of the CPU.
    get_online(self): Returns the online flag of the CPU.
    get_thread_siblings(self): Returns a list of CPU IDs of the threads associated with the CPU.
    get_node_siblings(self): Returns a list of CPU IDs of the CPUs that belong to the same NUMA node as the CPU.
    get_node(self): Returns the NUMA node that the CPU belongs to.
    """
    
    def __init__(self, cpu_dir, log = None, debug = False):
        """
        Initialize the system_cpu object.

        Parameters:
        cpu_dir (Path): A Path object representing the CPU directory in /sys/devices/system/cpu.
        log (logging.Logger): Optional, a logger object to be used. If None, a new logger object is created.
        debug (bool): Optional, set to True to enable debug logging.

        Returns:
        None
        """
        
        if not log is None:
            self.log = log
        else:
            if debug:
                logging.basicConfig(level = logging.DEBUG, format = log_format, stream = sys.stdout)
            else:
                logging.basicConfig(level = logging.INFO, format = log_format, stream = sys.stdout)

            self.log = logging.getLogger(__file__)

        self.log.debug("processing %s" % (cpu_dir))

        partition = str(cpu_dir).partition('cpu/cpu')
        if partition[1] == partition[2] == '':
            raise AttributeError("Could not extract cpu_id from '%s'" % (cpu_dir))
        self.cpu_id = int(partition[2])

        self.log.debug("found cpu=%s" % (self.cpu_id))

        file = cpu_dir / 'online'
        if file.exists() and file.is_file():
            with file.open() as fh:
                self.online = int(fh.readline().rstrip())
                self.log.debug("found cpu=%s online=%s" % (self.cpu_id, self.online))
        else:
            self.online = 1
            self.log.debug("found cpu=%s assuming to be online because online file does not exist" % (self.cpu_id))

        dir = cpu_dir / 'topology'
        if dir.exists() and dir.is_dir():
            for file in dir.iterdir():
                partition = str(file).partition('topology/')

                if partition[2] == 'physical_package_id':
                    with file.open() as fh:
                        self.physical_package_id = int(fh.readline().rstrip())
                        self.log.debug("found cpu=%s physical_package_id=%d" % (self.cpu_id, self.physical_package_id))
                elif partition[2] == 'core_id':
                    with file.open() as fh:
                        self.core_id = int(fh.readline().rstrip())
                        self.log.debug("found cpu=%s core_id=%d" % (self.cpu_id, self.core_id))
                elif partition[2] == 'die_id':
                    with file.open() as fh:
                        self.die_id = int(fh.readline().rstrip())
                        self.log.debug("found cpu=%s die_id=%d" % (self.cpu_id, self.die_id))
                elif partition[2] == 'core_cpus_list':
                    with file.open() as fh:
                        self.cores_cpus_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                        try:
                            self.cores_cpus_list.remove(self.cpu_id)
                        except ValueError as e:
                            pass

                        self.log.debug("found cpu=%s core_cpus_list=%s" % (self.cpu_id, self.cores_cpus_list))
                elif partition[2] == 'core_siblings_list':
                    with file.open() as fh:
                        self.core_siblings_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                        try:
                            self.core_siblings_list.remove(self.cpu_id)
                        except ValueError as e:
                            pass

                        self.log.debug("found cpu=%s core_siblings_list=%s" % (self.cpu_id, self.core_siblings_list))
                elif partition[2] == 'die_cpus_list':
                    with file.open() as fh:
                        self.die_cpus_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                        try:
                            self.die_cpus_list.remove(self.cpu_id)
                        except ValueError as e:
                            pass

                        self.log.debug("found cpu=%s die_cpus_list=%s" % (self.cpu_id, self.die_cpus_list))
                elif partition[2] == 'package_cpus_list':
                    with file.open() as fh:
                        self.package_cpus_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                        try:
                            self.package_cpus_list.remove(self.cpu_id)
                        except ValueError as e:
                            pass

                        self.log.debug("found cpu=%s package_cpus_list=%s" % (self.cpu_id, self.package_cpus_list))
                elif partition[2] == 'thread_siblings_list':
                    with file.open() as fh:
                        self.thread_siblings_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                        try:
                            self.thread_siblings_list.remove(self.cpu_id)
                        except ValueError as e:
                            pass

                        self.log.debug("found cpu=%s thread_siblings_list=%s" % (self.cpu_id, self.thread_siblings_list))
                else:
                    self.log.debug("skipping cpu=%s file=%s" % (self.cpu_id, partition[2]))

        self.numa_node = None
        self.numa_node_cpus_list = None
        for node in cpu_dir.glob('node[0-9]*'):
            partition = str(node).partition('/node')
            if partition[1] == partition[2] == '':
                pass
            else:
                self.numa_node = int(partition[2])

            self.numa_node_cpus_list = []
            for cpu in node.glob('cpu[0-9]*'):
                partition = str(cpu).partition('/node' + str(self.numa_node) + '/cpu')
                if partition[1] == partition[2] == '':
                    pass
                else:
                    node_cpu = int(partition[2])
                    if self.cpu_id != node_cpu:
                        self.numa_node_cpus_list.append(int(partition[2]))
            self.numa_node_cpus_list.sort()

        self.log.debug("found cpu=%s numa_node=%s" % (self.cpu_id, self.numa_node))
        self.log.debug("found cpu=%s numa_node_cpus_list=%s" % (self.cpu_id, self.numa_node_cpus_list))

        return(None)

    def get_id(self):
        # Returns the ID of the CPU.
        return(self.cpu_id)

    def get_online(self):
        # Returns the online flag of the CPU.
        return(self.online)

    def get_thread_siblings(self):
        # Returns a list of CPU IDs of the threads associated with the CPU.
        return(self.thread_siblings_list)

    def get_node_siblings(self):
        # Returns a list of CPU IDs of the CPUs that belong to the same NUMA node as the CPU.
        return(self.numa_node_cpus_list)

    def get_node(self):
        # Returns the NUMA node that the CPU belongs to.
        return(self.numa_node)

class system_cpu_topology:
    """
    A class that represents the CPU topology of a system and provides methods to extract and store information about the CPUs.

    Attributes:
    sysfs_path (str): The path to the sysfs directory that contains information about the system's CPUs.
    cpus (dict[int, system_cpu]): A dictionary containing system_cpu objects representing the system's CPUs.

    Methods:
    __init__(self, sysfs_path='/sys/devices/system/cpu', log = None, debug = False): Constructs a system_cpu_topology object and extracts information about the system's CPUs.
    discover(self): Discovers and constructs system_cpu objects representing the system's CPUs and stores them in a dictionary.
    get_all_cpus(self): Returns a list of all CPU IDs in the system.
    get_online_cpus(self): Returns a list of online CPU IDs in the system.
    get_thread_siblings(self, cpu): Returns a list of CPU IDs of the threads associated with a specified CPU.
    get_node(self, cpu): Returns the NUMA node that a specified CPU belongs to.
    get_node_siblings(self, cpu): Returns a list of CPU IDs of the CPUs that belong to the same NUMA node as a specified CPU.
    get_cpu_node(self, cpu): Returns the NUMA node that a specified CPU belongs to.
    parse_cpu_list(input_list): A static method that parses a string containing a comma-separated list of CPUs and returns a list of their IDs.
    formatted_cpu_list(cpu_list): A static method that takes a list of CPU IDs and returns a formatted string containing ranges of sequential CPUs.
    """
    
    def __init__(self, sysfs_path='/sys/devices/system/cpu', log = None, debug = False):
        """
        Initialize the system_cpu_topology object.

        Parameters:
        sysfs_path (str): Optional, the path to the sysfs directory that contains the CPU information. Defaults to '/sys/devices/system/cpu'.
        log (logging.Logger): Optional, a logger object to be used. If None, a new logger object is created.
        debug (bool): Optional, set to True to enable debug logging.

        Returns:
        None
        """
        
        self.sysfs_path = sysfs_path

        if not log is None:
            self.log = log
        else:
            if debug:
                logging.basicConfig(level = logging.DEBUG, format = log_format, stream = sys.stdout)
            else:
                logging.basicConfig(level = logging.INFO, format = log_format, stream = sys.stdout)

            self.log = logging.getLogger(__file__)

        self.discover()

        return(None)

    def discover(self):
        # Discover all CPUs on the system and create a system_cpu object for each one.

        self.cpus = {}

        path = Path(self.sysfs_path)

        for cpu in path.glob('cpu[0-9]*'):
            if cpu.is_dir():
                try:
                    cpu_obj = system_cpu(cpu, log = self.log)
                    self.cpus[cpu_obj.get_id()] = cpu_obj
                except AttributeError as e:
                    print(e)
        return(0)

    def get_all_cpus(self):
        """
        Get a list of all CPU IDs on the system.

        Parameters:
        None

        Returns:
        list[int]: A list of all CPU IDs on the system.
        """

        cpus = []
        for cpu in self.cpus:
            cpus.append(self.cpus[cpu].get_id())
        cpus.sort()
        return(cpus)

    def get_online_cpus(self):
        """
        Get a list of online CPU IDs on the system.

        Parameters:
        None

        Returns:
        list[int]: A list of online CPU IDs on the system.
        """

        cpus = []
        for cpu in self.cpus:
            if self.cpus[cpu].get_online():
                cpus.append(self.cpus[cpu].get_id())
        cpus.sort()
        return(cpus)

    def get_thread_siblings(self, cpu):
        """
        Get a list of thread sibling CPU IDs for the given CPU.

        Parameters:
        cpu (int): The ID of the CPU to get thread sibling information for.

        Returns:
        list[int]: A list of thread sibling CPU IDs for the given CPU.
        """

        siblings = []

        if cpu in self.cpus:
            siblings = self.cpus[cpu].get_thread_siblings()
        else:
            raise AttributeError("get_thread_siblings: invalid cpu %d" % (cpu))

        return(siblings)

    def get_node(self, cpu):
        """
        Get the NUMA node for the given CPU.

        Parameters:
        cpu (int): The ID of the CPU to get NUMA node information for.

        Returns:
        int: The NUMA node for the given CPU.
        """

        node = None

        if cpu in self.cpus:
            node = self.cpus[cpu].get_node()
        else:
            raise AttributeError("get_node: invalid cpu %d" % (cpu))

        return(node)

    def get_node_siblings(self, cpu):
        """
        Get a list of CPU IDs in the same NUMA node as the given CPU.

        Parameters:
        cpu (int): The ID of the CPU to get NUMA node sibling information for.

        Returns:
        list[int]: A list of CPU IDs in the same NUMA node as the given CPU.
        """

        siblings = []

        if cpu in self.cpus:
            siblings = self.cpus[cpu].get_node_siblings()
        else:
            raise AttributeError("get_node_siblings: invalid cpu %d" % (cpu))

        return(siblings)

    def get_cpu_node(self, cpu):
        """
        Get the NUMA node that the given CPU belongs to.

        Parameters:
        cpu (int): The ID of the CPU to get the NUMA node for.

        Returns:
        int: The NUMA node that the given CPU belongs to.
        """

        if cpu in self.cpus:
            return(self.cpus[cpu].get_node())
        else:
            raise AttributeError("get_cpu_node: invalid cpu %d" % (cpu))

    @staticmethod
    def parse_cpu_list(input_list):
        """
        Parse a CPU list string into a list of individual CPU IDs.

        Parameters:
        input_list (str): A string containing a comma-separated list of CPU IDs or ranges.

        Returns:
        list[int]: A list of individual CPU IDs extracted from the input string.
        """

        output_list = []
        for item in input_list.split(','):
            # check for a cpu range instead of a lone cpu
            partition = str(item).partition('-')
            # partition[1]==partition[2]=='' then it is a singular cpu, otherwise it is a cpu range
            if partition[1] == partition[2] == '':
                output_list.append(int(item))
            else:
                output_list.extend(range(int(partition[0]), int(partition[2]) + 1))
        return(output_list)

    @staticmethod
    def formatted_cpu_list(cpu_list):
        """
        Convert a list of CPU IDs into a formatted string containing individual CPU IDs and/or CPU ID ranges.

        Parameters:
        cpu_list (list[int]): A list of CPU IDs to be converted into a formatted string.

        Returns:
        str: A string containing individual CPU IDs and/or CPU ID ranges.
        """

        formatted_list = []

        # copy the list so that we can modify it (sort, remove)
        tmp_list = copy.deepcopy(cpu_list)
        tmp_list.sort()

        # process the list until it is empty
        while len(tmp_list) > 0:
            build_range = 0
            range_end = 0

            # if the list only has 1 element then handle it
            if len(tmp_list) < 2:
                formatted_list.append(str(tmp_list.pop(0)))
            else:
                # search for a sequential range of values using a look
                # back technique -- meaning we start at the second
                # element and see if it is sequetial to the prior
                # element (initially index 0) and continue from there
                # until the range ends
                for index in range(1, len(tmp_list)):
                    # compare current and previous index to see if
                    # they are sequential values
                    if tmp_list[index] == (tmp_list[index - 1] + 1):
                        # current values are sequential, continue building range

                        build_range = 1
                        range_end = index
                    else:
                        # current values are not sequential, stop building range

                        build_range = 0
                        range_end = index - 1

                    # check to see if the range building should
                    # continue -- this requires that there be more
                    # elements to check
                    if build_range == 1 and index < (len(tmp_list) - 1):
                        continue
                    else:
                        # range building is stopped

                        if range_end >= 1:
                            # add the newly built range
                            range_str = "%s-%s" % (tmp_list[0], tmp_list[range_end])
                            formatted_list.append(range_str)

                            # remove the processed values from the list
                            for idx in range(0, range_end+1):
                                tmp_list.pop(0)
                        else:
                            # no range was found, add a single value
                            # and remove it from the list
                            formatted_list.append(str(tmp_list.pop(0)))

                        # exit the range building loop and start over
                        break

        return(formatted_list)
