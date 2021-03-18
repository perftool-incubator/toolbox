import copy
from pathlib import Path

def _debug_log(log_msg):
    return(print("DEBUG: %s" % (log_msg)))

class system_cpu:
    def __init__(self, cpu_dir, debug = False):
        self.debug = debug

        if self.debug:
            _debug_log("system_cpu: processing %s" % (cpu_dir))

        partition = str(cpu_dir).partition('cpu/cpu')
        if partition[2] == '':
            raise AttributeError("system_cpu: Could not extract cpu_id from '%s'" % (cpu_dir))
        self.cpu_id = int(partition[2])

        if self.debug:
            _debug_log("system_cpu: found cpu=%s" % (self.cpu_id))

        file = cpu_dir / 'online'
        if file.exists() and file.is_file():
            with file.open() as fh:
                self.online = int(fh.readline().rstrip())
                if self.debug:
                    _debug_log("system_cpu: found cpu=%s online=%s" % (self.cpu_id, self.online))
        else:
            raise AttributeError("system_cpu: Could not open 'online' file for cpu=%d" % (cpu_id))

        dir = cpu_dir / 'topology'
        if dir.exists() and dir.is_dir():
            for file in dir.iterdir():
                partition = str(file).partition('topology/')
                if partition[2] != '':
                    if partition[2] == 'physical_package_id':
                        with file.open() as fh:
                            self.physical_package_id = int(fh.readline().rstrip())
                            if self.debug:
                                _debug_log("system_cpu: found cpu=%s physical_package_id=%d" % (self.cpu_id, self.physical_package_id))
                    elif partition[2] == 'core_id':
                        with file.open() as fh:
                            self.core_id = int(fh.readline().rstrip())
                            if self.debug:
                                _debug_log("system_cpu: found cpu=%s core_id=%d" % (self.cpu_id, self.core_id))
                    elif partition[2] == 'die_id':
                        with file.open() as fh:
                            self.die_id = int(fh.readline().rstrip())
                            if self.debug:
                                _debug_log("system_cpu: found cpu=%s die_id=%d" % (self.cpu_id, self.die_id))
                    elif partition[2] == 'core_cpus_list':
                        with file.open() as fh:
                            self.cores_cpus_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                            try:
                                self.cores_cpus_list.remove(self.cpu_id)
                            except ValueError as e:
                                pass

                            if self.debug:
                                _debug_log("system_cpu: found cpu=%s core_cpus_list=%s" % (self.cpu_id, self.cores_cpus_list))
                    elif partition[2] == 'core_siblings_list':
                        with file.open() as fh:
                            self.core_siblings_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                            try:
                                self.core_siblings_list.remove(self.cpu_id)
                            except ValueError as e:
                                pass

                            if self.debug:
                                _debug_log("system_cpu: found cpu=%s core_siblings_list=%s" % (self.cpu_id, self.core_siblings_list))
                    elif partition[2] == 'die_cpus_list':
                        with file.open() as fh:
                            self.die_cpus_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                            try:
                                self.die_cpus_list.remove(self.cpu_id)
                            except ValueError as e:
                                pass

                            if self.debug:
                                _debug_log("system_cpu: found cpu=%s die_cpus_list=%s" % (self.cpu_id, self.die_cpus_list))
                    elif partition[2] == 'package_cpus_list':
                        with file.open() as fh:
                            self.package_cpus_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                            try:
                                self.package_cpus_list.remove(self.cpu_id)
                            except ValueError as e:
                                pass

                            if self.debug:
                                _debug_log("system_cpu: found cpu=%s package_cpus_list=%s" % (self.cpu_id, self.package_cpus_list))
                    elif partition[2] == 'thread_siblings_list':
                        with file.open() as fh:
                            self.thread_siblings_list = system_cpu_topology.parse_cpu_list(fh.readline().rstrip())

                            try:
                                self.thread_siblings_list.remove(self.cpu_id)
                            except ValueError as e:
                                pass

                            if self.debug:
                                _debug_log("system_cpu: found cpu=%s thread_siblings_list=%s" % (self.cpu_id, self.thread_siblings_list))
        return(None)

    def get_id(self):
        return(self.cpu_id)

    def get_online(self):
        return(self.online)

    def get_thread_siblings(self):
        return(self.thread_siblings_list)

class system_cpu_topology:
    def __init__(self, sysfs_path='/sys/devices/system/cpu', debug = False):
        self.sysfs_path = sysfs_path
        self.debug = debug
        self.discover()
        return(None)

    def discover(self):
        self.cpus = {}

        path = Path(self.sysfs_path)

        for cpu in path.glob('cpu[0-9]*'):
            if cpu.is_dir():
                try:
                    cpu_obj = system_cpu(cpu, debug = self.debug)
                    self.cpus[cpu_obj.get_id()] = cpu_obj
                except AttributeError as e:
                    print(e)
        return(0)

    def get_all_cpus(self):
        cpus = []
        for cpu in self.cpus:
            cpus.append(self.cpus[cpu].get_id())
        cpus.sort()
        return(cpus)

    def get_online_cpus(self):
        cpus = []
        for cpu in self.cpus:
            if self.cpus[cpu].get_online():
                cpus.append(self.cpus[cpu].get_id())
        cpus.sort()
        return(cpus)

    def get_thread_siblings(self, cpu):
        siblings = []

        if cpu in self.cpus:
            siblings = self.cpus[cpu].get_thread_siblings()
        else:
            raise AttributeError("system_cpu_topology: get_thread_siblings: invalid cpu %d" % (cpu))

        return(siblings)

    @staticmethod
    def parse_cpu_list(input_list):
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
