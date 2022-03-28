import os
from selenium import webdriver


class BaseWebDriver:
    """
    An extensible, context based `selenium` web driver class.

    Parameters
    ----------
    profile : str
        The browser profile path within the application directory.
    timeout : int
        The maximum duration to wait for elements to load.

    Attributes
    ----------
    timeout : int
        The maximum duration to wait for elements to load.
    """

    def __init__(self, profile, timeout):
        self.timeout = timeout

        options = webdriver.ChromeOptions()
        options.binary_location = (
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        )

        session_dir = os.path.expanduser(f"~/.ig-mbs-scheduler/{profile}")
        options.add_argument(f"--user-data-dir={session_dir}")

        self._driver = webdriver.Chrome(options=options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._driver.close()

    def _get(self, url):
        """
        Open a URL in the web browser.

        Parameters
        ----------
        url : str
            The URL to request from the web driver.
        """
        if url != self._driver.current_url:
            print(f"URLs '{self._driver.current_url}' and '{url}' differ")
            print(f"Getting '{url}'")
            self._driver.get(url)
        else:
            print(
                f"URLs '{self._driver.current_url}' and '{url}' are equal, continuing..."
            )
