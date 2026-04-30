# jpl_forward.py
#
# 将 astroquery.jplhorizons 的请求转发到国内可访问的镜像站点。
# 在原 JPL Horizons 调用代码中，仅需在 import astroquery 后添加一行：
#     import jpl_forward
# 即可自动完成 URL 重定向与 token 注入。

from astroquery.jplhorizons import HorizonsClass

# 镜像站点地址
FORWARD_URL = "http://8.216.49.176:18766/api/horizons.api"
FORWARD_TOKEN = "fce2a741a94feded5c3b9b7ab51f6748"

_original_request = HorizonsClass._request


def _patched_request(self, method, url, params=None, **kwargs):
    if params is None:
        params = {}
    params["token"] = FORWARD_TOKEN
    url = FORWARD_URL
    return _original_request(self, method, url, params=params, **kwargs)


HorizonsClass._request = _patched_request
