import sys
from expiringdict import ExpiringDict


class DownloaderStatistics(object):
    expiring_dict = ExpiringDict(
        max_len=sys.maxint, max_age_seconds=600
    )
    expiring_dict["responses/total"] = 0

    @staticmethod
    def update(response):
        key = "responses/%s" % response.code
        if key not in DownloaderStatistics.expiring_dict:
            DownloaderStatistics.expiring_dict[key] = 0
        DownloaderStatistics.expiring_dict[key] += 1
        DownloaderStatistics.expiring_dict["responses/total"] += 1
        return response
