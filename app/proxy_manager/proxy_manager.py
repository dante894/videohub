def test_all():

    import requests

    for proxy in POOL:

        try:

            r = requests.get(
                "https://api.ipify.org?format=json",
                proxies={
                    "http": proxy.url,
                    "https": proxy.url,
                },
                timeout=10,
            )

            print(proxy.name, r.text)

        except Exception as e:

            print(proxy.name, e)