from typing import Tuple, Iterable

import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
from netaddr import IPSet, IPRange
import re

CIDR_RE = re.compile(ipv4cidrRegex)
IP_RE = re.compile(ipv4Regex)


def ip_groups_to_ranges(ip_range_groups: Iterable) -> set:
    """Collapse ip groups to ranges.

    Args:
        ip_range_groups (Iterable): a list of lists containing connected IPs

    Returns:
        Set. a set of Ranges.
    """
    ip_ranges = set()
    for group in ip_range_groups:
        # handle single ips
        if len(group) == 1:
            ip_ranges.add(str(group[0]))
            continue

        ip_ranges.add(str(group))

    return ip_ranges


def collect_ips(ioc_list: List[str]) -> Tuple[IPSet, set]:
    ip_set = IPSet()
    non_ip_group = set()
    for ioc in ioc_list:
        if '-' in ioc:
            # handle ip ranges
            ip_range = ioc.split('-')
            if len(ip_range) == 2 and IP_RE.fullmatch(ip_range[0]) and IP_RE.fullmatch(ip_range[1]):
                ip_set.add(IPRange(ip_range[0], ip_range[1]))
            else:
                non_ip_group.add(ioc)
        elif CIDR_RE.findall(ioc) or IP_RE.match(ioc):
            ip_set.add(ioc)
        else:
            non_ip_group.add(ioc)
    return ip_set, non_ip_group


def collect_unique_indicators_from_lists(ioc_list_1: List[str], ioc_list_2: List[str]) -> Tuple[set, set]:
    ip_set_1, non_ip_set_1 = collect_ips(ioc_list_1)
    ip_set_2, non_ip_set_2 = collect_ips(ioc_list_2)
    ip_diff1 = ip_set_1.difference(ip_set_2)
    ip_diff2 = ip_set_2.difference(ip_set_1)
    diff1 = ip_groups_to_ranges(ip_diff1.iter_ipranges())
    diff2 = ip_groups_to_ranges(ip_diff2.iter_ipranges())
    diff1.update(non_ip_set_1.difference(non_ip_set_2))
    diff2.update(non_ip_set_2.difference(non_ip_set_1))
    return diff1, diff2


def main():
    args = demisto.args()
    ioc_list1 = argToList(args.get('ioc_list1', []))
    ioc_list2 = argToList(args.get('ioc_list2', []))
    diff1, diff2 = collect_unique_indicators_from_lists(ioc_list1, ioc_list2)
    outputs = {
        'UniqueIndicators1': list(diff1),
        'UniqueIndicators2': list(diff2)
    }
    return_results(CommandResults(outputs=outputs, outputs_key_field='Query', outputs_prefix='IndicatorsCheck'))


if __name__ in ['__main__', 'builtin', 'builtins']:
    main()
